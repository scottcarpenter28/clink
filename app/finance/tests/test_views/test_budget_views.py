from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
import json

from finance.models import Budget
from finance.enums.transaction_enums import TransactionType


class BudgetCRUDTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.client.login(username="testuser", password="testpass123")

    def test_create_budget_requires_authentication(self):
        self.client.logout()
        response = self.client.post(reverse("create_budget"), {})
        self.assertEqual(response.status_code, 302)

    def test_create_budget_successfully(self):
        data = {
            "type": TransactionType.INCOME.name,
            "category": "Salary",
            "amount": "5000.00",
            "year": "2025",
            "month": "10",
        }

        response = self.client.post(reverse("create_budget"), data)
        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.content)
        self.assertTrue(response_data["success"])
        self.assertIn("budget_id", response_data)

        budget = Budget.objects.get(id=response_data["budget_id"])
        self.assertEqual(budget.user, self.user)
        self.assertEqual(budget.category, "Salary")
        self.assertEqual(budget.amount_in_cents, 500000)

    def test_create_budget_with_invalid_data(self):
        data = {
            "type": TransactionType.INCOME.name,
            "category": "Salary",
            "amount": "-100.00",
            "year": "2025",
            "month": "10",
        }

        response = self.client.post(reverse("create_budget"), data)
        self.assertEqual(response.status_code, 400)

        response_data = json.loads(response.content)
        self.assertFalse(response_data["success"])
        self.assertIn("errors", response_data)

    def test_create_budget_updates_existing_budget(self):
        Budget.objects.create(
            user=self.user,
            type=TransactionType.INCOME.value,
            category="Salary",
            amount_in_cents=400000,
            budget_year=2025,
            budget_month=10,
        )

        data = {
            "type": TransactionType.INCOME.name,
            "category": "Salary",
            "amount": "5000.00",
            "year": "2025",
            "month": "10",
        }

        response = self.client.post(reverse("create_budget"), data)
        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.content)
        self.assertFalse(response_data["created"])

        budget = Budget.objects.get(
            user=self.user,
            category="Salary",
            type=TransactionType.INCOME.value,
            budget_year=2025,
            budget_month=10,
        )
        self.assertEqual(budget.amount_in_cents, 500000)

    def test_update_budget_requires_authentication(self):
        budget = Budget.objects.create(
            user=self.user,
            type=TransactionType.INCOME.value,
            category="Salary",
            amount_in_cents=500000,
            budget_year=2025,
            budget_month=10,
        )

        self.client.logout()
        response = self.client.post(
            reverse("update_budget", kwargs={"budget_id": budget.id}), {}
        )
        self.assertEqual(response.status_code, 302)

    def test_update_budget_successfully(self):
        budget = Budget.objects.create(
            user=self.user,
            type=TransactionType.INCOME.value,
            category="Salary",
            amount_in_cents=500000,
            budget_year=2025,
            budget_month=10,
        )

        data = {
            "type": TransactionType.INCOME.name,
            "category": "Updated Salary",
            "amount": "6000.00",
        }

        response = self.client.post(
            reverse("update_budget", kwargs={"budget_id": budget.id}), data
        )
        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.content)
        self.assertTrue(response_data["success"])

        budget.refresh_from_db()
        self.assertEqual(budget.category, "Updated Salary")
        self.assertEqual(budget.amount_in_cents, 600000)

    def test_update_budget_prevents_access_to_other_users_budget(self):
        other_user = User.objects.create_user(
            username="otheruser", password="testpass123"
        )
        budget = Budget.objects.create(
            user=other_user,
            type=TransactionType.INCOME.value,
            category="Salary",
            amount_in_cents=500000,
            budget_year=2025,
            budget_month=10,
        )

        data = {
            "type": TransactionType.INCOME.name,
            "category": "Hacked",
            "amount": "1000.00",
        }

        response = self.client.post(
            reverse("update_budget", kwargs={"budget_id": budget.id}), data
        )
        self.assertEqual(response.status_code, 404)

    def test_delete_budget_requires_authentication(self):
        budget = Budget.objects.create(
            user=self.user,
            type=TransactionType.INCOME.value,
            category="Salary",
            amount_in_cents=500000,
            budget_year=2025,
            budget_month=10,
        )

        self.client.logout()
        response = self.client.post(
            reverse("delete_budget", kwargs={"budget_id": budget.id})
        )
        self.assertEqual(response.status_code, 302)

    def test_delete_budget_successfully(self):
        budget = Budget.objects.create(
            user=self.user,
            type=TransactionType.INCOME.value,
            category="Salary",
            amount_in_cents=500000,
            budget_year=2025,
            budget_month=10,
        )

        response = self.client.post(
            reverse("delete_budget", kwargs={"budget_id": budget.id})
        )
        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.content)
        self.assertTrue(response_data["success"])

        self.assertFalse(Budget.objects.filter(id=budget.id).exists())

    def test_delete_budget_prevents_access_to_other_users_budget(self):
        other_user = User.objects.create_user(
            username="otheruser", password="testpass123"
        )
        budget = Budget.objects.create(
            user=other_user,
            type=TransactionType.INCOME.value,
            category="Salary",
            amount_in_cents=500000,
            budget_year=2025,
            budget_month=10,
        )

        response = self.client.post(
            reverse("delete_budget", kwargs={"budget_id": budget.id})
        )
        self.assertEqual(response.status_code, 404)

        self.assertTrue(Budget.objects.filter(id=budget.id).exists())
