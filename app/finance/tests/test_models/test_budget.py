from django.test import TestCase
from django.contrib.auth.models import User
from datetime import datetime

from finance.models import Budget, BudgetAllocation, Category


class BudgetModelTest(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword'
        )

        # Create test categories
        self.expense_category1 = Category.objects.create(
            name='Housing',
            category_type='expense'
        )
        self.expense_category2 = Category.objects.create(
            name='Food',
            category_type='expense'
        )
        self.income_category = Category.objects.create(
            name='Salary',
            category_type='income'
        )

        # Create a test budget
        self.budget = Budget.objects.create(
            user=self.user,
            month=datetime(2025, 1, 1).date(),
            total_income=5000.0,
            is_active=True
        )

        # Create budget allocations
        self.allocation1 = BudgetAllocation.objects.create(
            budget=self.budget,
            category=self.expense_category1,
            allocated_amount=2000.0
        )

        self.allocation2 = BudgetAllocation.objects.create(
            budget=self.budget,
            category=self.expense_category2,
            allocated_amount=1000.0,
            rollover_from_previous=500.0
        )

    def test_budget_creation(self):
        """Test that a budget can be created with correct attributes."""
        self.assertEqual(self.budget.user, self.user)
        self.assertEqual(self.budget.month, datetime(2025, 1, 1).date())
        self.assertEqual(self.budget.total_income, 5000.0)
        self.assertTrue(self.budget.is_active)

    def test_budget_string_representation(self):
        """Test the string representation of the Budget model."""
        expected_string = f"Budget for January 2025 - {self.user.username}"
        self.assertEqual(str(self.budget), expected_string)

    def test_budget_allocation_creation(self):
        """Test that budget allocations can be created with correct attributes."""
        self.assertEqual(self.allocation1.budget, self.budget)
        self.assertEqual(self.allocation1.category, self.expense_category1)
        self.assertEqual(self.allocation1.allocated_amount, 2000.0)
        self.assertEqual(self.allocation1.rollover_from_previous, 0.0)  # Default

        self.assertEqual(self.allocation2.budget, self.budget)
        self.assertEqual(self.allocation2.category, self.expense_category2)
        self.assertEqual(self.allocation2.allocated_amount, 1000.0)
        self.assertEqual(self.allocation2.rollover_from_previous, 500.0)

    def test_budget_allocation_string_representation(self):
        """Test the string representation of the BudgetAllocation model."""
        expected_string = f"{self.expense_category1.name}: ${self.allocation1.allocated_amount} - {self.budget}"
        self.assertEqual(str(self.allocation1), expected_string)

    def test_budget_unique_constraint(self):
        """Test the unique constraint for user + month."""
        # Attempt to create a second budget for the same month and user
        with self.assertRaises(Exception):
            duplicate_budget = Budget.objects.create(
                user=self.user,
                month=datetime(2025, 1, 1).date(),
                total_income=6000.0
            )
