from django.test import TestCase
from django.contrib.auth.models import User
from django.core import mail
from django.utils import timezone
from datetime import timedelta

from finance.models import UserSettings, Transaction, EmailLog
from finance.tasks.email_tasks import send_weekly_reminders
from finance.enums import TransactionType, EmailType


class WeeklyReminderTaskTests(TestCase):
    def setUp(self):
        self.user_needs_reminder = User.objects.create_user(
            username="user1",
            email="user1@example.com",
            password="testpass123",
            first_name="User1",
        )
        UserSettings.objects.create(
            user=self.user_needs_reminder, weekly_reminder_enabled=True
        )

        self.user_with_recent_transaction = User.objects.create_user(
            username="user2",
            email="user2@example.com",
            password="testpass123",
            first_name="User2",
        )
        UserSettings.objects.create(
            user=self.user_with_recent_transaction, weekly_reminder_enabled=True
        )
        Transaction.objects.create(
            user=self.user_with_recent_transaction,
            type=TransactionType.NEED.name,
            category="Groceries",
            amount_in_cents=5000,
            date_of_expense=timezone.now().date(),
        )

        self.user_disabled = User.objects.create_user(
            username="user3",
            email="user3@example.com",
            password="testpass123",
            first_name="User3",
        )
        UserSettings.objects.create(
            user=self.user_disabled, weekly_reminder_enabled=False
        )

    def test_send_weekly_reminders_sends_to_eligible_users(self):
        result = send_weekly_reminders()

        self.assertEqual(result["sent"], 1)
        self.assertEqual(result["failed"], 0)
        self.assertEqual(len(mail.outbox), 1)

    def test_email_sent_has_correct_recipient(self):
        send_weekly_reminders()

        self.assertEqual(mail.outbox[0].to, ["user1@example.com"])

    def test_email_sent_has_correct_subject(self):
        send_weekly_reminders()

        self.assertEqual(
            mail.outbox[0].subject, "Reminder: Log Your Expenses This Week"
        )

    def test_email_sent_has_personalized_content(self):
        send_weekly_reminders()

        self.assertIn("Hello User1", mail.outbox[0].body)

    def test_creates_email_log_for_successful_send(self):
        send_weekly_reminders()

        log = EmailLog.objects.get(user=self.user_needs_reminder)
        self.assertEqual(log.email_type, EmailType.WEEKLY_REMINDER.name)
        self.assertTrue(log.success)
        self.assertIsNone(log.error_message)
        self.assertEqual(log.email_data["recipient"], "user1@example.com")

    def test_does_not_send_to_users_with_recent_transactions(self):
        send_weekly_reminders()

        self.assertFalse(
            EmailLog.objects.filter(user=self.user_with_recent_transaction).exists()
        )

    def test_does_not_send_to_users_with_disabled_reminders(self):
        send_weekly_reminders()

        self.assertFalse(EmailLog.objects.filter(user=self.user_disabled).exists())

    def test_handles_multiple_eligible_users(self):
        user4 = User.objects.create_user(
            username="user4",
            email="user4@example.com",
            password="testpass123",
        )
        UserSettings.objects.create(user=user4, weekly_reminder_enabled=True)

        result = send_weekly_reminders()

        self.assertEqual(result["sent"], 2)
        self.assertEqual(len(mail.outbox), 2)
