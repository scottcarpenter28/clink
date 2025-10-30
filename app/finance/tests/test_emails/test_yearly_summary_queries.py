from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from finance.models import UserSettings, Transaction
from finance.emails.yearly_summary.queries import get_users_needing_yearly_summary
from finance.enums import TransactionType


class YearlySummaryQueriesTests(TestCase):
    def setUp(self):
        self.user_with_transactions = User.objects.create_user(
            username="user_with_transactions",
            email="user1@example.com",
            password="testpass123",
        )
        UserSettings.objects.create(
            user=self.user_with_transactions, yearly_summary_enabled=True
        )

        self.user_disabled = User.objects.create_user(
            username="user_disabled",
            email="user2@example.com",
            password="testpass123",
        )
        UserSettings.objects.create(
            user=self.user_disabled, yearly_summary_enabled=False
        )

        self.user_no_email = User.objects.create_user(
            username="user_no_email", email="", password="testpass123"
        )
        UserSettings.objects.create(
            user=self.user_no_email, yearly_summary_enabled=True
        )

        self.user_no_transactions = User.objects.create_user(
            username="user_no_transactions",
            email="user3@example.com",
            password="testpass123",
        )
        UserSettings.objects.create(
            user=self.user_no_transactions, yearly_summary_enabled=True
        )

    def test_includes_users_with_current_year_transactions(self):
        current_date = timezone.now()
        Transaction.objects.create(
            user=self.user_with_transactions,
            type=TransactionType.NEED.name,
            category="Groceries",
            amount_in_cents=5000,
            date_of_expense=current_date.date(),
        )

        users = get_users_needing_yearly_summary()

        self.assertIn(self.user_with_transactions, users)

    def test_excludes_users_with_disabled_summaries(self):
        current_date = timezone.now()
        Transaction.objects.create(
            user=self.user_disabled,
            type=TransactionType.NEED.name,
            category="Groceries",
            amount_in_cents=5000,
            date_of_expense=current_date.date(),
        )

        users = get_users_needing_yearly_summary()

        self.assertNotIn(self.user_disabled, users)

    def test_excludes_users_without_email(self):
        current_date = timezone.now()
        Transaction.objects.create(
            user=self.user_no_email,
            type=TransactionType.NEED.name,
            category="Groceries",
            amount_in_cents=5000,
            date_of_expense=current_date.date(),
        )

        users = get_users_needing_yearly_summary()

        self.assertNotIn(self.user_no_email, users)

    def test_excludes_users_without_current_year_transactions(self):
        users = get_users_needing_yearly_summary()

        self.assertNotIn(self.user_no_transactions, users)

    def test_excludes_users_with_only_previous_year_transactions(self):
        current_date = timezone.now()
        previous_year_date = current_date.replace(year=current_date.year - 1)

        Transaction.objects.create(
            user=self.user_with_transactions,
            type=TransactionType.NEED.name,
            category="Groceries",
            amount_in_cents=5000,
            date_of_expense=previous_year_date.date(),
        )

        users = get_users_needing_yearly_summary()

        self.assertNotIn(self.user_with_transactions, users)

    def test_includes_users_with_transactions_at_start_of_year(self):
        current_date = timezone.now()
        first_of_year = current_date.replace(month=1, day=1)

        Transaction.objects.create(
            user=self.user_with_transactions,
            type=TransactionType.NEED.name,
            category="Groceries",
            amount_in_cents=5000,
            date_of_expense=first_of_year.date(),
        )

        users = get_users_needing_yearly_summary()

        self.assertIn(self.user_with_transactions, users)
