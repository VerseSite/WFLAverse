from django.urls import path

from . import api

urlpatterns = [
    path("site/", api.site, name="api-site"),
    path("auth/csrf/", api.csrf, name="api-csrf"),
    path("auth/register/", api.register, name="api-register"),
    path("auth/login/", api.sign_in, name="api-login"),
    path("auth/logout/", api.sign_out, name="api-logout"),
    path("auth/password/", api.password, name="api-password"),
    path("me/", api.me, name="api-me"),
    path("members/", api.members, name="api-members"),
    path("members/<uuid:user_id>/", api.member, name="api-member"),
]
