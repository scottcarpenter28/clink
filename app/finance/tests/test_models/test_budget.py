from django.test import TestCase
from django.contrib.auth.models import User
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
        )

    def test_budget_creation(self):
        self.assertEqual(self.budget.amount_in_cents, 100000)
        self.assertEqual(self.budget.amount_dollars, 1000.00)
        self.assertEqual(self.budget.type, TransactionType.NEED.name)
        self.assertEqual(self.budget.category, "Housing")
        self.assertGreaterEqual(self.budget.amount_in_cents, 0)

    def test_string_representation(self):
        expected_string = f"Budget: Housing - $1000.00 ({TransactionType.NEED.name})"
        self.assertEqual(str(self.budget), expected_string)

    def test_ordering(self):
        self.budget.save()

        budget2 = Budget.from_dollars(
            dollar_amount=500.00,
            user=self.user,
            type=TransactionType.WANT.name,
            category="Entertainment",
        )
        budget2.save()

        budgets = Budget.objects.all()
        self.assertEqual(len(budgets), 2)
        self.assertEqual(budgets[0], budget2)
        self.assertEqual(budgets[1], self.budget)
