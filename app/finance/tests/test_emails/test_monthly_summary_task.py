from django.test import TestCase
from django.contrib.auth.models import User
from django.core import mail
from django.utils import timezone
from datetime import timedelta

from finance.models import UserSettings, Transaction, EmailLog
from finance.tasks.email_tasks import send_monthly_summaries
from finance.enums import TransactionType, EmailType


class MonthlySummaryTaskTests(TestCase):
    def setUp(self):
        current_date = timezone.now()

        self.user_with_transactions = User.objects.create_user(
            username="user1",
            email="user1@example.com",
            password="testpass123",
            first_name="User1",
        )
        UserSettings.objects.create(
            user=self.user_with_transactions, monthly_summary_enabled=True
        )
        Transaction.objects.create(
            user=self.user_with_transactions,
            type=TransactionType.NEED.name,
            category="Groceries",
            amount_in_cents=5000,
            date_of_expense=current_date.date(),
        )

        self.user_no_transactions = User.objects.create_user(
            username="user2",
            email="user2@example.com",
            password="testpass123",
            first_name="User2",
        )
        UserSettings.objects.create(
            user=self.user_no_transactions, monthly_summary_enabled=True
        )

        self.user_disabled = User.objects.create_user(
            username="user3",
            email="user3@example.com",
            password="testpass123",
            first_name="User3",
        )
        UserSettings.objects.create(
            user=self.user_disabled, monthly_summary_enabled=False
        )
        Transaction.objects.create(
            user=self.user_disabled,
            type=TransactionType.NEED.name,
            category="Groceries",
            amount_in_cents=5000,
            date_of_expense=current_date.date(),
        )

    def test_send_monthly_summaries_sends_to_eligible_users(self):
        result = send_monthly_summaries()

        self.assertEqual(result["sent"], 1)
        self.assertEqual(result["failed"], 0)
        self.assertEqual(len(mail.outbox), 1)

    def test_email_sent_has_correct_recipient(self):
        send_monthly_summaries()

        self.assertEqual(mail.outbox[0].to, ["user1@example.com"])

    def test_email_sent_has_correct_subject(self):
        current_date = timezone.now()
        month_name = current_date.strftime("%B")

        send_monthly_summaries()

        self.assertEqual(mail.outbox[0].subject, f"Your {month_name} Financial Summary")

    def test_email_sent_has_personalized_content(self):
        send_monthly_summaries()

        self.assertIn("Hello User1", mail.outbox[0].body)

    def test_email_includes_financial_summary(self):
        send_monthly_summaries()

        self.assertIn("Income: $", mail.outbox[0].body)
        self.assertIn("Total Expenses: $", mail.outbox[0].body)

    def test_creates_email_log_for_successful_send(self):
        send_monthly_summaries()

        log = EmailLog.objects.get(user=self.user_with_transactions)
        self.assertEqual(log.email_type, EmailType.MONTHLY_SUMMARY.name)
        self.assertTrue(log.success)
        self.assertIsNone(log.error_message)
        self.assertEqual(log.email_data["recipient"], "user1@example.com")

    def test_does_not_send_to_users_without_transactions(self):
        send_monthly_summaries()

        self.assertFalse(
            EmailLog.objects.filter(user=self.user_no_transactions).exists()
        )

    def test_does_not_send_to_users_with_disabled_summaries(self):
        send_monthly_summaries()

        self.assertFalse(EmailLog.objects.filter(user=self.user_disabled).exists())

    def test_handles_multiple_eligible_users(self):
        current_date = timezone.now()

        user4 = User.objects.create_user(
            username="user4",
            email="user4@example.com",
            password="testpass123",
        )
        UserSettings.objects.create(user=user4, monthly_summary_enabled=True)
        Transaction.objects.create(
            user=user4,
            type=TransactionType.INCOME.name,
            category="Salary",
            amount_in_cents=500000,
            date_of_expense=current_date.date(),
        )

        result = send_monthly_summaries()

        self.assertEqual(result["sent"], 2)
        self.assertEqual(len(mail.outbox), 2)

    def test_excludes_users_with_only_previous_month_transactions(self):
        current_date = timezone.now()
        previous_month_date = current_date.replace(day=1) - timedelta(days=1)

        user5 = User.objects.create_user(
            username="user5",
            email="user5@example.com",
            password="testpass123",
        )
        UserSettings.objects.create(user=user5, monthly_summary_enabled=True)
        Transaction.objects.create(
            user=user5,
            type=TransactionType.NEED.name,
            category="Old Purchase",
            amount_in_cents=10000,
            date_of_expense=previous_month_date.date(),
        )

        result = send_monthly_summaries()

        self.assertEqual(result["sent"], 1)
        self.assertFalse(EmailLog.objects.filter(user=user5).exists())
