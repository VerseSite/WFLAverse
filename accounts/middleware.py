import hashlib
import json
import math
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import RequestDataTooBig
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone

from .models import RateLimitBucket


def consume_limit(key, limit):
    """Database-backed fixed window, shared by API, HTML and admin login."""
    key = hashlib.sha256(key.encode()).hexdigest()
    now = timezone.now()
    window = timedelta(seconds=settings.AUTH_RATE_LIMIT_WINDOW)
    with transaction.atomic():
        bucket, _ = RateLimitBucket.objects.select_for_update().get_or_create(
            key=key, defaults={"started_at": now, "count": 0},
        )
        if now >= bucket.started_at + window:
            bucket.started_at = now
            bucket.count = 0
        if bucket.count >= limit:
            return max(1, math.ceil((bucket.started_at + window - now).total_seconds()))
        bucket.count += 1
        bucket.save(update_fields=["started_at", "count"])
    return 0


class AuthRateLimitMiddleware:
    routes = {
        "/login/": ("login", 30),
        "/admin/login/": ("login", 30),
        "/api/v1/auth/login/": ("login", 30),
        "/register/": ("register", 10),
        "/api/v1/auth/register/": ("register", 10),
        "/account/password/": ("password", 10),
        "/api/v1/auth/password/": ("password", 10),
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        rule = self.routes.get(request.path)
        if request.method == "POST" and rule:
            operation, limit = rule
            # Do not trust client-supplied X-Forwarded-For.
            ip = request.META.get("REMOTE_ADDR", "unknown")
            retry = consume_limit(f"{operation}:ip:{ip}", limit)
            if not retry and operation == "login":
                if request.content_type == "application/json":
                    try:
                        payload = json.loads(request.body)
                        phone = payload.get("phone", "") if isinstance(payload, dict) else ""
                    except (ValueError, UnicodeDecodeError, RequestDataTooBig):
                        phone = ""
                else:
                    phone = request.POST.get("username", "")
                if isinstance(phone, str) and phone.strip():
                    retry = consume_limit(f"login:phone:{phone.strip()[:64]}", 10)
            if retry:
                message = "操作过于频繁，请稍后再试。"
                if request.path.startswith("/api/"):
                    response = JsonResponse({"error": {"code": "rate_limited", "message": message}}, status=429)
                else:
                    response = render(request, "verse/error.html", {"message": message}, status=429)
                response["Retry-After"] = str(retry)
                return response
        return self.get_response(request)
