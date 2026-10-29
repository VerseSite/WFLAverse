from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.views import LoginView
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from accounts.forms import BioForm, PhoneLoginForm, RegistrationForm
from accounts.models import User


class CampusLoginView(LoginView):
    authentication_form = PhoneLoginForm
    template_name = "verse/auth.html"
    extra_context = {"auth_mode": "login", "site_name": settings.SITE_NAME}
    redirect_authenticated_user = True


@never_cache
@require_GET
def home(request):
    students = User.objects.filter(is_active=True, is_staff=False)
    return render(request, "verse/home.html", {
        "student_count": students.count(),
        "recent_members": students.order_by("-date_joined", "id")[:3],
        "upcoming_modules": [
            {"name": "校园委托与招聘", "icon": "briefcase", "description": "竞赛组队、社团招募与校园委托，找到一起行动的人。"},
            {"name": "匿名论坛", "icon": "msg", "description": "未来的校园交流空间，分享想法、提出问题。"},
            {"name": "校园影像", "icon": "image", "description": "用摄影与艺术，记录校园里的每一个维度。"},
            {"name": "校园生活", "icon": "compass", "description": "校园动态、社团与活动，连接课内课外。"},
            {"name": "学生项目", "icon": "cube", "description": "展示从想法走向现实的学生作品。"},
            {"name": "校园故事", "icon": "mic", "description": "经验、文字与访谈，听见不同的校园声音。"},
        ],
    })


@never_cache
@require_http_methods(["GET", "POST"])
def register(request):
    if request.user.is_authenticated:
        return redirect("home")
    form = RegistrationForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                user = form.save()
        except IntegrityError:
            form.add_error(None, "手机号或学号已被使用。")
        else:
            login(request, user)
            messages.success(request, "注册成功，已登录。")
            return redirect("home")
    return render(request, "verse/auth.html", {"form": form, "auth_mode": "register"})


@require_POST
def sign_out(request):
    logout(request)
    return redirect("home")


@never_cache
@login_required
@require_http_methods(["GET", "POST"])
def account(request):
    form = BioForm(request.POST if request.method == "POST" else None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "简介已更新。")
        return redirect("account")
    return render(request, "verse/account.html", {"form": form, "panel": "profile"})


@never_cache
@login_required
@require_http_methods(["GET", "POST"])
def change_password(request):
    form = PasswordChangeForm(request.user, request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)
        messages.success(request, "密码已修改。")
        return redirect("account")
    return render(request, "verse/account.html", {"form": form, "panel": "password"})


@require_GET
def forgot_password(request):
    return render(request, "verse/auth.html", {"auth_mode": "forgot"})


@require_GET
def members(request):
    users = User.objects.filter(is_active=True, is_staff=False)
    page = Paginator(users, 20).get_page(request.GET.get("page"))
    return render(request, "verse/members.html", {"page_obj": page})


@require_GET
def member(request, user_id):
    user = get_object_or_404(User, pk=user_id, is_active=True, is_staff=False)
    return render(request, "verse/members.html", {"member": user})


@require_GET
def health(request):
    return JsonResponse({"status": "ok"})
