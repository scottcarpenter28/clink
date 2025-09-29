from django.test import TestCase
from django.contrib.auth.models import User
from finance.models import BaseFinancialModel, Transaction, Budget
from finance.enums import TransactionType


class BaseFinancialModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

    def test_amount_dollars_conversion(self):
        transaction = Transaction(
            user=self.user,
            type=TransactionType.NEED.name,
            category="Test Category",
            amount_in_cents=1250,
            date_of_expense="2023-01-01",
        )

        self.assertEqual(transaction.amount_dollars, 12.50)
        transaction.amount_in_cents = 0
        self.assertEqual(transaction.amount_dollars, 0.0)
        transaction.amount_in_cents = -2500
        self.assertEqual(transaction.amount_dollars, -25.0)

    def test_from_dollars_creation(self):
        transaction = Transaction.from_dollars(
            dollar_amount=24.99,
            user=self.user,
            type=TransactionType.WANT.name,
            category="Entertainment",
            date_of_expense="2023-02-15",
        )

        self.assertEqual(transaction.amount_in_cents, 2499)
        self.assertEqual(transaction.amount_dollars, 24.99)

        self.assertEqual(transaction.type, TransactionType.WANT.name)
        self.assertEqual(transaction.category, "Entertainment")
        self.assertEqual(str(transaction.date_of_expense), "2023-02-15")
