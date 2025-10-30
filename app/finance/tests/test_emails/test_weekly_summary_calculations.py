from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from finance.models import Transaction, Budget
from finance.emails.weekly_summary.calculations import (
    calculate_weekly_totals,
    calculate_remaining_budgets,
)
from finance.enums import TransactionType


class WeeklySummaryCalculationsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

    def test_calculate_weekly_totals_with_multiple_categories(self):
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.NEED.name,
            category="Groceries",
            amount_in_cents=5000,
            date_of_expense=timezone.now().date(),
        )
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.WANT.name,
            category="Entertainment",
            amount_in_cents=3000,
            date_of_expense=timezone.now().date() - timedelta(days=3),
        )
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.NEED.name,
            category="Groceries",
            amount_in_cents=2500,
            date_of_expense=timezone.now().date() - timedelta(days=5),
        )

        result = calculate_weekly_totals(self.user)

        self.assertEqual(len(result["totals_by_category"]), 2)
        self.assertEqual(result["grand_total"], 105.0)

        groceries = next(
            ct for ct in result["totals_by_category"] if ct["category"] == "Groceries"
        )
        self.assertEqual(groceries["total"], 75.0)

        entertainment = next(
            ct
            for ct in result["totals_by_category"]
            if ct["category"] == "Entertainment"
        )
        self.assertEqual(entertainment["total"], 30.0)

    def test_calculate_weekly_totals_excludes_old_transactions(self):
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.NEED.name,
            category="Groceries",
            amount_in_cents=5000,
            date_of_expense=timezone.now().date(),
        )
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.NEED.name,
            category="Old Purchase",
            amount_in_cents=10000,
            date_of_expense=timezone.now().date() - timedelta(days=8),
        )

        result = calculate_weekly_totals(self.user)

        self.assertEqual(len(result["totals_by_category"]), 1)
        self.assertEqual(result["grand_total"], 50.0)
        self.assertEqual(result["totals_by_category"][0]["category"], "Groceries")

    def test_calculate_weekly_totals_with_no_transactions(self):
        result = calculate_weekly_totals(self.user)

        self.assertEqual(len(result["totals_by_category"]), 0)
        self.assertEqual(result["grand_total"], 0.0)
        self.assertEqual(len(result["remaining_budgets"]), 0)

    def test_calculate_remaining_budgets_with_budget_and_spending(self):
        current_date = timezone.now()

        Budget.objects.create(
            user=self.user,
            type=TransactionType.NEED.name,
            category="Groceries",
            amount_in_cents=20000,
            budget_year=current_date.year,
            budget_month=current_date.month,
            carried_over_amount_in_cents=0,
        )

        Transaction.objects.create(
            user=self.user,
            type=TransactionType.NEED.name,
            category="Groceries",
            amount_in_cents=5000,
            date_of_expense=current_date.date(),
        )

        result = calculate_weekly_totals(self.user)

        self.assertEqual(len(result["remaining_budgets"]), 1)
        budget_info = result["remaining_budgets"][0]
        self.assertEqual(budget_info["category"], "Groceries")
        self.assertEqual(budget_info["budget"], 200.0)
        self.assertEqual(budget_info["spent"], 50.0)
        self.assertEqual(budget_info["remaining"], 150.0)

    def test_calculate_remaining_budgets_with_overspending(self):
        current_date = timezone.now()

        Budget.objects.create(
            user=self.user,
            type=TransactionType.NEED.name,
            category="Groceries",
            amount_in_cents=10000,
            budget_year=current_date.year,
            budget_month=current_date.month,
            carried_over_amount_in_cents=0,
        )

        Transaction.objects.create(
            user=self.user,
            type=TransactionType.NEED.name,
            category="Groceries",
            amount_in_cents=15000,
            date_of_expense=current_date.date(),
        )

        result = calculate_weekly_totals(self.user)

        budget_info = result["remaining_budgets"][0]
        self.assertEqual(budget_info["category"], "Groceries")
        self.assertEqual(budget_info["budget"], 100.0)
        self.assertEqual(budget_info["spent"], 150.0)
        self.assertEqual(budget_info["remaining"], -50.0)

    def test_calculate_remaining_budgets_with_carried_over_amount(self):
        current_date = timezone.now()

        Budget.objects.create(
            user=self.user,
            type=TransactionType.NEED.name,
            category="Groceries",
            amount_in_cents=10000,
            budget_year=current_date.year,
            budget_month=current_date.month,
            carried_over_amount_in_cents=5000,
        )

        Transaction.objects.create(
            user=self.user,
            type=TransactionType.NEED.name,
            category="Groceries",
            amount_in_cents=12000,
            date_of_expense=current_date.date(),
        )

        result = calculate_weekly_totals(self.user)

        budget_info = result["remaining_budgets"][0]
        self.assertEqual(budget_info["budget"], 150.0)
        self.assertEqual(budget_info["spent"], 120.0)
        self.assertEqual(budget_info["remaining"], 30.0)

    def test_calculate_remaining_budgets_sorted_by_remaining(self):
        current_date = timezone.now()

        Budget.objects.create(
            user=self.user,
            type=TransactionType.NEED.name,
            category="Groceries",
            amount_in_cents=10000,
            budget_year=current_date.year,
            budget_month=current_date.month,
            carried_over_amount_in_cents=0,
        )

        Budget.objects.create(
            user=self.user,
            type=TransactionType.WANT.name,
            category="Entertainment",
            amount_in_cents=20000,
            budget_year=current_date.year,
            budget_month=current_date.month,
            carried_over_amount_in_cents=0,
        )

        Transaction.objects.create(
            user=self.user,
            type=TransactionType.NEED.name,
            category="Groceries",
            amount_in_cents=9000,
            date_of_expense=current_date.date(),
        )

        Transaction.objects.create(
            user=self.user,
            type=TransactionType.WANT.name,
            category="Entertainment",
            amount_in_cents=5000,
            date_of_expense=current_date.date(),
        )

        result = calculate_weekly_totals(self.user)

        self.assertEqual(len(result["remaining_budgets"]), 2)
        self.assertEqual(result["remaining_budgets"][0]["category"], "Groceries")
        self.assertEqual(result["remaining_budgets"][0]["remaining"], 10.0)
        self.assertEqual(result["remaining_budgets"][1]["category"], "Entertainment")
        self.assertEqual(result["remaining_budgets"][1]["remaining"], 150.0)
