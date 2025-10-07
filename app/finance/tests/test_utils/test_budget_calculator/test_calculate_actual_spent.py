from django.test import TestCase
from django.contrib.auth.models import User

from finance.models import Budget, Transaction
from finance.enums.transaction_enums import TransactionType
from finance.utils.budget_calculator import calculate_actual_spent_for_budget


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
