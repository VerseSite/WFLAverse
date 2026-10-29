from django.conf import settings


def site_settings(request):
    return {"site_name": settings.SITE_NAME, "admin_contact": settings.ADMIN_CONTACT}
