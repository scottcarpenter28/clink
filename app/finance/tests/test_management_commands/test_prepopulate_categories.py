from django.test import TestCase
from django.core.management import call_command
from django.core.management.base import CommandError
from io import StringIO

from finance.models.category import Category


class PrepopulateCategoriesCommandTest(TestCase):
    def setUp(self):
        Category.objects.all().delete()

    def test_command_creates_all_categories_on_empty_database(self):
        """Test that the command creates all 25 categories when database is empty."""
        initial_count = Category.objects.count()
        self.assertEqual(initial_count, 0)

        out = StringIO()
        call_command('prepopulate_categories', stdout=out)

        total_count = Category.objects.count()
        expense_count = Category.objects.filter(category_type='expense').count()
        income_count = Category.objects.filter(category_type='income').count()

        self.assertEqual(total_count, 25)
        self.assertEqual(expense_count, 17)
        self.assertEqual(income_count, 8)

        output = out.getvalue()
        self.assertIn('Summary: Processed 25 categories - 25 created, 0 skipped', output)

    def test_command_is_idempotent(self):
        """Test that running the command twice doesn't create duplicates."""
        out1 = StringIO()
        call_command('prepopulate_categories', stdout=out1)

        first_count = Category.objects.count()
        self.assertEqual(first_count, 25)

        out2 = StringIO()
        call_command('prepopulate_categories', stdout=out2)

        second_count = Category.objects.count()
        self.assertEqual(second_count, 25)  # Should be the same

        output2 = out2.getvalue()
        self.assertIn('Summary: Processed 25 categories - 0 created, 25 skipped', output2)

    def test_expense_categories_created_correctly(self):
        """Test that all expense categories are created with correct names and types."""
        expected_expense_categories = [
            'Groceries', 'Utilities', 'Rent/Mortgage', 'Subscriptions',
            'Health & Wellness', 'Travel', 'Transportation', 'Bills',
            'Dining Out', 'Entertainment', 'Clothing', 'Home Maintenance',
            'Insurance', 'Education', 'Personal Care', 'Gifts & Donations',
            'Miscellaneous'
        ]

        call_command('prepopulate_categories', stdout=StringIO())

        expense_categories = Category.objects.filter(category_type='expense')
        expense_names = list(expense_categories.values_list('name', flat=True))

        self.assertEqual(len(expense_categories), 17)
        for expected_name in expected_expense_categories:
            self.assertIn(expected_name, expense_names)

    def test_income_categories_created_correctly(self):
        """Test that all income categories are created with correct names and types."""
        expected_income_categories = [
            'Salary', 'Freelance/Side Income', 'Investment Returns',
            'Gifts Received', 'Tax Refunds', 'Emergency Fund',
            'Sinking Fund', 'Other Income'
        ]

        call_command('prepopulate_categories', stdout=StringIO())

        income_categories = Category.objects.filter(category_type='income')
        income_names = list(income_categories.values_list('name', flat=True))

        self.assertEqual(len(income_categories), 8)
        for expected_name in expected_income_categories:
            self.assertIn(expected_name, income_names)

    def test_command_with_existing_categories(self):
        """Test that the command handles existing categories correctly."""
        Category.objects.create(name='Groceries', category_type='expense')
        Category.objects.create(name='Salary', category_type='income')

        initial_count = Category.objects.count()
        self.assertEqual(initial_count, 2)

        out = StringIO()
        call_command('prepopulate_categories', stdout=out)

        final_count = Category.objects.count()
        self.assertEqual(final_count, 25)  # 2 existing + 23 new

        output = out.getvalue()
        self.assertIn('Summary: Processed 25 categories - 23 created, 2 skipped', output)
        self.assertIn('Expense category already exists: Groceries', output)
        self.assertIn('Income category already exists: Salary', output)

    def test_categories_have_proper_capitalization(self):
        """Test that categories are created with proper title case."""
        call_command('prepopulate_categories', stdout=StringIO())

        categories = Category.objects.all()

        for category in categories:
            words = category.name.split()
            for word in words:
                if word not in ['&', '/']:  # Skip connecting words
                    self.assertTrue(word[0].isupper(),
                                  f"Category '{category.name}' word '{word}' should start with capital letter")

    def test_command_help_text(self):
        """Test that the command has proper help text."""
        from finance.management.commands.prepopulate_categories import Command
        command = Command()
        self.assertEqual(command.help, 'Prepopulates the database with predefined expense and income categories')
