from datetime import date, timedelta

from django.test import TestCase
from django.contrib.auth.models import User

from finance.forms import TransactionForm
from finance.models import Transaction
from finance.enums import TransactionType


class TransactionFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

    def test_valid_transaction_form(self):
        data = {
            "type": TransactionType.NEED.name,
            "category": "Groceries",
            "amount": "45.99",
            "date_of_expense": date.today(),
        }
        form = TransactionForm(data=data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["type"], TransactionType.NEED.name)
        self.assertEqual(form.cleaned_data["category"], "Groceries")
        self.assertEqual(float(form.cleaned_data["amount"]), 45.99)
        self.assertEqual(form.cleaned_data["date_of_expense"], date.today())

    def test_negative_amount_fails(self):
        data = {
            "type": TransactionType.NEED.name,
            "category": "Groceries",
            "amount": "-10.00",
            "date_of_expense": date.today(),
        }
        form = TransactionForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("amount", form.errors)

    def test_zero_amount_fails(self):
        data = {
            "type": TransactionType.NEED.name,
            "category": "Groceries",
            "amount": "0.00",
            "date_of_expense": date.today(),
        }
        form = TransactionForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("amount", form.errors)

    def test_invalid_amount_format(self):
        data = {
            "type": TransactionType.NEED.name,
            "category": "Groceries",
            "amount": "invalid",
            "date_of_expense": date.today(),
        }
        form = TransactionForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("amount", form.errors)

    def test_invalid_type(self):
        data = {
            "type": "INVALID_TYPE",
            "category": "Groceries",
            "amount": "10.00",
            "date_of_expense": date.today(),
        }
        form = TransactionForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("type", form.errors)

    def test_missing_required_fields(self):
        data = {}
        form = TransactionForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("type", form.errors)
        self.assertIn("category", form.errors)
        self.assertIn("amount", form.errors)
        self.assertIn("date_of_expense", form.errors)

    def test_category_max_length(self):
        data = {
            "type": TransactionType.NEED.name,
            "category": "A" * 101,
            "amount": "10.00",
            "date_of_expense": date.today(),
        }
        form = TransactionForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("category", form.errors)

    def test_future_date_valid(self):
        future_date = date.today() + timedelta(days=30)
        data = {
            "type": TransactionType.NEED.name,
            "category": "Groceries",
            "amount": "10.00",
            "date_of_expense": future_date,
        }
        form = TransactionForm(data=data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["date_of_expense"], future_date)

    def test_past_date_valid(self):
        past_date = date.today() - timedelta(days=7)
        data = {
            "type": TransactionType.NEED.name,
            "category": "Groceries",
            "amount": "10.00",
            "date_of_expense": past_date,
        }
        form = TransactionForm(data=data)
        self.assertTrue(form.is_valid())


class TransactionFormSaveTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

    def test_save_creates_transaction(self):
        data = {
            "type": TransactionType.NEED.name,
            "category": "Groceries",
            "amount": "45.99",
            "date_of_expense": date.today(),
        }
        form = TransactionForm(data=data)
        self.assertTrue(form.is_valid())

        transaction = form.save(commit=False)
        transaction.user = self.user
        transaction.save()

        self.assertEqual(Transaction.objects.filter(user=self.user).count(), 1)
        saved_transaction = Transaction.objects.get(user=self.user)
        self.assertEqual(saved_transaction.category, "Groceries")
        self.assertEqual(saved_transaction.type, TransactionType.NEED.name)
        self.assertEqual(saved_transaction.date_of_expense, date.today())

    def test_save_converts_dollars_to_cents_correctly(self):
        data = {
            "type": TransactionType.NEED.name,
            "category": "Groceries",
            "amount": "123.45",
            "date_of_expense": date.today(),
        }
        form = TransactionForm(data=data)
        self.assertTrue(form.is_valid())

        transaction = form.save(commit=False)
        transaction.user = self.user
        transaction.save()

        self.assertEqual(transaction.amount_in_cents, 12345)

    def test_save_associates_with_user(self):
        data = {
            "type": TransactionType.INCOME.name,
            "category": "Salary",
            "amount": "1500.00",
            "date_of_expense": date.today(),
        }
        form = TransactionForm(data=data)
        self.assertTrue(form.is_valid())

        transaction = form.save(commit=False)
        transaction.user = self.user
        transaction.save()

        self.assertEqual(transaction.user, self.user)
        self.assertEqual(Transaction.objects.filter(user=self.user).count(), 1)

    def test_save_returns_transaction_instance(self):
        data = {
            "type": TransactionType.WANT.name,
            "category": "Entertainment",
            "amount": "25.00",
            "date_of_expense": date.today(),
        }
        form = TransactionForm(data=data)
        self.assertTrue(form.is_valid())

        transaction = form.save(commit=False)
        transaction.user = self.user
        transaction.save()

        self.assertIsInstance(transaction, Transaction)

    def test_saved_amount_matches_input(self):
        data = {
            "type": TransactionType.NEED.name,
            "category": "Utilities",
            "amount": "87.65",
            "date_of_expense": date.today(),
        }
        form = TransactionForm(data=data)
        self.assertTrue(form.is_valid())

        transaction = form.save(commit=False)
        transaction.user = self.user
        transaction.save()

        self.assertEqual(transaction.amount_dollars, 87.65)
