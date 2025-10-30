from django.test import TestCase
from django.contrib.auth.models import User
from django.core import mail
from django.utils import timezone
from datetime import timedelta

from finance.models import UserSettings, Transaction, EmailLog, Budget
from finance.tasks.email_tasks import send_weekly_summaries
from finance.enums import TransactionType, EmailType


class WeeklySummaryTaskTests(TestCase):
    def setUp(self):
        self.user_with_transactions = User.objects.create_user(
            username="user1",
            email="user1@example.com",
            password="testpass123",
            first_name="User1",
        )
        UserSettings.objects.create(
            user=self.user_with_transactions, weekly_summary_enabled=True
        )
        Transaction.objects.create(
            user=self.user_with_transactions,
            type=TransactionType.NEED.name,
            category="Groceries",
            amount_in_cents=5000,
            date_of_expense=timezone.now().date(),
        )

        self.user_no_transactions = User.objects.create_user(
            username="user2",
            email="user2@example.com",
            password="testpass123",
            first_name="User2",
        )
        UserSettings.objects.create(
            user=self.user_no_transactions, weekly_summary_enabled=True
        )

        self.user_disabled = User.objects.create_user(
            username="user3",
            email="user3@example.com",
            password="testpass123",
            first_name="User3",
        )
        UserSettings.objects.create(
            user=self.user_disabled, weekly_summary_enabled=False
        )
        Transaction.objects.create(
            user=self.user_disabled,
            type=TransactionType.NEED.name,
            category="Groceries",
            amount_in_cents=5000,
            date_of_expense=timezone.now().date(),
        )

    def test_send_weekly_summaries_sends_to_eligible_users(self):
        result = send_weekly_summaries()

        self.assertEqual(result["sent"], 1)
        self.assertEqual(result["failed"], 0)
        self.assertEqual(len(mail.outbox), 1)

    def test_email_sent_has_correct_recipient(self):
        send_weekly_summaries()

        self.assertEqual(mail.outbox[0].to, ["user1@example.com"])

    def test_email_sent_has_correct_subject(self):
        send_weekly_summaries()

        self.assertEqual(mail.outbox[0].subject, "Your Weekly Spending Summary")

    def test_email_sent_has_personalized_content(self):
        send_weekly_summaries()

        self.assertIn("Hello User1", mail.outbox[0].body)

    def test_email_includes_spending_details(self):
        send_weekly_summaries()

        self.assertIn("Groceries: $50.00", mail.outbox[0].body)
        self.assertIn("Total Spent: $50.00", mail.outbox[0].body)

    def test_creates_email_log_for_successful_send(self):
        send_weekly_summaries()

        log = EmailLog.objects.get(user=self.user_with_transactions)
        self.assertEqual(log.email_type, EmailType.WEEKLY_SUMMARY.name)
        self.assertTrue(log.success)
        self.assertIsNone(log.error_message)
        self.assertEqual(log.email_data["recipient"], "user1@example.com")

    def test_does_not_send_to_users_without_transactions(self):
        send_weekly_summaries()

        self.assertFalse(
            EmailLog.objects.filter(user=self.user_no_transactions).exists()
        )

    def test_does_not_send_to_users_with_disabled_summaries(self):
        send_weekly_summaries()

        self.assertFalse(EmailLog.objects.filter(user=self.user_disabled).exists())

    def test_handles_multiple_eligible_users(self):
        user4 = User.objects.create_user(
            username="user4",
            email="user4@example.com",
            password="testpass123",
        )
        UserSettings.objects.create(user=user4, weekly_summary_enabled=True)
        Transaction.objects.create(
            user=user4,
            type=TransactionType.WANT.name,
            category="Entertainment",
            amount_in_cents=3000,
            date_of_expense=timezone.now().date(),
        )

        result = send_weekly_summaries()

        self.assertEqual(result["sent"], 2)
        self.assertEqual(len(mail.outbox), 2)

    def test_includes_budget_information_when_available(self):
        current_date = timezone.now()
        Budget.objects.create(
            user=self.user_with_transactions,
            type=TransactionType.NEED.name,
            category="Groceries",
            amount_in_cents=10000,
            budget_year=current_date.year,
            budget_month=current_date.month,
            carried_over_amount_in_cents=0,
        )

        send_weekly_summaries()

        self.assertIn("BUDGET STATUS", mail.outbox[0].body)
        self.assertIn("Groceries: $50.00 / $100.00", mail.outbox[0].body)
        self.assertIn("$50.00 remaining", mail.outbox[0].body)
