from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from finance.models import UserSettings, Transaction
from finance.emails.weekly_summary.queries import get_users_needing_weekly_summary
from finance.enums import TransactionType


class WeeklySummaryQueriesTests(TestCase):
    def setUp(self):
        self.user_with_transactions = User.objects.create_user(
            username="user_with_transactions",
            email="user1@example.com",
            password="testpass123",
        )
        UserSettings.objects.create(
            user=self.user_with_transactions, weekly_summary_enabled=True
        )

        self.user_disabled = User.objects.create_user(
            username="user_disabled",
            email="user2@example.com",
            password="testpass123",
        )
        UserSettings.objects.create(
            user=self.user_disabled, weekly_summary_enabled=False
        )

        self.user_no_email = User.objects.create_user(
            username="user_no_email", email="", password="testpass123"
        )
        UserSettings.objects.create(
            user=self.user_no_email, weekly_summary_enabled=True
        )

        self.user_no_transactions = User.objects.create_user(
            username="user_no_transactions",
            email="user3@example.com",
            password="testpass123",
        )
        UserSettings.objects.create(
            user=self.user_no_transactions, weekly_summary_enabled=True
        )

    def test_includes_users_with_recent_transactions(self):
        Transaction.objects.create(
            user=self.user_with_transactions,
            type=TransactionType.NEED.name,
            category="Groceries",
            amount_in_cents=5000,
            date_of_expense=timezone.now().date(),
        )

        users = get_users_needing_weekly_summary()

        self.assertIn(self.user_with_transactions, users)

    def test_excludes_users_with_disabled_summaries(self):
        Transaction.objects.create(
            user=self.user_disabled,
            type=TransactionType.NEED.name,
            category="Groceries",
            amount_in_cents=5000,
            date_of_expense=timezone.now().date(),
        )

        users = get_users_needing_weekly_summary()

        self.assertNotIn(self.user_disabled, users)

    def test_excludes_users_without_email(self):
        Transaction.objects.create(
            user=self.user_no_email,
            type=TransactionType.NEED.name,
            category="Groceries",
            amount_in_cents=5000,
            date_of_expense=timezone.now().date(),
        )

        users = get_users_needing_weekly_summary()

        self.assertNotIn(self.user_no_email, users)

    def test_excludes_users_without_recent_transactions(self):
        users = get_users_needing_weekly_summary()

        self.assertNotIn(self.user_no_transactions, users)

    def test_excludes_users_with_old_transactions_only(self):
        Transaction.objects.create(
            user=self.user_with_transactions,
            type=TransactionType.NEED.name,
            category="Groceries",
            amount_in_cents=5000,
            date_of_expense=timezone.now().date() - timedelta(days=8),
        )

        users = get_users_needing_weekly_summary()

        self.assertNotIn(self.user_with_transactions, users)

    def test_includes_users_with_transactions_exactly_7_days_ago(self):
        Transaction.objects.create(
            user=self.user_with_transactions,
            type=TransactionType.NEED.name,
            category="Groceries",
            amount_in_cents=5000,
            date_of_expense=timezone.now().date() - timedelta(days=6),
        )

        users = get_users_needing_weekly_summary()

        self.assertIn(self.user_with_transactions, users)
