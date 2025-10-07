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
            type=TransactionType.INCOME.name,
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
            type=TransactionType.INCOME.name,
            budget_year=2025,
            budget_month=10,
        )
        self.assertEqual(budget.amount_in_cents, 500000)

    def test_update_budget_requires_authentication(self):
        budget = Budget.objects.create(
            user=self.user,
            type=TransactionType.INCOME.name,
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
            type=TransactionType.INCOME.name,
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
            type=TransactionType.INCOME.name,
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
            type=TransactionType.INCOME.name,
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
            type=TransactionType.INCOME.name,
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
            type=TransactionType.INCOME.name,
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


class BudgetCategoriesTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.client.login(username="testuser", password="testpass123")

    def test_get_budget_categories_requires_authentication(self):
        self.client.logout()
        response = self.client.get(
            reverse(
                "get_budget_categories",
                kwargs={"year": 2025, "month": 10, "type": "INCOME"},
            )
        )
        self.assertEqual(response.status_code, 302)

    def test_get_budget_categories_returns_categories_for_type(self):
        Budget.objects.create(
            user=self.user,
            type=TransactionType.INCOME.name,
            category="Salary",
            amount_in_cents=500000,
            budget_year=2025,
            budget_month=10,
        )
        Budget.objects.create(
            user=self.user,
            type=TransactionType.INCOME.name,
            category="Freelance",
            amount_in_cents=200000,
            budget_year=2025,
            budget_month=10,
        )
        Budget.objects.create(
            user=self.user,
            type=TransactionType.NEED.name,
            category="Rent",
            amount_in_cents=150000,
            budget_year=2025,
            budget_month=10,
        )

        response = self.client.get(
            reverse(
                "get_budget_categories",
                kwargs={"year": 2025, "month": 10, "type": "INCOME"},
            )
        )
        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.content)
        self.assertTrue(response_data["success"])
        self.assertEqual(len(response_data["categories"]), 2)
        self.assertIn("Salary", response_data["categories"])
        self.assertIn("Freelance", response_data["categories"])
        self.assertNotIn("Rent", response_data["categories"])

    def test_get_budget_categories_returns_distinct_categories(self):
        Budget.objects.create(
            user=self.user,
            type=TransactionType.NEED.name,
            category="Groceries",
            amount_in_cents=50000,
            budget_year=2025,
            budget_month=10,
        )

        response = self.client.get(
            reverse(
                "get_budget_categories",
                kwargs={"year": 2025, "month": 10, "type": "NEED"},
            )
        )
        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.content)
        self.assertTrue(response_data["success"])
        self.assertEqual(len(response_data["categories"]), 1)
        self.assertEqual(response_data["categories"][0], "Groceries")

    def test_get_budget_categories_returns_empty_list_when_no_budgets(self):
        response = self.client.get(
            reverse(
                "get_budget_categories",
                kwargs={"year": 2025, "month": 10, "type": "WANT"},
            )
        )
        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.content)
        self.assertTrue(response_data["success"])
        self.assertEqual(len(response_data["categories"]), 0)

    def test_get_budget_categories_filters_by_year_and_month(self):
        Budget.objects.create(
            user=self.user,
            type=TransactionType.SAVINGS.name,
            category="Emergency Fund",
            amount_in_cents=100000,
            budget_year=2025,
            budget_month=10,
        )
        Budget.objects.create(
            user=self.user,
            type=TransactionType.SAVINGS.name,
            category="Vacation",
            amount_in_cents=50000,
            budget_year=2025,
            budget_month=11,
        )

        response = self.client.get(
            reverse(
                "get_budget_categories",
                kwargs={"year": 2025, "month": 10, "type": "SAVINGS"},
            )
        )
        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.content)
        self.assertTrue(response_data["success"])
        self.assertEqual(len(response_data["categories"]), 1)
        self.assertEqual(response_data["categories"][0], "Emergency Fund")

    def test_get_budget_categories_invalid_type_returns_error(self):
        response = self.client.get(
            reverse(
                "get_budget_categories",
                kwargs={"year": 2025, "month": 10, "type": "INVALID"},
            )
        )
        self.assertEqual(response.status_code, 400)

        response_data = json.loads(response.content)
        self.assertFalse(response_data["success"])
        self.assertIn("error", response_data)

    def test_get_budget_categories_only_returns_current_user_budgets(self):
        other_user = User.objects.create_user(
            username="otheruser", password="testpass123"
        )
        Budget.objects.create(
            user=other_user,
            type=TransactionType.INCOME.name,
            category="Other Salary",
            amount_in_cents=500000,
            budget_year=2025,
            budget_month=10,
        )
        Budget.objects.create(
            user=self.user,
            type=TransactionType.INCOME.name,
            category="My Salary",
            amount_in_cents=500000,
            budget_year=2025,
            budget_month=10,
        )

        response = self.client.get(
            reverse(
                "get_budget_categories",
                kwargs={"year": 2025, "month": 10, "type": "INCOME"},
            )
        )
        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.content)
        self.assertTrue(response_data["success"])
        self.assertEqual(len(response_data["categories"]), 1)
        self.assertEqual(response_data["categories"][0], "My Salary")
