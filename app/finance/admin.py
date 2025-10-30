from django.contrib import admin

from finance.models import UserSettings, EmailLog


@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "weekly_reminder_enabled",
        "weekly_summary_enabled",
        "monthly_summary_enabled",
        "yearly_summary_enabled",
        "date_updated",
    ]
    list_filter = [
        "weekly_reminder_enabled",
        "weekly_summary_enabled",
        "monthly_summary_enabled",
        "yearly_summary_enabled",
    ]
    search_fields = ["user__username", "user__email"]
    readonly_fields = ["date_created", "date_updated"]


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ["user", "email_type", "success", "sent_at"]
    list_filter = ["email_type", "success", "sent_at"]
    search_fields = ["user__username", "user__email", "error_message"]
    readonly_fields = [
        "user",
        "email_type",
        "sent_at",
        "success",
        "error_message",
        "email_data",
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
