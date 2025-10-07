from decimal import Decimal

from django.test import TestCase
from django.contrib.auth.models import User

from finance.models import Budget, Transaction
from finance.enums.transaction_enums import TransactionType
from finance.utils.budget_calculator import group_budgets_with_actuals


class GroupBudgetsWithActualsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

    def test_creates_groups_for_all_transaction_types(self):
        budgets = Budget.objects.filter(user=self.user)
        transactions = Transaction.objects.filter(user=self.user)

        result = group_budgets_with_actuals(budgets, transactions)

        for transaction_type in TransactionType:
            self.assertIn(transaction_type.value, result)

    def test_groups_budgets_by_type(self):
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
        Budget.objects.create(
            user=self.user,
            type=TransactionType.NEED.name,
            category="Groceries",
            amount_in_cents=50000,
            budget_year=2025,
            budget_month=10,
        )

        budgets = Budget.objects.filter(user=self.user)
        transactions = Transaction.objects.filter(user=self.user)

        result = group_budgets_with_actuals(budgets, transactions)

        self.assertEqual(len(result[TransactionType.INCOME.value]), 1)
        self.assertEqual(len(result[TransactionType.NEED.value]), 2)
        self.assertEqual(len(result[TransactionType.WANT.value]), 0)

    def test_includes_actual_spent_amounts(self):
        Budget.objects.create(
            user=self.user,
            type=TransactionType.NEED.name,
            category="Rent",
            amount_in_cents=150000,
            budget_year=2025,
            budget_month=10,
        )
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.NEED.name,
            category="Rent",
            amount_in_cents=150000,
            date_of_expense="2025-10-01",
        )

        budgets = Budget.objects.filter(user=self.user)
        transactions = Transaction.objects.filter(user=self.user)

        result = group_budgets_with_actuals(budgets, transactions)

        need_budgets = result[TransactionType.NEED.value]
        self.assertEqual(len(need_budgets), 1)
        self.assertEqual(need_budgets[0]["expected"], Decimal("1500.00"))
        self.assertEqual(need_budgets[0]["actual"], Decimal("1500.00"))
        self.assertEqual(need_budgets[0]["remaining"], Decimal("0.00"))
