from django import forms

from finance.models.user_settings import UserSettings


class UserSettingsForm(forms.ModelForm):
    class Meta:
        model = UserSettings
        fields = [
            "weekly_reminder_enabled",
            "weekly_summary_enabled",
            "monthly_summary_enabled",
            "yearly_summary_enabled",
        ]
        widgets = {
            "weekly_reminder_enabled": forms.CheckboxInput(),
            "weekly_summary_enabled": forms.CheckboxInput(),
            "monthly_summary_enabled": forms.CheckboxInput(),
            "yearly_summary_enabled": forms.CheckboxInput(),
        }
        help_texts = {
            "weekly_reminder_enabled": "Receive email reminders at the start of each week to log your entries",
            "weekly_summary_enabled": "Receive a summary of your weekly activity and spending",
            "monthly_summary_enabled": "Receive a summary of your monthly activity and spending",
            "yearly_summary_enabled": "Receive a summary of your yearly activity and spending",
        }
