from django.db import models
from django.contrib.auth.models import User

from finance.enums import EmailType


class EmailLog(models.Model):
    EMAIL_TYPE_CHOICES: list[tuple[str, str]] = [
        (EmailType.WEEKLY_REMINDER.name, EmailType.WEEKLY_REMINDER.value),
        (EmailType.WEEKLY_SUMMARY.name, EmailType.WEEKLY_SUMMARY.value),
        (EmailType.MONTHLY_SUMMARY.name, EmailType.MONTHLY_SUMMARY.value),
        (EmailType.YEARLY_SUMMARY.name, EmailType.YEARLY_SUMMARY.value),
    ]

    user: models.ForeignKey = models.ForeignKey(
        User, on_delete=models.CASCADE, blank=False, null=False
    )

    email_type: models.CharField = models.CharField(
        max_length=20, choices=EMAIL_TYPE_CHOICES, blank=False, null=False
    )

    sent_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)

    success: models.BooleanField = models.BooleanField(default=False)

    error_message: models.TextField = models.TextField(blank=True, null=True)

    email_data: models.JSONField = models.JSONField(blank=True, null=True)

    class Meta:
        verbose_name = "Email Log"
        verbose_name_plural = "Email Logs"
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["email_type"]),
            models.Index(fields=["sent_at"]),
        ]
        ordering = ["-sent_at"]

    def __str__(self) -> str:
        status = "Success" if self.success else "Failed"
        return f"{self.user.username} - {self.email_type} - {status}"
