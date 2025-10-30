from django.test import TestCase
from django.contrib.auth.models import User

from finance.emails.weekly_reminder.content import (
    build_reminder_email_subject,
    build_reminder_email_content,
)


class WeeklyReminderContentTests(TestCase):
    def setUp(self):
        self.user_with_name = User.objects.create_user(
            username="johndoe",
            email="john@example.com",
            password="testpass123",
            first_name="John",
        )

        self.user_without_name = User.objects.create_user(
            username="janedoe", email="jane@example.com", password="testpass123"
        )

    def test_build_reminder_email_subject(self):
        subject = build_reminder_email_subject()

        self.assertEqual(subject, "Reminder: Log Your Expenses This Week")

    def test_build_reminder_email_content_with_first_name(self):
        content = build_reminder_email_content(self.user_with_name)

        self.assertIn("Hello John", content)
        self.assertIn("haven't logged any expenses in the past 7 days", content)
        self.assertIn("Clink Finance Team", content)

    def test_build_reminder_email_content_without_first_name(self):
        content = build_reminder_email_content(self.user_without_name)

        self.assertIn("Hello janedoe", content)
        self.assertIn("haven't logged any expenses in the past 7 days", content)

    def test_content_includes_preference_management_info(self):
        content = build_reminder_email_content(self.user_with_name)

        self.assertIn("manage your email preferences", content)
