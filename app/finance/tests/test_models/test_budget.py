from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from finance.models import Budget
from finance.enums import TransactionType
from django.db.utils import IntegrityError
from django.utils import timezone


class BudgetModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.budget = Budget.from_dollars(
            dollar_amount=1000.00,
            user=self.user,
            type=TransactionType.NEED.name,
            category="Housing",
            budget_year=2025,
            budget_month=9,
        )

    def test_budget_creation(self):
        self.assertEqual(self.budget.amount_in_cents, 100000)
        self.assertEqual(self.budget.amount_dollars, 1000.00)
        self.assertEqual(self.budget.type, TransactionType.NEED.name)
        self.assertEqual(self.budget.category, "Housing")
        self.assertEqual(self.budget.budget_year, 2025)
        self.assertEqual(self.budget.budget_month, 9)
        self.assertGreaterEqual(self.budget.amount_in_cents, 0)

    def test_budget_creation_with_year_month(self):
        budget = Budget.from_dollars(
            dollar_amount=500.00,
            user=self.user,
            type=TransactionType.WANT.name,
            category="Entertainment",
            budget_year=2025,
            budget_month=10,
        )
        budget.save()
        self.assertEqual(budget.budget_year, 2025)
        self.assertEqual(budget.budget_month, 10)

    def test_string_representation(self):
        expected_string = (
            f"Budget: Housing - $1000.00 ({TransactionType.NEED.name}) - 2025/09"
        )
        self.assertEqual(str(self.budget), expected_string)

    def test_ordering(self):
        self.budget.save()

        budget2 = Budget.from_dollars(
            dollar_amount=500.00,
            user=self.user,
            type=TransactionType.WANT.name,
            category="Entertainment",
            budget_year=2025,
            budget_month=10,
        )
        budget2.save()

        budgets = Budget.objects.all()
        self.assertEqual(len(budgets), 2)
        self.assertEqual(budgets[0], budget2)
        self.assertEqual(budgets[1], self.budget)

    def test_invalid_month_validation(self):
        invalid_budget = Budget.from_dollars(
            dollar_amount=100.00,
            user=self.user,
            type=TransactionType.NEED.name,
            category="Test",
            budget_year=2025,
            budget_month=13,
        )
        with self.assertRaises(ValidationError):
            invalid_budget.full_clean()

        invalid_budget2 = Budget.from_dollars(
            dollar_amount=100.00,
            user=self.user,
            type=TransactionType.NEED.name,
            category="Test",
            budget_year=2025,
            budget_month=0,
        )
        with self.assertRaises(ValidationError):
            invalid_budget2.full_clean()

    def test_unique_constraint(self):
        self.budget.save()

        duplicate_budget = Budget.from_dollars(
            dollar_amount=1500.00,
            user=self.user,
            type=TransactionType.NEED.name,
            category="Housing",
            budget_year=2025,
            budget_month=9,
        )
        with self.assertRaises(IntegrityError):
            duplicate_budget.save()

    def test_query_by_year_and_month(self):
        Budget.from_dollars(
            dollar_amount=1000.00,
            user=self.user,
            type=TransactionType.NEED.name,
            category="Housing",
            budget_year=2025,
            budget_month=9,
        ).save()

        Budget.from_dollars(
            dollar_amount=500.00,
            user=self.user,
            type=TransactionType.WANT.name,
            category="Entertainment",
            budget_year=2025,
            budget_month=10,
        ).save()

        Budget.from_dollars(
            dollar_amount=300.00,
            user=self.user,
            type=TransactionType.NEED.name,
            category="Groceries",
            budget_year=2024,
            budget_month=9,
        ).save()

        september_2025_budgets = Budget.objects.filter(
            user=self.user, budget_year=2025, budget_month=9
        )
        self.assertEqual(september_2025_budgets.count(), 1)
        self.assertEqual(september_2025_budgets.first().category, "Housing")

        october_2025_budgets = Budget.objects.filter(
            user=self.user, budget_year=2025, budget_month=10
        )
        self.assertEqual(october_2025_budgets.count(), 1)
        self.assertEqual(october_2025_budgets.first().category, "Entertainment")
