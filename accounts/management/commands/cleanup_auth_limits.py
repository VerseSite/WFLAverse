from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import RateLimitBucket


class Command(BaseCommand):
    help = "清理已过期的认证请求限流记录（可定期手动运行）。"

    def handle(self, *args, **options):
        deleted, _ = RateLimitBucket.objects.filter(
            started_at__lt=timezone.now() - timedelta(seconds=settings.AUTH_RATE_LIMIT_WINDOW),
        ).delete()
        self.stdout.write(f"已清理 {deleted} 条记录。")
