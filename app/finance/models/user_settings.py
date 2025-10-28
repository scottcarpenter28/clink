from django.db import models
from django.contrib.auth.models import User


class UserSettings(models.Model):
    user: models.OneToOneField = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="email_settings"
    )

    weekly_reminder_enabled: models.BooleanField = models.BooleanField(default=True)
    weekly_summary_enabled: models.BooleanField = models.BooleanField(default=True)
    monthly_summary_enabled: models.BooleanField = models.BooleanField(default=True)
    yearly_summary_enabled: models.BooleanField = models.BooleanField(default=True)

    date_created: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    date_updated: models.DateTimeField = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User Settings"
        verbose_name_plural = "User Settings"

    def __str__(self) -> str:
        return f"{self.user.username} - Email Settings"
