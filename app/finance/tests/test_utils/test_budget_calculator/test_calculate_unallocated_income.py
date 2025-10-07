from decimal import Decimal

from django.test import TestCase
from django.contrib.auth.models import User

from finance.models import Budget
from finance.enums.transaction_enums import TransactionType
from finance.utils.budget_calculator import calculate_unallocated_income


class CalculateUnallocatedIncomeTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

    def test_normal_scenario_with_partial_allocation(self):
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
        Budget.objects.create(
            user=self.user,
            type=TransactionType.WANT.name,
            category="Entertainment",
            amount_in_cents=50000,
            budget_year=2025,
            budget_month=10,
        )

        budgets = Budget.objects.filter(user=self.user)

        result = calculate_unallocated_income(budgets)

        self.assertEqual(result["total_income"], Decimal("2000.00"))
        self.assertEqual(result["total_allocated"], Decimal("1500.00"))
        self.assertEqual(result["unallocated"], Decimal("500.00"))
        self.assertEqual(result["percent_allocated"], 75.0)

    def test_fifty_percent_allocation(self):
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
            amount_in_cents=80000,
            budget_year=2025,
            budget_month=10,
        )
        Budget.objects.create(
            user=self.user,
            type=TransactionType.WANT.name,
            category="Entertainment",
            amount_in_cents=20000,
            budget_year=2025,
            budget_month=10,
        )

        budgets = Budget.objects.filter(user=self.user)

        result = calculate_unallocated_income(budgets)

        self.assertEqual(result["total_income"], Decimal("2000.00"))
        self.assertEqual(result["total_allocated"], Decimal("1000.00"))
        self.assertEqual(result["unallocated"], Decimal("1000.00"))
        self.assertEqual(result["percent_allocated"], 50.0)

    def test_over_allocated_budget(self):
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
            amount_in_cents=250000,
            budget_year=2025,
            budget_month=10,
        )

        budgets = Budget.objects.filter(user=self.user)

        result = calculate_unallocated_income(budgets)

        self.assertEqual(result["total_income"], Decimal("2000.00"))
        self.assertEqual(result["total_allocated"], Decimal("2500.00"))
        self.assertEqual(result["unallocated"], Decimal("-500.00"))
        self.assertEqual(result["percent_allocated"], 125.0)

    def test_no_budgets_allocated(self):
        Budget.objects.create(
            user=self.user,
            type=TransactionType.INCOME.name,
            category="Salary",
            amount_in_cents=200000,
            budget_year=2025,
            budget_month=10,
        )

        budgets = Budget.objects.filter(user=self.user)

        result = calculate_unallocated_income(budgets)

        self.assertEqual(result["total_income"], Decimal("2000.00"))
        self.assertEqual(result["total_allocated"], Decimal("0.00"))
        self.assertEqual(result["unallocated"], Decimal("2000.00"))
        self.assertEqual(result["percent_allocated"], 0.0)

    def test_no_income_budget_exists(self):
        Budget.objects.create(
            user=self.user,
            type=TransactionType.NEED.name,
            category="Rent",
            amount_in_cents=100000,
            budget_year=2025,
            budget_month=10,
        )

        budgets = Budget.objects.filter(user=self.user)

        result = calculate_unallocated_income(budgets)

        self.assertEqual(result["total_income"], Decimal("0.00"))
        self.assertEqual(result["total_allocated"], Decimal("1000.00"))
        self.assertEqual(result["unallocated"], Decimal("-1000.00"))
        self.assertEqual(result["percent_allocated"], 0.0)

    def test_empty_budgets_queryset(self):
        budgets = Budget.objects.filter(user=self.user)

        result = calculate_unallocated_income(budgets)

        self.assertEqual(result["total_income"], Decimal("0.00"))
        self.assertEqual(result["total_allocated"], Decimal("0.00"))
        self.assertEqual(result["unallocated"], Decimal("0.00"))
        self.assertEqual(result["percent_allocated"], 0.0)

    def test_excludes_income_type_from_allocation(self):
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
            type=TransactionType.INCOME.name,
            category="Bonus",
            amount_in_cents=50000,
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

        result = calculate_unallocated_income(budgets)

        self.assertEqual(result["total_income"], Decimal("2500.00"))
        self.assertEqual(result["total_allocated"], Decimal("1000.00"))
        self.assertEqual(result["unallocated"], Decimal("1500.00"))
        self.assertEqual(result["percent_allocated"], 40.0)

    def test_all_budget_types_allocated(self):
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
            type=TransactionType.SAVINGS.name,
            category="Emergency Fund",
            amount_in_cents=100000,
            budget_year=2025,
            budget_month=10,
        )
        Budget.objects.create(
            user=self.user,
            type=TransactionType.INVESTING.name,
            category="401k",
            amount_in_cents=150000,
            budget_year=2025,
            budget_month=10,
        )
        Budget.objects.create(
            user=self.user,
            type=TransactionType.DEBTS.name,
            category="Student Loan",
            amount_in_cents=50000,
            budget_year=2025,
            budget_month=10,
        )

        budgets = Budget.objects.filter(user=self.user)

        result = calculate_unallocated_income(budgets)

        self.assertEqual(result["total_income"], Decimal("5000.00"))
        self.assertEqual(result["total_allocated"], Decimal("4500.00"))
        self.assertEqual(result["unallocated"], Decimal("500.00"))
        self.assertEqual(result["percent_allocated"], 90.0)
