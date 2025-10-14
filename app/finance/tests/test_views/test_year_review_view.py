from datetime import datetime
from decimal import Decimal

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

from finance.models import Budget, Transaction
from finance.enums.transaction_enums import TransactionType


class YearReviewViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.client.login(username="testuser", password="testpass123")

    def test_year_review_view_requires_authentication(self):
        self.client.logout()
        response = self.client.get(reverse("year_review"))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login"))

    def test_year_review_view_renders_successfully(self):
        response = self.client.get(reverse("year_review"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "year_review.html")

    def test_year_review_view_uses_current_year_by_default(self):
        response = self.client.get(reverse("year_review"))
        now = datetime.now()
        self.assertEqual(response.context["year"], now.year)

    def test_year_review_view_accepts_year_parameter(self):
        response = self.client.get(
            reverse("year_review_with_year", kwargs={"year": 2024})
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["year"], 2024)

    def test_year_review_view_includes_type_breakdown(self):
        response = self.client.get(reverse("year_review"))
        self.assertIn("type_breakdown", response.context)

        type_breakdown = response.context["type_breakdown"]
        expected_types = ["Income", "Need", "Want", "Debts", "Savings", "Investing"]

        for transaction_type in expected_types:
            self.assertIn(transaction_type, type_breakdown)
            self.assertEqual(len(type_breakdown[transaction_type]), 14)

    def test_year_review_view_includes_category_breakdowns(self):
        response = self.client.get(reverse("year_review"))
        self.assertIn("category_breakdowns", response.context)

        category_breakdowns = response.context["category_breakdowns"]
        expected_types = ["Need", "Want", "Debts", "Savings", "Investing"]

        for transaction_type in expected_types:
            self.assertIn(transaction_type, category_breakdowns)

    def test_year_review_view_aggregates_transactions_correctly(self):
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.INCOME.name,
            category="Salary",
            amount_in_cents=500000,
            date_of_expense="2025-01-15",
        )
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.INCOME.name,
            category="Salary",
            amount_in_cents=500000,
            date_of_expense="2025-06-15",
        )

        response = self.client.get(
            reverse("year_review_with_year", kwargs={"year": 2025})
        )

        type_breakdown = response.context["type_breakdown"]
        self.assertEqual(type_breakdown["Income"][0], Decimal("5000.00"))
        self.assertEqual(type_breakdown["Income"][5], Decimal("5000.00"))
        self.assertEqual(type_breakdown["Income"][12], Decimal("10000.00"))

    def test_year_review_view_filters_data_by_user(self):
        other_user = User.objects.create_user(
            username="otheruser", password="testpass123"
        )

        Transaction.objects.create(
            user=other_user,
            type=TransactionType.INCOME.name,
            category="Salary",
            amount_in_cents=500000,
            date_of_expense="2025-01-15",
        )

        response = self.client.get(
            reverse("year_review_with_year", kwargs={"year": 2025})
        )

        type_breakdown = response.context["type_breakdown"]
        self.assertEqual(type_breakdown["Income"][0], Decimal("0.00"))
        self.assertEqual(type_breakdown["Income"][12], Decimal("0.00"))

    def test_year_review_view_has_navigation_data(self):
        response = self.client.get(
            reverse("year_review_with_year", kwargs={"year": 2025})
        )

        self.assertEqual(response.context["year"], 2025)
        self.assertEqual(response.context["prev_year"], 2024)
        self.assertEqual(response.context["next_year"], 2026)

    def test_year_review_view_shows_has_data_flag(self):
        response = self.client.get(
            reverse("year_review_with_year", kwargs={"year": 2025})
        )
        self.assertFalse(response.context["has_data"])

        Budget.objects.create(
            user=self.user,
            type=TransactionType.INCOME.name,
            category="Salary",
            amount_in_cents=500000,
            budget_year=2025,
            budget_month=1,
        )

        response = self.client.get(
            reverse("year_review_with_year", kwargs={"year": 2025})
        )
        self.assertTrue(response.context["has_data"])

    def test_year_review_view_category_breakdown_structure(self):
        Budget.objects.create(
            user=self.user,
            type=TransactionType.NEED.name,
            category="Rent",
            amount_in_cents=150000,
            budget_year=2025,
            budget_month=1,
        )

        Transaction.objects.create(
            user=self.user,
            type=TransactionType.NEED.name,
            category="Rent",
            amount_in_cents=150000,
            date_of_expense="2025-01-15",
        )

        response = self.client.get(
            reverse("year_review_with_year", kwargs={"year": 2025})
        )

        category_breakdowns = response.context["category_breakdowns"]
        self.assertIn("Rent", category_breakdowns["Need"])
        self.assertIn("months", category_breakdowns["Need"]["Rent"])
        self.assertIn("total", category_breakdowns["Need"]["Rent"])
        self.assertIn("average", category_breakdowns["Need"]["Rent"])

    def test_year_review_view_filters_transactions_by_year(self):
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.NEED.name,
            category="Groceries",
            amount_in_cents=10000,
            date_of_expense="2025-01-15",
        )

        Transaction.objects.create(
            user=self.user,
            type=TransactionType.NEED.name,
            category="Groceries",
            amount_in_cents=20000,
            date_of_expense="2024-01-15",
        )

        response = self.client.get(
            reverse("year_review_with_year", kwargs={"year": 2025})
        )

        type_breakdown = response.context["type_breakdown"]
        self.assertEqual(type_breakdown["Need"][0], Decimal("100.00"))
        self.assertEqual(type_breakdown["Need"][12], Decimal("100.00"))

    def test_year_review_view_excludes_income_from_category_breakdown(self):
        Budget.objects.create(
            user=self.user,
            type=TransactionType.INCOME.name,
            category="Salary",
            amount_in_cents=500000,
            budget_year=2025,
            budget_month=1,
        )

        response = self.client.get(
            reverse("year_review_with_year", kwargs={"year": 2025})
        )

        category_breakdowns = response.context["category_breakdowns"]
        self.assertNotIn("Income", category_breakdowns)
