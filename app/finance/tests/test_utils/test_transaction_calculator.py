from decimal import Decimal

from django.test import TestCase
from django.contrib.auth.models import User

from finance.models import Transaction
from finance.enums.transaction_enums import TransactionType
from finance.utils.transaction_calculator import (
    calculate_total_by_types,
    calculate_total_income,
    calculate_total_spent,
    calculate_total_saved,
)


class TransactionCalculatorTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

    def test_calculate_total_by_types_returns_zero_for_empty_queryset(self):
        transactions = Transaction.objects.filter(user=self.user)
        result = calculate_total_by_types(transactions, [TransactionType.INCOME])
        self.assertEqual(result, Decimal("0.00"))

    def test_calculate_total_by_types_sums_single_type(self):
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.INCOME.value,
            category="Salary",
            amount_in_cents=500000,
            date_of_expense="2025-10-01",
        )
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.INCOME.value,
            category="Bonus",
            amount_in_cents=100000,
            date_of_expense="2025-10-02",
        )

        transactions = Transaction.objects.filter(user=self.user)
        result = calculate_total_by_types(transactions, [TransactionType.INCOME])
        self.assertEqual(result, Decimal("6000.00"))

    def test_calculate_total_by_types_sums_multiple_types(self):
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.NEED.value,
            category="Rent",
            amount_in_cents=150000,
            date_of_expense="2025-10-01",
        )
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.WANT.value,
            category="Entertainment",
            amount_in_cents=5000,
            date_of_expense="2025-10-02",
        )
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.DEBTS.value,
            category="Credit Card",
            amount_in_cents=10000,
            date_of_expense="2025-10-03",
        )

        transactions = Transaction.objects.filter(user=self.user)
        result = calculate_total_by_types(
            transactions,
            [TransactionType.NEED, TransactionType.WANT, TransactionType.DEBTS],
        )
        self.assertEqual(result, Decimal("1650.00"))

    def test_calculate_total_income(self):
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.INCOME.value,
            category="Salary",
            amount_in_cents=500000,
            date_of_expense="2025-10-01",
        )

        transactions = Transaction.objects.filter(user=self.user)
        result = calculate_total_income(transactions)
        self.assertEqual(result, Decimal("5000.00"))

    def test_calculate_total_spent(self):
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.NEED.value,
            category="Rent",
            amount_in_cents=150000,
            date_of_expense="2025-10-01",
        )
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.WANT.value,
            category="Shopping",
            amount_in_cents=5000,
            date_of_expense="2025-10-02",
        )

        transactions = Transaction.objects.filter(user=self.user)
        result = calculate_total_spent(transactions)
        self.assertEqual(result, Decimal("1550.00"))

    def test_calculate_total_saved(self):
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.SAVINGS.value,
            category="Emergency Fund",
            amount_in_cents=50000,
            date_of_expense="2025-10-01",
        )
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.INVESTING.value,
            category="401k",
            amount_in_cents=30000,
            date_of_expense="2025-10-02",
        )

        transactions = Transaction.objects.filter(user=self.user)
        result = calculate_total_saved(transactions)
        self.assertEqual(result, Decimal("800.00"))

    def test_calculate_total_excludes_other_types(self):
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.INCOME.value,
            category="Salary",
            amount_in_cents=500000,
            date_of_expense="2025-10-01",
        )
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.NEED.value,
            category="Rent",
            amount_in_cents=150000,
            date_of_expense="2025-10-02",
        )

        transactions = Transaction.objects.filter(user=self.user)
        result = calculate_total_income(transactions)
        self.assertEqual(result, Decimal("5000.00"))
