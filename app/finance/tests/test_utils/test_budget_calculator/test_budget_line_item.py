from decimal import Decimal

from django.test import TestCase
from django.contrib.auth.models import User

from finance.models import Budget
from finance.enums.transaction_enums import TransactionType
from finance.utils.budget_calculator import BudgetLineItem


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
