import uuid

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models

phone_validator = RegexValidator(r"\A1[3-9][0-9]{9}\Z", "请输入 11 位中国大陆手机号。")
student_id_validator = RegexValidator(r"\A[0-9]{8}\Z", "学号必须是 8 位数字。")


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError("必须提供手机号。")
        user = self.model(phone=phone.strip(), **extra_fields)
        user.set_password(password)
        user.full_clean(exclude=["password"])
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("real_name", "管理员")
        if extra_fields.get("is_staff") is not True or extra_fields.get("is_superuser") is not True:
            raise ValueError("管理员必须启用 is_staff 和 is_superuser。")
        return self.create_user(phone, password, **extra_fields)


class User(AbstractUser):
    username = None
    first_name = None
    last_name = None
    email = None
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone = models.CharField("手机号", max_length=11, unique=True, validators=[phone_validator])
    student_id = models.CharField(
        "学号", max_length=8, unique=True, blank=True, null=True,
        validators=[student_id_validator],
    )
    real_name = models.CharField("真实姓名", max_length=40)
    class_name = models.CharField("班级", max_length=40, blank=True)
    bio = models.TextField("个人简介", max_length=500, blank=True)
    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = []
    objects = UserManager()

    class Meta:
        verbose_name = "用户"
        verbose_name_plural = "用户"
        ordering = ["date_joined", "id"]

    @property
    def role(self):
        return "admin" if self.is_staff else "student"

    def clean(self):
        super().clean()
        self.phone = self.phone.strip()
        self.real_name = self.real_name.strip()
        self.class_name = self.class_name.strip()
        self.student_id = self.student_id.strip() if self.student_id else None
        errors = {}
        if self.is_superuser and not self.is_staff:
            errors["is_superuser"] = "超级用户必须同时具有后台访问权限。"
        if not self.real_name:
            errors["real_name"] = "请填写真实姓名。"
        if not self.is_staff and not self.student_id:
            errors["student_id"] = "学生账号必须有学号。"
        if not self.is_staff and not self.class_name:
            errors["class_name"] = "学生账号必须有班级。"
        if errors:
            raise ValidationError(errors)

    def get_full_name(self):
        return self.real_name

    def get_short_name(self):
        return self.real_name

    def __str__(self):
        return f"{self.real_name} ({self.phone})"


class RateLimitBucket(models.Model):
    key = models.CharField(max_length=64, primary_key=True)
    started_at = models.DateTimeField(db_index=True)
    count = models.PositiveIntegerField(default=0)
