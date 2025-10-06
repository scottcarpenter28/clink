from datetime import datetime
from decimal import Decimal

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

from finance.models import Budget, Transaction
from finance.enums.transaction_enums import TransactionType


class HomeViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.client.login(username="testuser", password="testpass123")

    def test_home_view_requires_authentication(self):
        self.client.logout()
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login"))

    def test_home_view_renders_successfully(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "home.html")

    def test_home_view_uses_current_year_and_month_by_default(self):
        response = self.client.get(reverse("home"))
        now = datetime.now()
        self.assertEqual(response.context["year"], now.year)
        self.assertEqual(response.context["month"], now.month)

    def test_home_view_accepts_year_and_month_parameters(self):
        response = self.client.get(
            reverse("home_with_date", kwargs={"year": 2024, "month": 5})
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["year"], 2024)
        self.assertEqual(response.context["month"], 5)

    def test_home_view_displays_monthly_totals(self):
        Budget.objects.create(
            user=self.user,
            type=TransactionType.INCOME.value,
            category="Salary",
            amount_in_cents=500000,
            budget_year=2025,
            budget_month=10,
        )

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
            category="Groceries",
            amount_in_cents=10000,
            date_of_expense="2025-10-02",
        )

        response = self.client.get(
            reverse("home_with_date", kwargs={"year": 2025, "month": 10})
        )

        self.assertEqual(response.context["total_income"], Decimal("5000.00"))
        self.assertEqual(response.context["total_spent"], Decimal("100.00"))
        self.assertEqual(response.context["total_saved"], Decimal("0.00"))

    def test_home_view_filters_data_by_user(self):
        other_user = User.objects.create_user(
            username="otheruser", password="testpass123"
        )

        Budget.objects.create(
            user=other_user,
            type=TransactionType.INCOME.value,
            category="Salary",
            amount_in_cents=100000,
            budget_year=2025,
            budget_month=10,
        )

        Transaction.objects.create(
            user=other_user,
            type=TransactionType.INCOME.value,
            category="Salary",
            amount_in_cents=100000,
            date_of_expense="2025-10-01",
        )

        response = self.client.get(
            reverse("home_with_date", kwargs={"year": 2025, "month": 10})
        )

        self.assertEqual(response.context["total_income"], Decimal("0.00"))
        self.assertEqual(
            len(response.context["budget_data"][TransactionType.INCOME.value]), 0
        )

    def test_home_view_groups_budgets_by_type(self):
        Budget.objects.create(
            user=self.user,
            type=TransactionType.INCOME.value,
            category="Salary",
            amount_in_cents=500000,
            budget_year=2025,
            budget_month=10,
        )

        Budget.objects.create(
            user=self.user,
            type=TransactionType.NEED.value,
            category="Rent",
            amount_in_cents=150000,
            budget_year=2025,
            budget_month=10,
        )

        response = self.client.get(
            reverse("home_with_date", kwargs={"year": 2025, "month": 10})
        )
        budget_data = response.context["budget_data"]

        self.assertEqual(len(budget_data[TransactionType.INCOME.value]), 1)
        self.assertEqual(len(budget_data[TransactionType.NEED.value]), 1)
        self.assertEqual(len(budget_data[TransactionType.WANT.value]), 0)

    def test_future_transactions_not_shown_in_current_month(self):
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.NEED.value,
            category="Groceries",
            amount_in_cents=10000,
            date_of_expense="2025-10-15",
        )

        Transaction.objects.create(
            user=self.user,
            type=TransactionType.WANT.value,
            category="Entertainment",
            amount_in_cents=5000,
            date_of_expense="2025-11-20",
        )

        response = self.client.get(
            reverse("home_with_date", kwargs={"year": 2025, "month": 10})
        )

        self.assertEqual(response.context["total_spent"], Decimal("100.00"))

        future_response = self.client.get(
            reverse("home_with_date", kwargs={"year": 2025, "month": 11})
        )

        self.assertEqual(future_response.context["total_spent"], Decimal("50.00"))
