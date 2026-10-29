from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("login/", views.CampusLoginView.as_view(), name="login"),
    path("register/", views.register, name="register"),
    path("logout/", views.sign_out, name="logout"),
    path("account/", views.account, name="account"),
    path("account/password/", views.change_password, name="password"),
    path("forgot-password/", views.forgot_password, name="forgot-password"),
    path("members/", views.members, name="members"),
    path("members/<uuid:user_id>/", views.member, name="member"),
    path("health/", views.health, name="health"),
]
