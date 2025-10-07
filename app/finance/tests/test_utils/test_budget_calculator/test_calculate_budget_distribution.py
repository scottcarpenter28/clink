from decimal import Decimal

from django.test import TestCase
from django.contrib.auth.models import User

from finance.models import Budget
from finance.enums.transaction_enums import TransactionType
from finance.utils.budget_calculator import calculate_budget_distribution


class CalculateBudgetDistributionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

    def test_all_budget_types_present(self):
        Budget.objects.create(
            user=self.user,
            type=TransactionType.NEED.name,
            category="Rent",
            amount_in_cents=100000,
            budget_year=2025,
            budget_month=10,
        )
        Budget.objects.create(
            user=self.user,
            type=TransactionType.WANT.name,
            category="Entertainment",
            amount_in_cents=50000,
            budget_year=2025,
            budget_month=10,
        )
        Budget.objects.create(
            user=self.user,
            type=TransactionType.DEBTS.name,
            category="Credit Card",
            amount_in_cents=30000,
            budget_year=2025,
            budget_month=10,
        )
        Budget.objects.create(
            user=self.user,
            type=TransactionType.SAVINGS.name,
            category="Emergency Fund",
            amount_in_cents=20000,
            budget_year=2025,
            budget_month=10,
        )
        Budget.objects.create(
            user=self.user,
            type=TransactionType.INVESTING.name,
            category="401k",
            amount_in_cents=40000,
            budget_year=2025,
            budget_month=10,
        )

        budgets = Budget.objects.filter(user=self.user)
        result = calculate_budget_distribution(budgets)

        self.assertEqual(len(result), 5)
        self.assertEqual(result[TransactionType.NEED.value], Decimal("1000.00"))
        self.assertEqual(result[TransactionType.WANT.value], Decimal("500.00"))
        self.assertEqual(result[TransactionType.DEBTS.value], Decimal("300.00"))
        self.assertEqual(result[TransactionType.SAVINGS.value], Decimal("200.00"))
        self.assertEqual(result[TransactionType.INVESTING.value], Decimal("400.00"))

    def test_some_budget_types_missing(self):
        Budget.objects.create(
            user=self.user,
            type=TransactionType.NEED.name,
            category="Rent",
            amount_in_cents=100000,
            budget_year=2025,
            budget_month=10,
        )
        Budget.objects.create(
            user=self.user,
            type=TransactionType.SAVINGS.name,
            category="Emergency Fund",
            amount_in_cents=20000,
            budget_year=2025,
            budget_month=10,
        )

        budgets = Budget.objects.filter(user=self.user)
        result = calculate_budget_distribution(budgets)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[TransactionType.NEED.value], Decimal("1000.00"))
        self.assertEqual(result[TransactionType.SAVINGS.value], Decimal("200.00"))
        self.assertNotIn(TransactionType.WANT.value, result)
        self.assertNotIn(TransactionType.DEBTS.value, result)
        self.assertNotIn(TransactionType.INVESTING.value, result)

    def test_single_budget_type_only(self):
        Budget.objects.create(
            user=self.user,
            type=TransactionType.NEED.name,
            category="Rent",
            amount_in_cents=150000,
            budget_year=2025,
            budget_month=10,
        )

        budgets = Budget.objects.filter(user=self.user)
        result = calculate_budget_distribution(budgets)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[TransactionType.NEED.value], Decimal("1500.00"))

    def test_no_budgets_returns_empty_dict(self):
        budgets = Budget.objects.filter(user=self.user)
        result = calculate_budget_distribution(budgets)

        self.assertEqual(result, {})

    def test_excludes_income_type(self):
        Budget.objects.create(
            user=self.user,
            type=TransactionType.INCOME.name,
            category="Salary",
            amount_in_cents=200000,
            budget_year=2025,
            budget_month=10,
        )
        Budget.objects.create(
            user=self.user,
            type=TransactionType.NEED.name,
            category="Rent",
            amount_in_cents=100000,
            budget_year=2025,
            budget_month=10,
        )

        budgets = Budget.objects.filter(user=self.user)
        result = calculate_budget_distribution(budgets)

        self.assertEqual(len(result), 1)
        self.assertNotIn(TransactionType.INCOME.value, result)
        self.assertEqual(result[TransactionType.NEED.value], Decimal("1000.00"))

    def test_multiple_budgets_same_type_are_summed(self):
        Budget.objects.create(
            user=self.user,
            type=TransactionType.NEED.name,
            category="Rent",
            amount_in_cents=100000,
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
        Budget.objects.create(
            user=self.user,
            type=TransactionType.NEED.name,
            category="Utilities",
            amount_in_cents=30000,
            budget_year=2025,
            budget_month=10,
        )

        budgets = Budget.objects.filter(user=self.user)
        result = calculate_budget_distribution(budgets)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[TransactionType.NEED.value], Decimal("1800.00"))
