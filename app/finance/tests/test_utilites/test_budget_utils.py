import unittest
from decimal import Decimal
from datetime import datetime, date
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth.models import User

from finance.models import Budget, BudgetAllocation, Category, Transaction, Account
from finance.utilities.budget_utils import (
    validate_zero_based_allocation,
    get_user_previous_allocations,
    calculate_category_spending,
    get_budget_summary,
    get_unallocated_amount,
    get_expense_categories
)


class ValidateZeroBasedAllocationTest(TestCase):
    def test_exact_match(self):
        """Test that allocations exactly matching total income return True"""
        allocations = {'1': 500.00, '2': 1000.00, '3': 1500.00}
        self.assertTrue(validate_zero_based_allocation(allocations, 3000.00))

    def test_small_difference(self):
        """Test that allocations with tiny floating point differences return True"""
        # Due to floating point precision, 1000.00 + 2000.00 might be 2999.999999999
        allocations = {'1': 1000.00, '2': 2000.00}
        self.assertTrue(validate_zero_based_allocation(allocations, 3000.00))

    def test_mismatch(self):
        """Test that allocations not matching total income return False"""
        allocations = {'1': 500.00, '2': 1000.00}
        self.assertFalse(validate_zero_based_allocation(allocations, 2000.00))


class BudgetUtilsWithDBTest(TestCase):
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass'
        )

        # Create test account
        self.account = Account.objects.create(
            owner=self.user,
            name='Test Account',
            starting_balance=10000.00
        )

        # Create test categories
        self.housing_category = Category.objects.create(
            name='Housing',
            category_type='expense'
        )
        self.food_category = Category.objects.create(
            name='Food',
            category_type='expense'
        )
        self.salary_category = Category.objects.create(
            name='Salary',
            category_type='income'
        )

        # Create test budgets for two months
        self.january_budget = Budget.objects.create(
            user=self.user,
            month=date(2025, 1, 1),
            total_income=5000.00,
            is_active=True
        )

        self.february_budget = Budget.objects.create(
            user=self.user,
            month=date(2025, 2, 1),
            total_income=5200.00,
            is_active=True
        )

        # Create allocations for January
        self.housing_allocation_jan = BudgetAllocation.objects.create(
            budget=self.january_budget,
            category=self.housing_category,
            allocated_amount=2000.00
        )

        self.food_allocation_jan = BudgetAllocation.objects.create(
            budget=self.january_budget,
            category=self.food_category,
            allocated_amount=1000.00
        )

        # Create allocations for February with rollovers
        self.housing_allocation_feb = BudgetAllocation.objects.create(
            budget=self.february_budget,
            category=self.housing_category,
            allocated_amount=2000.00,
            rollover_from_previous=200.00
        )

        self.food_allocation_feb = BudgetAllocation.objects.create(
            budget=self.february_budget,
            category=self.food_category,
            allocated_amount=1000.00,
            rollover_from_previous=100.00
        )

        # Create transactions
        self.housing_transaction = Transaction.objects.create(
            account=self.account,
            category=self.housing_category,
            amount=1800.00,
            transaction_date=date(2025, 1, 15)
        )

        self.food_transaction = Transaction.objects.create(
            account=self.account,
            category=self.food_category,
            amount=950.00,
            transaction_date=date(2025, 1, 20)
        )

        self.salary_transaction = Transaction.objects.create(
            account=self.account,
            category=self.salary_category,
            amount=5000.00,
            transaction_date=date(2025, 1, 1)
        )

    def test_get_user_previous_allocations(self):
        """Test retrieving a user's previous budget allocations"""
        # Get March allocations, should return February's
        march_date = date(2025, 3, 1)
        prev_allocations = get_user_previous_allocations(self.user, march_date)

        # Should have two categories from February's budget
        self.assertEqual(len(prev_allocations), 2)
        self.assertEqual(prev_allocations[self.housing_category.id], 2000.00)
        self.assertEqual(prev_allocations[self.food_category.id], 1000.00)

    def test_calculate_category_spending(self):
        """Test calculating how much was spent in a category"""
        spent = calculate_category_spending(self.january_budget, self.housing_category)
        self.assertEqual(spent, 1800.00)

        spent = calculate_category_spending(self.january_budget, self.food_category)
        self.assertEqual(spent, 950.00)

    def test_get_budget_summary(self):
        """Test getting summary information for a budget"""
        summary = get_budget_summary(self.january_budget)

        # Check summary calculations
        self.assertEqual(summary['total_income'], 5000.00)
        self.assertEqual(summary['total_allocated'], 3000.00)  # 2000 + 1000
        self.assertEqual(summary['total_rollover'], 0.00)
        self.assertEqual(summary['total_spent'], 2750.00)  # 1800 + 950

        # Check February with rollovers
        summary = get_budget_summary(self.february_budget)
        self.assertEqual(summary['total_rollover'], 300.00)  # 200 + 100

    def test_get_unallocated_amount(self):
        """Test getting the unallocated amount in a budget"""
        unallocated = get_unallocated_amount(self.january_budget)
        self.assertEqual(unallocated, 2000.00)  # 5000 - (2000 + 1000)

    def test_get_expense_categories(self):
        """Test getting expense categories used by a user"""
        # Should return two expense categories
        categories = get_expense_categories(self.user)
        self.assertEqual(len(categories), 2)

        # Categories should be expense type only
        for category in categories:
            self.assertEqual(category.category_type, 'expense')

        # Should include our test categories
        category_names = [c.name for c in categories]
        self.assertIn('Housing', category_names)
        self.assertIn('Food', category_names)
