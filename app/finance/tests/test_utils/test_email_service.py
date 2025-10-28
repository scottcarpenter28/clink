from django.test import TestCase
from django.contrib.auth.models import User
from django.core import mail
from unittest.mock import patch

from finance.models import EmailLog
from finance.utils.email_service import send_email_with_logging
from finance.enums.email_enums import EmailType


class EmailServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )

    def test_send_email_with_logging_sends_email(self):
        success = send_email_with_logging(
            user=self.user,
            email_type=EmailType.WEEKLY_REMINDER,
            subject="Test Subject",
            content="Test Content",
        )

        self.assertTrue(success)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Test Subject")
        self.assertEqual(mail.outbox[0].body, "Test Content")
        self.assertEqual(mail.outbox[0].to, ["test@example.com"])

    def test_creates_successful_email_log(self):
        send_email_with_logging(
            user=self.user,
            email_type=EmailType.WEEKLY_REMINDER,
            subject="Test Subject",
            content="Test Content",
        )

        log = EmailLog.objects.get(user=self.user)
        self.assertTrue(log.success)
        self.assertEqual(log.email_type, EmailType.WEEKLY_REMINDER.name)
        self.assertIsNone(log.error_message)
        self.assertEqual(log.email_data["subject"], "Test Subject")
        self.assertEqual(log.email_data["content"], "Test Content")
        self.assertEqual(log.email_data["recipient"], "test@example.com")

    @patch("finance.utils.email_service.send_mail")
    def test_creates_failed_email_log_on_exception(self, mock_send_mail):
        mock_send_mail.side_effect = Exception("SMTP Error")

        success = send_email_with_logging(
            user=self.user,
            email_type=EmailType.WEEKLY_REMINDER,
            subject="Test Subject",
            content="Test Content",
        )

        self.assertFalse(success)
        log = EmailLog.objects.get(user=self.user)
        self.assertFalse(log.success)
        self.assertEqual(log.error_message, "SMTP Error")
        self.assertEqual(log.email_type, EmailType.WEEKLY_REMINDER.name)

    def test_handles_different_email_types(self):
        send_email_with_logging(
            user=self.user,
            email_type=EmailType.MONTHLY_SUMMARY,
            subject="Monthly Summary",
            content="Monthly Content",
        )

        log = EmailLog.objects.get(user=self.user)
        self.assertEqual(log.email_type, EmailType.MONTHLY_SUMMARY.name)
