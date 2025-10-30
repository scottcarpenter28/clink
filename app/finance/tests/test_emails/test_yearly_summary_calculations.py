from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from finance.models import Transaction
from finance.emails.yearly_summary.calculations import calculate_yearly_totals
from finance.enums import TransactionType


class YearlySummaryCalculationsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

    def test_calculate_yearly_totals_with_multiple_categories(self):
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
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.WANT.name,
            category="Entertainment",
            amount_in_cents=15000,
            date_of_expense=current_date.date(),
        )

        result = calculate_yearly_totals(self.user)

        self.assertEqual(result["total_income"], 5000.0)
        self.assertEqual(result["total_expenses"], 400.0)
        self.assertEqual(result["net_income"], 4600.0)
        self.assertEqual(result["grand_total"], 5400.0)

    def test_calculate_yearly_totals_excludes_previous_year(self):
        current_date = timezone.now()
        previous_year_date = current_date.replace(year=current_date.year - 1)

        Transaction.objects.create(
            user=self.user,
            type=TransactionType.NEED.name,
            category="Old Purchase",
            amount_in_cents=100000,
            date_of_expense=previous_year_date.date(),
        )
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.NEED.name,
            category="Current Purchase",
            amount_in_cents=50000,
            date_of_expense=current_date.date(),
        )

        result = calculate_yearly_totals(self.user)

        self.assertEqual(result["total_expenses"], 500.0)
        self.assertEqual(len(result["totals_by_category"]), 1)

    def test_calculate_yearly_totals_with_no_transactions(self):
        result = calculate_yearly_totals(self.user)

        self.assertEqual(result["total_income"], 0.0)
        self.assertEqual(result["total_expenses"], 0.0)
        self.assertEqual(result["net_income"], 0.0)
        self.assertEqual(result["grand_total"], 0.0)
        self.assertEqual(len(result["totals_by_category"]), 0)

    def test_calculate_yearly_totals_includes_category_with_type(self):
        current_date = timezone.now()

        Transaction.objects.create(
            user=self.user,
            type=TransactionType.NEED.name,
            category="Groceries",
            amount_in_cents=25000,
            date_of_expense=current_date.date(),
        )

        result = calculate_yearly_totals(self.user)

        self.assertEqual(len(result["totals_by_category"]), 1)
        self.assertEqual(
            result["totals_by_category"][0]["category"], "Groceries (NEED)"
        )
        self.assertEqual(result["totals_by_category"][0]["total"], 250.0)

    def test_calculate_yearly_totals_separates_same_category_different_types(self):
        current_date = timezone.now()

        Transaction.objects.create(
            user=self.user,
            type=TransactionType.NEED.name,
            category="Rent",
            amount_in_cents=100000,
            date_of_expense=current_date.date(),
        )
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.DEBTS.name,
            category="Rent",
            amount_in_cents=50000,
            date_of_expense=current_date.date(),
        )

        result = calculate_yearly_totals(self.user)

        self.assertEqual(len(result["totals_by_category"]), 2)
        categories = [ct["category"] for ct in result["totals_by_category"]]
        self.assertIn("Rent (NEED)", categories)
        self.assertIn("Rent (DEBTS)", categories)

    def test_net_income_negative_when_expenses_exceed_income(self):
        current_date = timezone.now()

        Transaction.objects.create(
            user=self.user,
            type=TransactionType.INCOME.name,
            category="Salary",
            amount_in_cents=100000,
            date_of_expense=current_date.date(),
        )
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.NEED.name,
            category="Expenses",
            amount_in_cents=150000,
            date_of_expense=current_date.date(),
        )

        result = calculate_yearly_totals(self.user)

        self.assertEqual(result["total_income"], 1000.0)
        self.assertEqual(result["total_expenses"], 1500.0)
        self.assertEqual(result["net_income"], -500.0)

    def test_calculate_yearly_totals_includes_all_months(self):
        current_date = timezone.now()
        year_start = current_date.replace(month=1, day=1)

        Transaction.objects.create(
            user=self.user,
            type=TransactionType.NEED.name,
            category="January Purchase",
            amount_in_cents=10000,
            date_of_expense=year_start.date(),
        )
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.NEED.name,
            category="Current Purchase",
            amount_in_cents=10000,
            date_of_expense=current_date.date(),
        )

        result = calculate_yearly_totals(self.user)

        self.assertEqual(result["total_expenses"], 200.0)
