from django.test import TestCase
from django.contrib.auth.models import User

from finance.models import Budget, Transaction
from finance.enums.transaction_enums import TransactionType
from finance.utils.budget_calculator import create_budget_line_items_for_type


class CreateBudgetLineItemsForTypeTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

    def test_returns_empty_list_when_no_budgets(self):
        budgets = Budget.objects.filter(user=self.user)
        transactions = Transaction.objects.filter(user=self.user)

        result = create_budget_line_items_for_type(
            TransactionType.INCOME, budgets, transactions, self.user, 2025, 10
        )

        self.assertEqual(result, [])

    def test_creates_line_items_for_type(self):
        Budget.objects.create(
            user=self.user,
            type=TransactionType.INCOME.name,
            category="Salary",
            amount_in_cents=500000,
            budget_year=2025,
            budget_month=10,
        )
        Budget.objects.create(
            user=self.user,
            type=TransactionType.INCOME.name,
            category="Freelance",
            amount_in_cents=100000,
            budget_year=2025,
            budget_month=10,
        )

        budgets = Budget.objects.filter(user=self.user)
        transactions = Transaction.objects.filter(user=self.user)

        result = create_budget_line_items_for_type(
            TransactionType.INCOME, budgets, transactions, self.user, 2025, 10
        )

        self.assertEqual(len(result), 2)

    def test_filters_by_transaction_type(self):
        Budget.objects.create(
            user=self.user,
            type=TransactionType.INCOME.name,
            category="Salary",
            amount_in_cents=500000,
            budget_year=2025,
            budget_month=10,
        )
        Budget.objects.create(
            user=self.user,
            type=TransactionType.NEED.name,
            category="Rent",
            amount_in_cents=150000,
            budget_year=2025,
            budget_month=10,
        )

        budgets = Budget.objects.filter(user=self.user)
        transactions = Transaction.objects.filter(user=self.user)

        result = create_budget_line_items_for_type(
            TransactionType.INCOME, budgets, transactions, self.user, 2025, 10
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["category"], "Salary")
