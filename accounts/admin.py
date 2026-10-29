from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import AdminUserChangeForm, AdminUserCreationForm
from .models import User


@admin.register(User)
class CampusUserAdmin(UserAdmin):
    form = AdminUserChangeForm
    add_form = AdminUserCreationForm
    list_display = ("real_name", "class_name", "phone", "student_id", "is_active", "is_staff")
    list_filter = ("is_active", "is_staff", "class_name")
    search_fields = ("real_name", "phone", "student_id", "class_name")
    ordering = ("date_joined",)
    readonly_fields = ("id", "last_login", "date_joined")
    fieldsets = (
        ("账号", {"fields": ("id", "phone", "password")}),
        ("资料", {"fields": ("student_id", "real_name", "class_name", "bio")}),
        ("权限", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("记录", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (("新建账号", {"fields": (
        "phone", "real_name", "student_id", "class_name", "bio", "password1", "password2",
        "is_staff", "is_superuser",
    )}),)
    actions = ("disable_accounts", "enable_accounts")

    @admin.action(description="停用所选账号（保留自己的账号）")
    def disable_accounts(self, request, queryset):
        count = queryset.exclude(pk=request.user.pk).update(is_active=False)
        self.message_user(request, f"已停用 {count} 个账号。")

    @admin.action(description="启用所选账号")
    def enable_accounts(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f"已启用 {count} 个账号。")


admin.site.site_header = "校园网管理"
admin.site.site_title = "校园网管理"
admin.site.index_title = "用户与权限管理"
