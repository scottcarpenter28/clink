from decimal import Decimal

from django.test import TestCase
from django.contrib.auth.models import User

from finance.models import Budget, Transaction
from finance.enums.transaction_enums import TransactionType
from finance.utils.budget_calculator import (
    BudgetLineItem,
    calculate_actual_spent_for_budget,
    create_budget_line_items_for_type,
    group_budgets_with_actuals,
)


class BudgetLineItemTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.budget = Budget.objects.create(
            user=self.user,
            type=TransactionType.NEED.value,
            category="Rent",
            amount_in_cents=150000,
            budget_year=2025,
            budget_month=10,
        )

    def test_budget_line_item_calculates_values(self):
        line_item = BudgetLineItem(self.budget, 100000)

        self.assertEqual(line_item.id, self.budget.id)
        self.assertEqual(line_item.category, "Rent")
        self.assertEqual(line_item.expected, Decimal("1500.00"))
        self.assertEqual(line_item.actual, Decimal("1000.00"))
        self.assertEqual(line_item.remaining, Decimal("500.00"))

    def test_budget_line_item_to_dict(self):
        line_item = BudgetLineItem(self.budget, 100000)
        result = line_item.to_dict()

        self.assertEqual(result["id"], self.budget.id)
        self.assertEqual(result["category"], "Rent")
        self.assertEqual(result["expected"], Decimal("1500.00"))
        self.assertEqual(result["actual"], Decimal("1000.00"))
        self.assertEqual(result["remaining"], Decimal("500.00"))


class CalculateActualSpentForBudgetTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.budget = Budget.objects.create(
            user=self.user,
            type=TransactionType.NEED.value,
            category="Rent",
            amount_in_cents=150000,
            budget_year=2025,
            budget_month=10,
        )

    def test_returns_zero_when_no_transactions(self):
        transactions = Transaction.objects.filter(user=self.user)
        result = calculate_actual_spent_for_budget(self.budget, transactions)
        self.assertEqual(result, 0)

    def test_sums_matching_transactions(self):
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.NEED.value,
            category="Rent",
            amount_in_cents=75000,
            date_of_expense="2025-10-01",
        )
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.NEED.value,
            category="Rent",
            amount_in_cents=75000,
            date_of_expense="2025-10-15",
        )

        transactions = Transaction.objects.filter(user=self.user)
        result = calculate_actual_spent_for_budget(self.budget, transactions)
        self.assertEqual(result, 150000)

    def test_excludes_non_matching_transactions(self):
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.NEED.value,
            category="Rent",
            amount_in_cents=75000,
            date_of_expense="2025-10-01",
        )
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.NEED.value,
            category="Groceries",
            amount_in_cents=5000,
            date_of_expense="2025-10-01",
        )

        transactions = Transaction.objects.filter(user=self.user)
        result = calculate_actual_spent_for_budget(self.budget, transactions)
        self.assertEqual(result, 75000)


class CreateBudgetLineItemsForTypeTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

    def test_returns_empty_list_when_no_budgets(self):
        budgets = Budget.objects.filter(user=self.user)
        transactions = Transaction.objects.filter(user=self.user)

        result = create_budget_line_items_for_type(
            TransactionType.INCOME, budgets, transactions
        )

        self.assertEqual(result, [])

    def test_creates_line_items_for_type(self):
        Budget.objects.create(
            user=self.user,
            type=TransactionType.INCOME.value,
            category="Salary",
            amount_in_cents=500000,
            budget_year=2025,
            budget_month=10,
        )
        Budget.objects.create(
            user=self.user,
            type=TransactionType.INCOME.value,
            category="Freelance",
            amount_in_cents=100000,
            budget_year=2025,
            budget_month=10,
        )

        budgets = Budget.objects.filter(user=self.user)
        transactions = Transaction.objects.filter(user=self.user)

        result = create_budget_line_items_for_type(
            TransactionType.INCOME, budgets, transactions
        )

        self.assertEqual(len(result), 2)

    def test_filters_by_transaction_type(self):
        Budget.objects.create(
            user=self.user,
            type=TransactionType.INCOME.value,
            category="Salary",
            amount_in_cents=500000,
            budget_year=2025,
            budget_month=10,
        )
        Budget.objects.create(
            user=self.user,
            type=TransactionType.NEED.value,
            category="Rent",
            amount_in_cents=150000,
            budget_year=2025,
            budget_month=10,
        )

        budgets = Budget.objects.filter(user=self.user)
        transactions = Transaction.objects.filter(user=self.user)

        result = create_budget_line_items_for_type(
            TransactionType.INCOME, budgets, transactions
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["category"], "Salary")


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
            type=TransactionType.INCOME.value,
            category="Salary",
            amount_in_cents=500000,
            budget_year=2025,
            budget_month=10,
        )
        Budget.objects.create(
            user=self.user,
            type=TransactionType.NEED.value,
            category="Rent",
            amount_in_cents=150000,
            budget_year=2025,
            budget_month=10,
        )
        Budget.objects.create(
            user=self.user,
            type=TransactionType.NEED.value,
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
            type=TransactionType.NEED.value,
            category="Rent",
            amount_in_cents=150000,
            budget_year=2025,
            budget_month=10,
        )
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.NEED.value,
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
