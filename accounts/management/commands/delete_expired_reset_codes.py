from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from your_app.models import PasswordResetCode

class Command(BaseCommand):
    help = 'Delete expired password reset codes older than 2 minutes.'

    def handle(self, *args, **kwargs):
        expiration_time = timezone.now() - timedelta(minutes=2)
        expired = PasswordResetCode.objects.filter(created_at__lt=expiration_time, is_used=False)
        count = expired.count()
        expired.delete()
        self.stdout.write(f"Deleted {count} expired reset code(s).")
