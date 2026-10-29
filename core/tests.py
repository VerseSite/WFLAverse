from html.parser import HTMLParser

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.staticfiles import finders
from django.test import Client, TestCase
from django.urls import reverse


class PageMarkup(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.links = []
        self.scripts = []
        self.forms = []
        self.inputs = {}
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a" and "href" in attrs:
            self.links.append(attrs["href"])
        if tag == "script" and "src" in attrs:
            self.scripts.append(attrs["src"])
        if tag == "form":
            self.forms.append(attrs)
        if tag in ("input", "textarea") and "name" in attrs:
            self.inputs[attrs["name"]] = attrs


class FrontendIntegrationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            phone="13800138021", student_id="00123421", real_name="集成测试同学",
            class_name="Pre10-2", bio="喜欢工程", password="Integration!2026",
        )

    def test_guest_home_uses_real_public_data_without_private_identifiers(self):
        response = self.client.get(reverse("home"))
        self.assertTemplateUsed(response, "verse/home.html")
        self.assertContains(response, self.user.real_name)
        self.assertContains(response, "筹备中")
        self.assertNotContains(response, self.user.phone)
        self.assertNotContains(response, self.user.student_id)
        self.assertEqual(response.context["student_count"], 1)
        markup = PageMarkup(response.content.decode())
        self.assertNotIn("#admin", markup.links)
        self.assertNotIn("#compose", markup.links)
        self.assertTrue(all(src.startswith("/static/") for src in markup.scripts))

    def test_register_and_login_forms_have_real_server_fields_and_csrf(self):
        signup = self.client.get(reverse("register"))
        markup = PageMarkup(signup.content.decode())
        self.assertTrue({"phone", "student_id", "real_name", "class_name", "password1", "password2", "csrfmiddlewaretoken"} <= set(markup.inputs))
        self.assertEqual(markup.forms[-1]["method"], "post")
        self.assertNotIn("email", markup.inputs)
        self.assertNotIn("role", markup.inputs)
        login = PageMarkup(self.client.get(reverse("login")).content.decode())
        self.assertIn("username", login.inputs)
        self.assertIn("password", login.inputs)
        self.assertIn("csrfmiddlewaretoken", login.inputs)
        self.assertNotIn("value", login.inputs["password"])

    def test_branding_is_consistent_on_login_and_home(self):
        for name in ("home", "login", "register", "forgot-password"):
            response = self.client.get(reverse(name))
            self.assertEqual(response.context["site_name"], settings.SITE_NAME)

    def test_html_account_and_password_forms_persist_changes(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        response = client.get(reverse("account"))
        token = PageMarkup(response.content.decode()).inputs["csrfmiddlewaretoken"]["value"]
        response = client.post(reverse("account"), {"csrfmiddlewaretoken": token, "bio": "已与真实后端连接"}, follow=True)
        self.assertContains(response, "简介已更新")
        self.user.refresh_from_db()
        self.assertEqual(self.user.bio, "已与真实后端连接")
        response = client.get(reverse("password"))
        token = PageMarkup(response.content.decode()).inputs["csrfmiddlewaretoken"]["value"]
        response = client.post(reverse("password"), {
            "csrfmiddlewaretoken": token, "old_password": "Integration!2026",
            "new_password1": "Different!Integration2027", "new_password2": "Different!Integration2027",
        }, follow=True)
        self.assertContains(response, "密码已修改")
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("Different!Integration2027"))

    def test_navigation_comes_from_server_session(self):
        guest = self.client.get(reverse("home"))
        self.assertContains(guest, 'href="/login/"')
        self.assertNotContains(guest, 'action="/logout/"')
        self.client.force_login(self.user)
        member = self.client.get(reverse("home"))
        self.assertContains(member, 'action="/logout/"')
        self.assertNotContains(member, 'href="/admin/"')
        self.assertNotContains(member, 'href="/login/"')
        self.client.post(reverse("logout"))
        self.assertEqual(self.client.get(reverse("account")).status_code, 302)

    def test_supported_pages_and_local_assets_exist(self):
        for name in ("home", "login", "register", "forgot-password", "members"):
            response = self.client.get(reverse(name))
            markup = PageMarkup(response.content.decode())
            for href in markup.links:
                if href.startswith("/") and not href.startswith("//"):
                    result = self.client.get(href.split("#")[0])
                    self.assertLess(result.status_code, 400, href)
        for asset in ("verse/utilities.css", "verse/theme.css", "verse/integration.css", "verse/ui.js",
                      "verse/campus.js", "verse/vendor/three.min.js", "verse/mark.svg", "verse/icons.svg"):
            self.assertIsNotNone(finders.find(asset), asset)

    def test_home_escapes_member_content_and_excludes_inactive_users(self):
        self.user.bio = '<img src=x onerror="alert(1)">'
        self.user.save()
        response = self.client.get(reverse("home"))
        self.assertNotContains(response, '<img src=x onerror="alert(1)">')
        self.assertContains(response, "&lt;img")
        self.user.is_active = False
        self.user.save()
        response = self.client.get(reverse("home"))
        self.assertEqual(response.context["student_count"], 0)
        self.assertNotContains(response, self.user.real_name)
