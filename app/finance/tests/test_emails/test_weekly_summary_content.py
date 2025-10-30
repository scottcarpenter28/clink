from django.test import TestCase
from django.contrib.auth.models import User

from finance.emails.weekly_summary.content import (
    build_weekly_summary_subject,
    build_weekly_summary_content,
)
from finance.emails.weekly_summary.calculations import WeeklySummaryData


class WeeklySummaryContentTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            first_name="John",
        )

        self.user_no_name = User.objects.create_user(
            username="user_no_name",
            email="user@example.com",
            password="testpass123",
        )

    def test_build_weekly_summary_subject(self):
        subject = build_weekly_summary_subject()
        self.assertEqual(subject, "Your Weekly Spending Summary")

    def test_build_weekly_summary_content_with_first_name(self):
        summary_data: WeeklySummaryData = {
            "totals_by_category": [
                {"category": "Groceries", "total": 75.0},
                {"category": "Entertainment", "total": 30.0},
            ],
            "remaining_budgets": [],
            "grand_total": 105.0,
        }

        content = build_weekly_summary_content(self.user, summary_data)

        self.assertIn("Hello John", content)
        self.assertIn("Groceries: $75.00", content)
        self.assertIn("Entertainment: $30.00", content)
        self.assertIn("Total Spent: $105.00", content)

    def test_build_weekly_summary_content_with_username_fallback(self):
        summary_data: WeeklySummaryData = {
            "totals_by_category": [],
            "remaining_budgets": [],
            "grand_total": 0.0,
        }

        content = build_weekly_summary_content(self.user_no_name, summary_data)

        self.assertIn("Hello user_no_name", content)

    def test_build_weekly_summary_content_with_no_expenses(self):
        summary_data: WeeklySummaryData = {
            "totals_by_category": [],
            "remaining_budgets": [],
            "grand_total": 0.0,
        }

        content = build_weekly_summary_content(self.user, summary_data)

        self.assertIn("No expenses recorded this week", content)

    def test_build_weekly_summary_content_with_budget_status(self):
        summary_data: WeeklySummaryData = {
            "totals_by_category": [{"category": "Groceries", "total": 50.0}],
            "remaining_budgets": [
                {
                    "category": "Groceries",
                    "budget": 100.0,
                    "spent": 50.0,
                    "remaining": 50.0,
                }
            ],
            "grand_total": 50.0,
        }

        content = build_weekly_summary_content(self.user, summary_data)

        self.assertIn("BUDGET STATUS", content)
        self.assertIn("Groceries: $50.00 / $100.00", content)
        self.assertIn("$50.00 remaining", content)

    def test_build_weekly_summary_content_with_over_budget(self):
        summary_data: WeeklySummaryData = {
            "totals_by_category": [{"category": "Groceries", "total": 150.0}],
            "remaining_budgets": [
                {
                    "category": "Groceries",
                    "budget": 100.0,
                    "spent": 150.0,
                    "remaining": -50.0,
                }
            ],
            "grand_total": 150.0,
        }

        content = build_weekly_summary_content(self.user, summary_data)

        self.assertIn("Groceries: $150.00 / $100.00", content)
        self.assertIn("$50.00 over budget", content)

    def test_build_weekly_summary_content_includes_preferences_info(self):
        summary_data: WeeklySummaryData = {
            "totals_by_category": [],
            "remaining_budgets": [],
            "grand_total": 0.0,
        }

        content = build_weekly_summary_content(self.user, summary_data)

        self.assertIn("manage your email preferences", content)
