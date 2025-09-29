from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from finance.models import Transaction
from finance.enums import TransactionType
from datetime import date


class TransactionModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.today = date.today()
        self.transaction = Transaction.from_dollars(
            dollar_amount=42.50,
            user=self.user,
            type=TransactionType.NEED.name,
            category="Groceries",
            date_of_expense=self.today,
        )

    def test_transaction_creation(self):
        # Test basic instance creation
        self.assertEqual(self.transaction.amount_in_cents, 4250)
        self.assertEqual(self.transaction.amount_dollars, 42.50)
        self.assertEqual(self.transaction.type, TransactionType.NEED.name)
        self.assertEqual(self.transaction.category, "Groceries")
        self.assertEqual(self.transaction.date_of_expense, self.today)

    def test_string_representation(self):
        # Test string representation
        expected_string = f"Groceries - $42.50 ({self.today})"
        self.assertEqual(str(self.transaction), expected_string)

    def test_ordering(self):
        # Create transactions with different dates to test ordering
        yesterday = date.fromordinal(self.today.toordinal() - 1)
        tomorrow = date.fromordinal(self.today.toordinal() + 1)

        transaction_yesterday = Transaction.from_dollars(
            dollar_amount=10.00,
            user=self.user,
            type=TransactionType.WANT.name,
            category="Entertainment",
            date_of_expense=yesterday,
        )

        transaction_tomorrow = Transaction.from_dollars(
            dollar_amount=20.00,
            user=self.user,
            type=TransactionType.SAVINGS.name,
            category="Emergency Fund",
            date_of_expense=tomorrow,
        )

        # Save all transactions to test ordering
        transaction_yesterday.save()
        self.transaction.save()
        transaction_tomorrow.save()

        # Get all transactions and verify ordering (newest first)
        transactions = Transaction.objects.all()
        self.assertEqual(transactions[0].date_of_expense, tomorrow)
        self.assertEqual(transactions[1].date_of_expense, self.today)
        self.assertEqual(transactions[2].date_of_expense, yesterday)

    def test_positive_amounts_only(self):
        # Test that negative amounts get converted to positive
        transaction = Transaction.from_dollars(
            dollar_amount=-15.75,
            user=self.user,
            type=TransactionType.WANT.name,
            category="Dining Out",
            date_of_expense=self.today,
        )

        # Should convert negative to positive
        self.assertEqual(transaction.amount_in_cents, 1575)
        self.assertEqual(transaction.amount_dollars, 15.75)
        self.assertGreaterEqual(transaction.amount_in_cents, 0)
