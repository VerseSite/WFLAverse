import json
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .middleware import consume_limit
from .models import RateLimitBucket

User = get_user_model()
PASSWORD = "Campus!Local2026"
NEW_PASSWORD = "Different!Campus2027"


def student(**kwargs):
    defaults = {"phone": "13800138001", "student_id": "00123456", "real_name": "测试同学",
                "class_name": "Pre10-1", "bio": "喜欢物理与工程"}
    return User.objects.create_user(password=PASSWORD, **(defaults | kwargs))


class ApiTests(TestCase):
    def post(self, name, payload, client=None):
        return (client or self.client).post(reverse(name), json.dumps(payload), content_type="application/json")

    def registration(self, **kwargs):
        return {"phone": "13800138001", "student_id": "00123456", "real_name": "测试同学",
                "class_name": "Pre10-1", "bio": "喜欢物理", "password": PASSWORD,
                "password_confirm": PASSWORD} | kwargs

    def test_registration_is_active_hashes_password_and_logs_in(self):
        response = self.post("api-register", self.registration())
        self.assertEqual(response.status_code, 201)
        user = User.objects.get()
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.check_password(PASSWORD))
        self.assertNotEqual(user.password, PASSWORD)
        self.assertEqual(user.student_id, "00123456")
        self.assertEqual(self.client.get(reverse("api-me")).json()["user"]["id"], str(user.pk))

    def test_registration_requires_student_fields(self):
        for changes in ({"student_id": "1234567"}, {"student_id": "１２３４５６７８"},
                        {"student_id": ""}, {"real_name": " "}, {"class_name": ""},
                        {"phone": "123"}, {"password_confirm": "mismatch"},
                        {"password": "12345678", "password_confirm": "12345678"}):
            with self.subTest(changes=changes):
                response = self.post("api-register", self.registration(**changes))
                self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.exists())

    def test_duplicate_phone_and_student_id_are_rejected(self):
        student()
        for changes in ({"student_id": "00223456"}, {"phone": "13800138002"}):
            response = self.post("api-register", self.registration(**changes))
            self.assertEqual(response.status_code, 400)
        self.assertEqual(User.objects.count(), 1)

    def test_signup_cannot_set_permissions(self):
        for field in ("is_staff", "is_superuser", "role", "is_active", "groups"):
            response = self.post("api-register", self.registration(**{field: "admin"}))
            self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.exists())

    def test_login_logout_and_private_endpoint(self):
        user = student()
        self.assertEqual(self.client.get(reverse("api-me")).status_code, 401)
        response = self.post("api-login", {"phone": user.phone, "password": PASSWORD})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["user"]["role"], "student")
        self.assertIn("csrf_token", response.json())
        self.assertEqual(self.client.get(reverse("api-me")).status_code, 200)
        self.assertEqual(self.post("api-logout", {}).status_code, 200)
        self.assertEqual(self.client.get(reverse("api-me")).status_code, 401)

    def test_unknown_wrong_password_and_disabled_login_share_error(self):
        user = student(is_active=False)
        payloads = [{"phone": "13800138009", "password": PASSWORD},
                    {"phone": user.phone, "password": "wrong"},
                    {"phone": user.phone, "password": PASSWORD}]
        responses = [self.post("api-login", payload) for payload in payloads]
        self.assertTrue(all(response.status_code == 401 for response in responses))
        self.assertTrue(all(response.json() == responses[0].json() for response in responses))

    def test_disabled_account_loses_existing_session_and_public_profile(self):
        user = student()
        self.client.force_login(user)
        user.is_active = False
        user.save()
        self.assertEqual(self.client.get(reverse("api-me")).status_code, 401)
        self.assertEqual(self.client.get(reverse("api-member", args=[user.pk])).status_code, 404)

    def test_public_profiles_do_not_expose_private_fields(self):
        user = student()
        User.objects.create_superuser(phone="13800138099", password=PASSWORD)
        list_response = self.client.get(reverse("api-members")).json()
        self.assertEqual(list_response["total"], 1)
        profile = self.client.get(reverse("api-member", args=[user.pk])).json()["user"]
        self.assertEqual(set(profile), {"id", "real_name", "class_name", "bio"})
        for route in (reverse("members"), reverse("member", args=[user.pk])):
            response = self.client.get(route)
            self.assertContains(response, user.real_name)
            self.assertNotContains(response, user.phone)
            self.assertNotContains(response, user.student_id)

    def test_bio_update_is_only_self_service_field(self):
        user = student()
        self.client.force_login(user)
        response = self.client.patch(reverse("api-me"), json.dumps({"bio": "新简介"}), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertEqual(user.bio, "新简介")
        for field in ("real_name", "phone", "student_id", "class_name", "role", "is_staff"):
            response = self.client.patch(reverse("api-me"), json.dumps({field: "changed"}), content_type="application/json")
            self.assertEqual(response.status_code, 400)
        response = self.client.patch(reverse("api-me"), json.dumps({"bio": "x" * 501}), content_type="application/json")
        self.assertEqual(response.status_code, 400)

    def test_password_change_checks_old_password_and_invalidates_other_sessions(self):
        user = student()
        other = Client()
        self.client.force_login(user)
        other.force_login(user)
        payload = {"old_password": "wrong", "new_password": NEW_PASSWORD, "new_password_confirm": NEW_PASSWORD}
        self.assertEqual(self.post("api-password", payload).status_code, 400)
        payload["old_password"] = PASSWORD
        self.assertEqual(self.post("api-password", payload).status_code, 200)
        user.refresh_from_db()
        self.assertTrue(user.check_password(NEW_PASSWORD))
        self.assertEqual(self.client.get(reverse("api-me")).status_code, 200)
        self.assertEqual(other.get(reverse("api-me")).status_code, 401)

    def test_csrf_is_required_and_rotates_on_login(self):
        user = student()
        client = Client(enforce_csrf_checks=True)
        payload = {"phone": user.phone, "password": PASSWORD}
        denied = self.post("api-login", payload, client)
        self.assertEqual(denied.status_code, 403)
        self.assertEqual(denied.json()["error"]["code"], "csrf_failed")
        old_token = client.get(reverse("api-csrf")).json()["csrf_token"]
        response = client.post(reverse("api-login"), json.dumps(payload), content_type="application/json", HTTP_X_CSRFTOKEN=old_token)
        self.assertEqual(response.status_code, 200)
        new_token = response.json()["csrf_token"]
        self.assertEqual(client.post(reverse("api-logout"), "{}", content_type="application/json", HTTP_X_CSRFTOKEN=old_token).status_code, 403)
        self.assertEqual(client.post(reverse("api-logout"), "{}", content_type="application/json", HTTP_X_CSRFTOKEN=new_token).status_code, 200)

    def test_input_shapes_content_type_and_methods(self):
        for payload in ("[1]", "null", '{"phone": 123}', "{"):
            response = self.client.post(reverse("api-login"), payload, content_type="application/json")
            self.assertEqual(response.status_code, 400)
        response = self.client.post(reverse("api-login"), {"phone": "13800138001"})
        self.assertEqual(response.status_code, 415)
        self.assertEqual(self.client.get(reverse("api-login")).status_code, 405)
        self.assertEqual(self.client.get(reverse("api-members"), {"page": "-1"}).status_code, 400)

    def test_public_directory_paginates(self):
        for index in range(21):
            student(phone=f"1380013{index:04d}", student_id=f"{index:08d}")
        response = self.client.get(reverse("api-members")).json()
        self.assertEqual(response["total"], 21)
        self.assertEqual(len(response["users"]), 20)
        self.assertEqual(len(self.client.get(reverse("api-members"), {"page": "2"}).json()["users"]), 1)

    def test_private_responses_cannot_be_cached(self):
        self.client.force_login(student())
        self.assertIn("no-store", self.client.get(reverse("api-me"))["Cache-Control"])

    def test_registration_requires_csrf_and_returns_new_token(self):
        client = Client(enforce_csrf_checks=True)
        denied = self.post("api-register", self.registration(), client)
        self.assertEqual(denied.status_code, 403)
        token = client.get(reverse("api-csrf")).json()["csrf_token"]
        response = client.post(reverse("api-register"), json.dumps(self.registration()),
                               content_type="application/json", HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(client.patch(reverse("api-me"), json.dumps({"bio": "已注册"}),
                                      content_type="application/json",
                                      HTTP_X_CSRFTOKEN=response.json()["csrf_token"]).status_code, 200)

    def test_oversized_json_is_rejected(self):
        response = self.post("api-login", {"phone": "13800138001", "password": "x" * 33000})
        self.assertEqual(response.status_code, 413)
        self.assertEqual(response.json()["error"]["code"], "request_too_large")


class HtmlAndAdminTests(TestCase):
    def setUp(self):
        self.user = student()
        self.admin = User.objects.create_superuser(phone="13800138099", password=PASSWORD)

    def test_pages_are_available(self):
        for name in ("home", "login", "register", "members", "forgot-password"):
            self.assertEqual(self.client.get(reverse(name)).status_code, 200)
        self.assertEqual(self.client.get(reverse("health")).json(), {"status": "ok"})
        self.assertEqual(self.client.get(reverse("account")).status_code, 302)

    def test_html_registration_and_login(self):
        response = self.client.post(reverse("register"), {
            "phone": "13800138002", "student_id": "00123457", "real_name": "另一位同学",
            "class_name": "Pre10-2", "password1": PASSWORD, "password2": PASSWORD,
        })
        self.assertRedirects(response, reverse("home"))
        self.client.post(reverse("logout"))
        response = self.client.post(reverse("login"), {"username": "13800138002", "password": PASSWORD})
        self.assertRedirects(response, reverse("home"))

    def test_student_cannot_access_admin(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response["Location"])

    def test_admin_can_view_users_edit_identity_and_reset_password(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse("admin:accounts_user_changelist")).status_code, 200)
        change_url = reverse("admin:accounts_user_change", args=[self.user.pk])
        self.assertEqual(self.client.get(change_url).status_code, 200)
        response = self.client.post(change_url, {
            "phone": self.user.phone, "student_id": self.user.student_id, "real_name": "更正姓名",
            "class_name": "Pre10-2", "bio": self.user.bio, "is_active": "on", "_save": "保存",
        })
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.real_name, "更正姓名")
        self.assertEqual(self.user.class_name, "Pre10-2")
        other = Client()
        other.force_login(self.user)
        response = self.client.post(reverse("admin:auth_user_password_change", args=[self.user.pk]), {
            "password1": NEW_PASSWORD, "password2": NEW_PASSWORD, "set_usable_password": "true",
        })
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(NEW_PASSWORD))
        self.assertEqual(other.get(reverse("api-me")).status_code, 401)

    def test_admin_can_create_student(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse("admin:accounts_user_add"), {
            "phone": "13800138002", "real_name": "新同学", "student_id": "00123457",
            "class_name": "Pre10-2", "password1": PASSWORD, "password2": PASSWORD,
        })
        self.assertEqual(response.status_code, 302)
        self.assertFalse(User.objects.get(phone="13800138002").is_staff)

    def test_admin_can_create_admin_without_student_id(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse("admin:accounts_user_add"), {
            "phone": "13800138002", "real_name": "另一位管理员", "password1": PASSWORD,
            "password2": PASSWORD, "is_staff": "on", "is_superuser": "on",
        })
        self.assertEqual(response.status_code, 302)
        created = User.objects.get(phone="13800138002")
        self.assertTrue(created.is_superuser)
        self.assertEqual(created.role, "admin")
        self.assertIsNone(created.student_id)

    def test_profile_escapes_user_content(self):
        self.user.bio = '<script>alert("x")</script>'
        self.user.save()
        response = self.client.get(reverse("member", args=[self.user.pk]))
        self.assertNotContains(response, '<script>alert("x")</script>')
        self.assertContains(response, "&lt;script&gt;")

    def test_logout_is_post_only_and_login_does_not_redirect_to_external_url(self):
        self.assertEqual(self.client.get(reverse("logout")).status_code, 405)
        response = self.client.post(reverse("login"), {
            "username": self.user.phone, "password": PASSWORD, "next": "https://example.com/",
        })
        self.assertRedirects(response, reverse("home"))

    @override_settings(DEBUG=False)
    def test_unknown_api_returns_json(self):
        response = self.client.get("/api/v1/not-a-route/")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"]["code"], "not_found")


