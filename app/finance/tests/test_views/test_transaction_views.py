from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
import json

from finance.models import Transaction
from finance.enums.transaction_enums import TransactionType


class TransactionCRUDTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.client.login(username="testuser", password="testpass123")

    def test_create_transaction_requires_authentication(self):
        self.client.logout()
        response = self.client.post(reverse("create_transaction"), {})
        self.assertEqual(response.status_code, 302)

    def test_create_transaction_successfully(self):
        data = {
            "type": TransactionType.INCOME.name,
            "category": "Salary",
            "amount": "5000.00",
            "date_of_expense": "2025-10-01",
        }

        response = self.client.post(reverse("create_transaction"), data)
        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.content)
        self.assertTrue(response_data["success"])
        self.assertIn("transaction_id", response_data)

        transaction = Transaction.objects.get(id=response_data["transaction_id"])
        self.assertEqual(transaction.user, self.user)
        self.assertEqual(transaction.category, "Salary")
        self.assertEqual(transaction.amount_in_cents, 500000)

    def test_create_transaction_with_invalid_data(self):
        data = {
            "type": TransactionType.INCOME.name,
            "category": "Salary",
            "amount": "-100.00",
            "date_of_expense": "2025-10-01",
        }

        response = self.client.post(reverse("create_transaction"), data)
        self.assertEqual(response.status_code, 400)

        response_data = json.loads(response.content)
        self.assertFalse(response_data["success"])
        self.assertIn("errors", response_data)

    def test_create_transaction_rejects_future_date(self):
        data = {
            "type": TransactionType.INCOME.name,
            "category": "Salary",
            "amount": "5000.00",
            "date_of_expense": "2099-12-31",
        }

        response = self.client.post(reverse("create_transaction"), data)
        self.assertEqual(response.status_code, 400)

        response_data = json.loads(response.content)
        self.assertFalse(response_data["success"])

    def test_update_transaction_requires_authentication(self):
        transaction = Transaction.objects.create(
            user=self.user,
            type=TransactionType.INCOME.value,
            category="Salary",
            amount_in_cents=500000,
            date_of_expense="2025-10-01",
        )

        self.client.logout()
        response = self.client.post(
            reverse("update_transaction", kwargs={"transaction_id": transaction.id}), {}
        )
        self.assertEqual(response.status_code, 302)

    def test_update_transaction_successfully(self):
        transaction = Transaction.objects.create(
            user=self.user,
            type=TransactionType.INCOME.value,
            category="Salary",
            amount_in_cents=500000,
            date_of_expense="2025-10-01",
        )

        data = {
            "type": TransactionType.INCOME.name,
            "category": "Updated Salary",
            "amount": "6000.00",
            "date_of_expense": "2025-10-02",
        }

        response = self.client.post(
            reverse("update_transaction", kwargs={"transaction_id": transaction.id}),
            data,
        )
        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.content)
        self.assertTrue(response_data["success"])

        transaction.refresh_from_db()
        self.assertEqual(transaction.category, "Updated Salary")
        self.assertEqual(transaction.amount_in_cents, 600000)
        self.assertEqual(str(transaction.date_of_expense), "2025-10-02")

    def test_update_transaction_prevents_access_to_other_users_transaction(self):
        other_user = User.objects.create_user(
            username="otheruser", password="testpass123"
        )
        transaction = Transaction.objects.create(
            user=other_user,
            type=TransactionType.INCOME.value,
            category="Salary",
            amount_in_cents=500000,
            date_of_expense="2025-10-01",
        )

        data = {
            "type": TransactionType.INCOME.name,
            "category": "Hacked",
            "amount": "1000.00",
            "date_of_expense": "2025-10-01",
        }

        response = self.client.post(
            reverse("update_transaction", kwargs={"transaction_id": transaction.id}),
            data,
        )
        self.assertEqual(response.status_code, 404)

    def test_delete_transaction_requires_authentication(self):
        transaction = Transaction.objects.create(
            user=self.user,
            type=TransactionType.INCOME.value,
            category="Salary",
            amount_in_cents=500000,
            date_of_expense="2025-10-01",
        )

        self.client.logout()
        response = self.client.post(
            reverse("delete_transaction", kwargs={"transaction_id": transaction.id})
        )
        self.assertEqual(response.status_code, 302)

    def test_delete_transaction_successfully(self):
        transaction = Transaction.objects.create(
            user=self.user,
            type=TransactionType.INCOME.value,
            category="Salary",
            amount_in_cents=500000,
            date_of_expense="2025-10-01",
        )

        response = self.client.post(
            reverse("delete_transaction", kwargs={"transaction_id": transaction.id})
        )
        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.content)
        self.assertTrue(response_data["success"])

        self.assertFalse(Transaction.objects.filter(id=transaction.id).exists())

    def test_delete_transaction_prevents_access_to_other_users_transaction(self):
        other_user = User.objects.create_user(
            username="otheruser", password="testpass123"
        )
        transaction = Transaction.objects.create(
            user=other_user,
            type=TransactionType.INCOME.value,
            category="Salary",
            amount_in_cents=500000,
            date_of_expense="2025-10-01",
        )

        response = self.client.post(
            reverse("delete_transaction", kwargs={"transaction_id": transaction.id})
        )
        self.assertEqual(response.status_code, 404)

        self.assertTrue(Transaction.objects.filter(id=transaction.id).exists())
