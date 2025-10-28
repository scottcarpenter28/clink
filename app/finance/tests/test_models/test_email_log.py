from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone

from finance.models import EmailLog
from finance.enums import EmailType


class EmailLogModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

    def test_email_log_creation(self):
        email_log = EmailLog.objects.create(
            user=self.user,
            email_type=EmailType.WEEKLY_REMINDER.name,
            success=True,
        )

        self.assertEqual(email_log.user, self.user)
        self.assertEqual(email_log.email_type, EmailType.WEEKLY_REMINDER.name)
        self.assertTrue(email_log.success)
        self.assertIsNotNone(email_log.sent_at)
        self.assertIsNone(email_log.error_message)
        self.assertIsNone(email_log.email_data)

    def test_email_log_string_representation(self):
        email_log = EmailLog.objects.create(
            user=self.user,
            email_type=EmailType.WEEKLY_SUMMARY.name,
            success=True,
        )

        expected_string = f"testuser - {EmailType.WEEKLY_SUMMARY.name} - Success"
        self.assertEqual(str(email_log), expected_string)

    def test_email_log_failed_status(self):
        email_log = EmailLog.objects.create(
            user=self.user,
            email_type=EmailType.MONTHLY_SUMMARY.name,
            success=False,
            error_message="SMTP connection failed",
        )

        self.assertFalse(email_log.success)
        self.assertEqual(email_log.error_message, "SMTP connection failed")
        expected_string = f"testuser - {EmailType.MONTHLY_SUMMARY.name} - Failed"
        self.assertEqual(str(email_log), expected_string)

    def test_email_log_with_data(self):
        email_data = {
            "total_spent": 150.50,
            "categories": ["Groceries", "Entertainment"],
            "budget_remaining": 349.50,
        }

        email_log = EmailLog.objects.create(
            user=self.user,
            email_type=EmailType.WEEKLY_SUMMARY.name,
            success=True,
            email_data=email_data,
        )

        self.assertEqual(email_log.email_data, email_data)
        self.assertEqual(email_log.email_data["total_spent"], 150.50)
        self.assertIn("Groceries", email_log.email_data["categories"])

    def test_email_log_ordering(self):
        email_log_1 = EmailLog.objects.create(
            user=self.user,
            email_type=EmailType.WEEKLY_REMINDER.name,
            success=True,
        )

        email_log_2 = EmailLog.objects.create(
            user=self.user,
            email_type=EmailType.WEEKLY_SUMMARY.name,
            success=True,
        )

        email_log_3 = EmailLog.objects.create(
            user=self.user,
            email_type=EmailType.MONTHLY_SUMMARY.name,
            success=True,
        )

        logs = EmailLog.objects.all()
        self.assertEqual(logs[0], email_log_3)
        self.assertEqual(logs[1], email_log_2)
        self.assertEqual(logs[2], email_log_1)

    def test_email_log_all_email_types(self):
        for email_type in EmailType:
            email_log = EmailLog.objects.create(
                user=self.user,
                email_type=email_type.name,
                success=True,
            )
            self.assertEqual(email_log.email_type, email_type.name)

    def test_email_log_cascade_delete(self):
        email_log = EmailLog.objects.create(
            user=self.user,
            email_type=EmailType.WEEKLY_REMINDER.name,
            success=True,
        )
        email_log_id = email_log.id

        self.user.delete()

        with self.assertRaises(EmailLog.DoesNotExist):
            EmailLog.objects.get(id=email_log_id)

    def test_email_log_default_success_false(self):
        email_log = EmailLog.objects.create(
            user=self.user,
            email_type=EmailType.YEARLY_SUMMARY.name,
        )

        self.assertFalse(email_log.success)
