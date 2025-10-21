from datetime import date

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
import json

from finance.models import Budget, InternalTransfer
from finance.enums.transaction_enums import TransactionType


class CreateInternalTransferTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.client.login(username="testuser", password="testpass123")

        self.source_budget = Budget.objects.create(
            user=self.user,
            type=TransactionType.SAVINGS.name,
            category="Emergency Fund",
            amount_in_cents=100000,
            budget_year=2025,
            budget_month=10,
            allow_carry_over=True,
        )

        self.dest_budget = Budget.objects.create(
            user=self.user,
            type=TransactionType.SAVINGS.name,
            category="Vacation",
            amount_in_cents=50000,
            budget_year=2025,
            budget_month=10,
            allow_carry_over=True,
        )

    def test_create_transfer_requires_authentication(self):
        self.client.logout()
        response = self.client.post(reverse("create_internal_transfer"), {})
        self.assertEqual(response.status_code, 302)

    def test_create_transfer_successfully(self):
        data = {
            "source_budget_id": self.source_budget.id,
            "destination_budget_id": self.dest_budget.id,
            "amount": "200.00",
            "transfer_date": "2025-10-15",
            "description": "Moving funds for trip",
        }

        response = self.client.post(reverse("create_internal_transfer"), data)
        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.content)
        self.assertTrue(response_data["success"])
        self.assertIn("transfer_id", response_data)
        self.assertEqual(response_data["source_budget_id"], self.source_budget.id)
        self.assertEqual(response_data["destination_budget_id"], self.dest_budget.id)

        transfer = InternalTransfer.objects.get(id=response_data["transfer_id"])
        self.assertEqual(transfer.user, self.user)
        self.assertEqual(transfer.amount_in_cents, 20000)
        self.assertEqual(transfer.description, "Moving funds for trip")

    def test_create_transfer_to_use_funds(self):
        data = {
            "source_budget_id": self.source_budget.id,
            "destination_budget_id": "",
            "amount": "150.00",
            "transfer_date": "2025-10-10",
            "description": "Using accumulated funds",
        }

        response = self.client.post(reverse("create_internal_transfer"), data)
        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.content)
        self.assertTrue(response_data["success"])
        self.assertIsNone(response_data["destination_budget_id"])

        transfer = InternalTransfer.objects.get(id=response_data["transfer_id"])
        self.assertIsNone(transfer.destination_budget)

    def test_create_transfer_from_income_budget_fails(self):
        income_budget = Budget.objects.create(
            user=self.user,
            type=TransactionType.INCOME.name,
            category="Salary",
            amount_in_cents=500000,
            budget_year=2025,
            budget_month=10,
        )

        data = {
            "source_budget_id": income_budget.id,
            "destination_budget_id": self.dest_budget.id,
            "amount": "100.00",
            "transfer_date": "2025-10-15",
        }

        response = self.client.post(reverse("create_internal_transfer"), data)
        self.assertEqual(response.status_code, 400)

        response_data = json.loads(response.content)
        self.assertFalse(response_data["success"])
        self.assertIn("errors", response_data)

    def test_create_transfer_with_negative_amount_fails(self):
        data = {
            "source_budget_id": self.source_budget.id,
            "destination_budget_id": self.dest_budget.id,
            "amount": "-50.00",
            "transfer_date": "2025-10-15",
        }

        response = self.client.post(reverse("create_internal_transfer"), data)
        self.assertEqual(response.status_code, 400)

        response_data = json.loads(response.content)
        self.assertFalse(response_data["success"])

    def test_create_transfer_with_same_source_and_destination_fails(self):
        data = {
            "source_budget_id": self.source_budget.id,
            "destination_budget_id": self.source_budget.id,
            "amount": "100.00",
            "transfer_date": "2025-10-15",
        }

        response = self.client.post(reverse("create_internal_transfer"), data)
        self.assertEqual(response.status_code, 400)

        response_data = json.loads(response.content)
        self.assertFalse(response_data["success"])

    def test_create_transfer_prevents_access_to_other_users_budget(self):
        other_user = User.objects.create_user(
            username="otheruser", password="testpass123"
        )
        other_budget = Budget.objects.create(
            user=other_user,
            type=TransactionType.SAVINGS.name,
            category="Other Savings",
            amount_in_cents=100000,
            budget_year=2025,
            budget_month=10,
        )

        data = {
            "source_budget_id": other_budget.id,
            "destination_budget_id": self.dest_budget.id,
            "amount": "100.00",
            "transfer_date": "2025-10-15",
        }

        response = self.client.post(reverse("create_internal_transfer"), data)
        self.assertEqual(response.status_code, 404)


class GetInternalTransfersTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.client.login(username="testuser", password="testpass123")

        self.budget1 = Budget.objects.create(
            user=self.user,
            type=TransactionType.SAVINGS.name,
            category="Emergency Fund",
            amount_in_cents=100000,
            budget_year=2025,
            budget_month=10,
        )

        self.budget2 = Budget.objects.create(
            user=self.user,
            type=TransactionType.SAVINGS.name,
            category="Vacation",
            amount_in_cents=50000,
            budget_year=2025,
            budget_month=10,
        )

        self.transfer1 = InternalTransfer.objects.create(
            user=self.user,
            source_budget=self.budget1,
            destination_budget=self.budget2,
            amount_in_cents=20000,
            transfer_date=date(2025, 10, 15),
            description="Transfer 1",
        )

        self.transfer2 = InternalTransfer.objects.create(
            user=self.user,
            source_budget=self.budget1,
            destination_budget=None,
            amount_in_cents=10000,
            transfer_date=date(2025, 10, 20),
            description="Transfer 2",
        )

    def test_get_transfers_requires_authentication(self):
        self.client.logout()
        response = self.client.get(
            reverse("get_internal_transfers"), {"budget_id": self.budget1.id}
        )
        self.assertEqual(response.status_code, 302)

    def test_get_transfers_by_budget_id(self):
        response = self.client.get(
            reverse("get_internal_transfers"), {"budget_id": self.budget1.id}
        )
        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.content)
        self.assertTrue(response_data["success"])
        self.assertEqual(len(response_data["transfers"]), 2)

    def test_get_transfers_by_year_and_month(self):
        response = self.client.get(
            reverse("get_internal_transfers"), {"year": 2025, "month": 10}
        )
        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.content)
        self.assertTrue(response_data["success"])
        self.assertEqual(len(response_data["transfers"]), 2)

    def test_get_transfers_returns_correct_structure(self):
        response = self.client.get(
            reverse("get_internal_transfers"), {"budget_id": self.budget1.id}
        )
        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.content)
        transfer = response_data["transfers"][1]

        self.assertIn("id", transfer)
        self.assertIn("source_budget_id", transfer)
        self.assertIn("source_category", transfer)
        self.assertIn("destination_budget_id", transfer)
        self.assertIn("destination_category", transfer)
        self.assertIn("amount", transfer)
        self.assertIn("transfer_date", transfer)
        self.assertIn("description", transfer)

        self.assertEqual(transfer["source_category"], "Emergency Fund")
        self.assertEqual(transfer["destination_category"], "Vacation")

    def test_get_transfers_shows_use_funds_correctly(self):
        response = self.client.get(
            reverse("get_internal_transfers"), {"budget_id": self.budget1.id}
        )
        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.content)
        use_funds_transfer = response_data["transfers"][0]

        self.assertEqual(use_funds_transfer["destination_category"], "Used Funds")
        self.assertIsNone(use_funds_transfer["destination_budget_id"])

    def test_get_transfers_requires_parameters(self):
        response = self.client.get(reverse("get_internal_transfers"))
        self.assertEqual(response.status_code, 400)

        response_data = json.loads(response.content)
        self.assertFalse(response_data["success"])
        self.assertIn("error", response_data)

    def test_get_transfers_only_returns_current_user_transfers(self):
        other_user = User.objects.create_user(
            username="otheruser", password="testpass123"
        )
        other_budget = Budget.objects.create(
            user=other_user,
            type=TransactionType.SAVINGS.name,
            category="Other Savings",
            amount_in_cents=100000,
            budget_year=2025,
            budget_month=10,
        )
        InternalTransfer.objects.create(
            user=other_user,
            source_budget=other_budget,
            destination_budget=None,
            amount_in_cents=50000,
            transfer_date=date(2025, 10, 15),
        )

        response = self.client.get(
            reverse("get_internal_transfers"), {"year": 2025, "month": 10}
        )
        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.content)
        self.assertEqual(len(response_data["transfers"]), 2)


class DeleteInternalTransferTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.client.login(username="testuser", password="testpass123")

        self.budget = Budget.objects.create(
            user=self.user,
            type=TransactionType.SAVINGS.name,
            category="Emergency Fund",
            amount_in_cents=100000,
            budget_year=2025,
            budget_month=10,
        )

        self.transfer = InternalTransfer.objects.create(
            user=self.user,
            source_budget=self.budget,
            destination_budget=None,
            amount_in_cents=20000,
            transfer_date=date(2025, 10, 15),
        )

    def test_delete_transfer_requires_authentication(self):
        self.client.logout()
        response = self.client.post(
            reverse(
                "delete_internal_transfer", kwargs={"transfer_id": self.transfer.id}
            )
        )
        self.assertEqual(response.status_code, 302)

    def test_delete_transfer_successfully(self):
        response = self.client.post(
            reverse(
                "delete_internal_transfer", kwargs={"transfer_id": self.transfer.id}
            )
        )
        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.content)
        self.assertTrue(response_data["success"])

        self.assertFalse(InternalTransfer.objects.filter(id=self.transfer.id).exists())

    def test_delete_transfer_prevents_access_to_other_users_transfer(self):
        other_user = User.objects.create_user(
            username="otheruser", password="testpass123"
        )
        other_budget = Budget.objects.create(
            user=other_user,
            type=TransactionType.SAVINGS.name,
            category="Other Savings",
            amount_in_cents=100000,
            budget_year=2025,
            budget_month=10,
        )
        other_transfer = InternalTransfer.objects.create(
            user=other_user,
            source_budget=other_budget,
            destination_budget=None,
            amount_in_cents=50000,
            transfer_date=date(2025, 10, 15),
        )

        response = self.client.post(
            reverse(
                "delete_internal_transfer", kwargs={"transfer_id": other_transfer.id}
            )
        )
        self.assertEqual(response.status_code, 404)

        self.assertTrue(InternalTransfer.objects.filter(id=other_transfer.id).exists())
