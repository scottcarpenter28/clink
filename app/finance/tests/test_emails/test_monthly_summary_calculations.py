from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from finance.models import Transaction
from finance.emails.monthly_summary.calculations import calculate_monthly_totals
from finance.enums import TransactionType


class MonthlySummaryCalculationsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

    def test_calculate_monthly_totals_with_all_transaction_types(self):
        current_date = timezone.now()

        Transaction.objects.create(
            user=self.user,
            type=TransactionType.INCOME.name,
            category="Salary",
            amount_in_cents=500000,
            date_of_expense=current_date.date(),
        )
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.SAVINGS.name,
            category="Emergency Fund",
            amount_in_cents=100000,
            date_of_expense=current_date.date(),
        )
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.INVESTING.name,
            category="Retirement",
            amount_in_cents=75000,
            date_of_expense=current_date.date(),
        )
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.NEED.name,
            category="Groceries",
            amount_in_cents=25000,
            date_of_expense=current_date.date(),
        )
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.WANT.name,
            category="Entertainment",
            amount_in_cents=15000,
            date_of_expense=current_date.date(),
        )
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.DEBTS.name,
            category="Credit Card",
            amount_in_cents=10000,
            date_of_expense=current_date.date(),
        )

        result = calculate_monthly_totals(self.user)

        self.assertEqual(result["income"], 5000.0)
        self.assertEqual(result["savings"], 1000.0)
        self.assertEqual(result["investing"], 750.0)
        self.assertEqual(result["needs"], 250.0)
        self.assertEqual(result["wants"], 150.0)
        self.assertEqual(result["debts"], 100.0)
        self.assertEqual(result["total_expenses"], 2250.0)

    def test_calculate_monthly_totals_excludes_previous_month(self):
        current_date = timezone.now()
        previous_month_date = current_date.replace(day=1) - timedelta(days=1)

        Transaction.objects.create(
            user=self.user,
            type=TransactionType.NEED.name,
            category="Old Purchase",
            amount_in_cents=100000,
            date_of_expense=previous_month_date.date(),
        )
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.NEED.name,
            category="Current Purchase",
            amount_in_cents=50000,
            date_of_expense=current_date.date(),
        )

        result = calculate_monthly_totals(self.user)

        self.assertEqual(result["needs"], 500.0)
        self.assertEqual(result["total_expenses"], 500.0)

    def test_calculate_monthly_totals_with_no_transactions(self):
        result = calculate_monthly_totals(self.user)

        self.assertEqual(result["income"], 0.0)
        self.assertEqual(result["savings"], 0.0)
        self.assertEqual(result["investing"], 0.0)
        self.assertEqual(result["needs"], 0.0)
        self.assertEqual(result["wants"], 0.0)
        self.assertEqual(result["debts"], 0.0)
        self.assertEqual(result["total_expenses"], 0.0)
        self.assertEqual(len(result["totals_by_type"]), 0)

    def test_calculate_monthly_totals_with_multiple_same_type(self):
        current_date = timezone.now()

        Transaction.objects.create(
            user=self.user,
            type=TransactionType.NEED.name,
            category="Groceries",
            amount_in_cents=25000,
            date_of_expense=current_date.date(),
        )
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.NEED.name,
            category="Utilities",
            amount_in_cents=15000,
            date_of_expense=current_date.date(),
        )

        result = calculate_monthly_totals(self.user)

        self.assertEqual(result["needs"], 400.0)
        self.assertEqual(result["total_expenses"], 400.0)

    def test_calculate_monthly_totals_totals_by_type_contains_human_readable_names(
        self,
    ):
        current_date = timezone.now()

        Transaction.objects.create(
            user=self.user,
            type=TransactionType.INCOME.name,
            category="Salary",
            amount_in_cents=500000,
            date_of_expense=current_date.date(),
        )

        result = calculate_monthly_totals(self.user)

        self.assertEqual(len(result["totals_by_type"]), 1)
        self.assertEqual(result["totals_by_type"][0]["type"], "Income")
        self.assertEqual(result["totals_by_type"][0]["total"], 5000.0)

    def test_calculate_monthly_totals_includes_current_month_start(self):
        current_date = timezone.now()
        first_of_month = current_date.replace(day=1)

        Transaction.objects.create(
            user=self.user,
            type=TransactionType.NEED.name,
            category="Groceries",
            amount_in_cents=10000,
            date_of_expense=first_of_month.date(),
        )

        result = calculate_monthly_totals(self.user)

        self.assertEqual(result["needs"], 100.0)

    def test_total_expenses_excludes_income(self):
        current_date = timezone.now()

        Transaction.objects.create(
            user=self.user,
            type=TransactionType.INCOME.name,
            category="Salary",
            amount_in_cents=500000,
            date_of_expense=current_date.date(),
        )
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.NEED.name,
            category="Groceries",
            amount_in_cents=25000,
            date_of_expense=current_date.date(),
        )

        result = calculate_monthly_totals(self.user)

        self.assertEqual(result["total_expenses"], 250.0)
        self.assertEqual(result["income"], 5000.0)
