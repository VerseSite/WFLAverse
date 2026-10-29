import json
from functools import wraps

from django.conf import settings
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.core.exceptions import RequestDataTooBig
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import ensure_csrf_cookie

from .forms import BioForm, PhoneLoginForm, RegistrationForm
from .models import User
from .serializers import private_user, public_user


def error(code, message, status=400, fields=None):
    body = {"code": code, "message": message}
    if fields is not None:
        body["fields"] = fields
    return JsonResponse({"error": body}, status=status)


def api_view(methods, *, authenticated=False):
    def decorator(view):
        @never_cache
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            if request.method not in methods:
                response = error("method_not_allowed", "请求方法不受支持。", 405)
                response["Allow"] = ", ".join(methods)
                return response
            if authenticated and not request.user.is_authenticated:
                return error("authentication_required", "请先登录。", 401)
            request.api_data = {}
            if request.method in ("POST", "PATCH"):
                if request.content_type != "application/json":
                    return error("unsupported_media_type", "请使用 application/json 请求体。", 415)
                try:
                    payload = json.loads(request.body)
                except RequestDataTooBig:
                    return error("request_too_large", "请求体过大。", 413)
                except (ValueError, UnicodeDecodeError):
                    return error("invalid_json", "请求体必须是有效 JSON。")
                if not isinstance(payload, dict) or any(not isinstance(v, str) for v in payload.values()):
                    return error("invalid_json", "请求体必须是对象，且字段值必须是字符串。")
                request.api_data = payload
            return view(request, *args, **kwargs)
        return wrapper
    return decorator


def check_fields(data, allowed):
    if set(data) - set(allowed):
        return error("unknown_fields", "请求包含不允许修改的字段。")
    return None


def form_error(form, field_names=None):
    field_names = field_names or {}
    fields = {field_names.get(name, name): [str(item) for item in errors] for name, errors in form.errors.items()}
    return error("validation_error", "请检查填写内容。", fields=fields)


@ensure_csrf_cookie
@api_view(["GET"])
def csrf(request):
    return JsonResponse({"csrf_token": get_token(request)})


@api_view(["GET"])
def site(request):
    return JsonResponse({"name": settings.SITE_NAME, "admin_contact": settings.ADMIN_CONTACT, "modules": [
        {"key": "accounts", "name": "用户与登录", "enabled": True, "url": "/account/"},
        {"key": "tasks", "name": "校园委托与招聘", "enabled": False, "url": None},
        {"key": "forum", "name": "匿名论坛", "enabled": False, "url": None},
    ]})


@api_view(["POST"])
def register(request):
    rejected = check_fields(request.api_data, ("phone", "student_id", "real_name", "class_name", "bio", "password", "password_confirm"))
    if rejected is not None:
        return rejected
    data = {**request.api_data, "password1": request.api_data.get("password", ""),
            "password2": request.api_data.get("password_confirm", "")}
    form = RegistrationForm(data)
    if not form.is_valid():
        return form_error(form, {"password1": "password", "password2": "password_confirm"})
    try:
        with transaction.atomic():
            user = form.save()
    except IntegrityError:
        return error("account_conflict", "手机号或学号已被使用。", 409)
    login(request, user)
    return JsonResponse({"user": private_user(user), "csrf_token": get_token(request)}, status=201)


@api_view(["POST"])
def sign_in(request):
    rejected = check_fields(request.api_data, ("phone", "password"))
    if rejected is not None:
        return rejected
    form = PhoneLoginForm(request, data={"username": request.api_data.get("phone", ""),
                                        "password": request.api_data.get("password", "")})
    if not form.is_valid():
        return error("invalid_credentials", "手机号或密码不正确，或账号已被停用。", 401)
    login(request, form.get_user())
    return JsonResponse({"user": private_user(form.get_user()), "csrf_token": get_token(request)})


@api_view(["POST"], authenticated=True)
def sign_out(request):
    logout(request)
    return JsonResponse({"message": "已退出登录。"})


@api_view(["GET", "PATCH"], authenticated=True)
def me(request):
    if request.method == "PATCH":
        rejected = check_fields(request.api_data, ("bio",))
        if rejected is not None:
            return rejected
        if "bio" not in request.api_data:
            return error("validation_error", "请提供 bio 字段。")
        form = BioForm(request.api_data, instance=request.user)
        if not form.is_valid():
            return form_error(form)
        form.save()
    return JsonResponse({"user": private_user(request.user)})


@api_view(["POST"], authenticated=True)
def password(request):
    rejected = check_fields(request.api_data, ("old_password", "new_password", "new_password_confirm"))
    if rejected is not None:
        return rejected
    form = PasswordChangeForm(request.user, data={
        "old_password": request.api_data.get("old_password", ""),
        "new_password1": request.api_data.get("new_password", ""),
        "new_password2": request.api_data.get("new_password_confirm", ""),
    })
    if not form.is_valid():
        return form_error(form, {"new_password1": "new_password", "new_password2": "new_password_confirm"})
    user = form.save()
    update_session_auth_hash(request, user)
    return JsonResponse({"message": "密码已修改。"})


@api_view(["GET"])
def member(request, user_id):
    user = User.objects.filter(pk=user_id, is_active=True, is_staff=False).first()
    if user is None:
        return error("not_found", "找不到该学生。", 404)
    return JsonResponse({"user": public_user(user)})


@api_view(["GET"])
def members(request):
    try:
        page = int(request.GET.get("page", "1"))
        if page < 1 or page > 100000:
            raise ValueError
    except ValueError:
        return error("invalid_page", "page 必须是 1 到 100000 的整数。")
    users = User.objects.filter(is_active=True, is_staff=False)
    offset = (page - 1) * 20
    return JsonResponse({"users": [public_user(u) for u in users[offset:offset + 20]],
                         "page": page, "page_size": 20, "total": users.count()})
