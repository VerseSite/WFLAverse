from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserChangeForm, UserCreationForm

from .models import User, phone_validator


class RegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("phone", "student_id", "real_name", "class_name", "bio")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["student_id"].required = True
        self.fields["class_name"].required = True
        self.fields["phone"].widget.attrs.update({"autocomplete": "tel", "inputmode": "tel"})
        self.fields["student_id"].widget.attrs.update({"inputmode": "numeric"})
        self.fields["real_name"].help_text = "向所有访客公开，请使用真实姓名。"
        self.fields["class_name"].help_text = "例如：Pre10-1。向所有访客公开。"
        self.fields["bio"].help_text = "选填，最多 500 字。向所有访客公开。"
        self.fields["bio"].widget.attrs["rows"] = 3


class PhoneLoginForm(AuthenticationForm):
    username = forms.CharField(
        label="手机号", max_length=11, validators=[phone_validator],
        widget=forms.TextInput(attrs={"autocomplete": "username", "inputmode": "tel"}),
    )
    error_messages = {
        "invalid_login": "手机号或密码不正确，或账号已被停用。",
        "inactive": "手机号或密码不正确，或账号已被停用。",
    }


class BioForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("bio",)
        widgets = {"bio": forms.Textarea(attrs={"rows": 4})}


class AdminUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("phone", "real_name", "student_id", "class_name", "bio", "is_staff", "is_superuser")


class AdminUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = "__all__"