class RateLimitTests(TestCase):
    def test_login_limit_is_shared_between_api_and_html(self):
        for _ in range(10):
            response = self.client.post(reverse("api-login"), json.dumps({
                "phone": "13800138001", "password": "wrong",
            }), content_type="application/json")
            self.assertEqual(response.status_code, 401)
        response = self.client.post(reverse("login"), {"username": "13800138001", "password": "wrong"})
        self.assertEqual(response.status_code, 429)
        self.assertGreater(int(response["Retry-After"]), 0)

    def test_admin_login_is_limited(self):
        for _ in range(10):
            self.client.post("/admin/login/", {"username": "13800138001", "password": "wrong"})
        self.assertEqual(self.client.post("/admin/login/", {
            "username": "13800138001", "password": "wrong",
        }).status_code, 429)

    def test_limit_expires_and_cleanup_removes_expired_records(self):
        self.assertEqual(consume_limit("test", 1), 0)
        self.assertGreater(consume_limit("test", 1), 0)
        RateLimitBucket.objects.update(started_at=timezone.now() - timedelta(hours=1))
        self.assertEqual(consume_limit("test", 1), 0)
        RateLimitBucket.objects.update(started_at=timezone.now() - timedelta(hours=1))
        call_command("cleanup_auth_limits", verbosity=0)
        self.assertFalse(RateLimitBucket.objects.exists())

    def test_rate_limits_do_not_store_plaintext_phone(self):
        consume_limit("login:phone:13800138001", 10)
        bucket = RateLimitBucket.objects.get()
        self.assertEqual(len(bucket.key), 64)
        self.assertNotIn("13800138001", bucket.key)
