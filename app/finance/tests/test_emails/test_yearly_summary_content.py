from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone

from finance.emails.yearly_summary.content import (
    build_yearly_summary_subject,
    build_yearly_summary_content,
)
from finance.emails.yearly_summary.calculations import YearlySummaryData


class YearlySummaryContentTests(TestCase):
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

    def test_build_yearly_summary_subject_includes_year(self):
        current_date = timezone.now()
        year = current_date.year

        subject = build_yearly_summary_subject()

        self.assertEqual(subject, f"Your {year} Year in Review")

    def test_build_yearly_summary_content_with_first_name(self):
        current_date = timezone.now()
        year = current_date.year

        summary_data: YearlySummaryData = {
            "totals_by_category": [],
            "grand_total": 5000.0,
            "total_income": 5000.0,
            "total_expenses": 0.0,
            "net_income": 5000.0,
        }

        content = build_yearly_summary_content(self.user, summary_data)

        self.assertIn("Hello John", content)
        self.assertIn(f"year in review for {year}", content)

    def test_build_yearly_summary_content_with_username_fallback(self):
        summary_data: YearlySummaryData = {
            "totals_by_category": [],
            "grand_total": 0.0,
            "total_income": 0.0,
            "total_expenses": 0.0,
            "net_income": 0.0,
        }

        content = build_yearly_summary_content(self.user_no_name, summary_data)

        self.assertIn("Hello user_no_name", content)

    def test_build_yearly_summary_content_includes_overview(self):
        summary_data: YearlySummaryData = {
            "totals_by_category": [],
            "grand_total": 5400.0,
            "total_income": 5000.0,
            "total_expenses": 400.0,
            "net_income": 4600.0,
        }

        content = build_yearly_summary_content(self.user, summary_data)

        self.assertIn("Total Income: $5000.00", content)
        self.assertIn("Total Expenses: $400.00", content)
        self.assertIn("Net Income: +$4600.00", content)

    def test_build_yearly_summary_content_with_negative_net_income(self):
        summary_data: YearlySummaryData = {
            "totals_by_category": [],
            "grand_total": 2000.0,
            "total_income": 500.0,
            "total_expenses": 1500.0,
            "net_income": -1000.0,
        }

        content = build_yearly_summary_content(self.user, summary_data)

        self.assertIn("Net Income: -$1000.00", content)

    def test_build_yearly_summary_content_shows_top_5_categories(self):
        summary_data: YearlySummaryData = {
            "totals_by_category": [
                {"category": "Groceries (NEED)", "total": 500.0},
                {"category": "Rent (NEED)", "total": 400.0},
                {"category": "Entertainment (WANT)", "total": 300.0},
                {"category": "Utilities (NEED)", "total": 200.0},
                {"category": "Gas (NEED)", "total": 100.0},
                {"category": "Coffee (WANT)", "total": 50.0},
            ],
            "grand_total": 1550.0,
            "total_income": 2000.0,
            "total_expenses": 1550.0,
            "net_income": 450.0,
        }

        content = build_yearly_summary_content(self.user, summary_data)

        self.assertIn("Groceries (NEED): $500.00", content)
        self.assertIn("Rent (NEED): $400.00", content)
        self.assertIn("Entertainment (WANT): $300.00", content)
        self.assertIn("Utilities (NEED): $200.00", content)
        self.assertIn("Gas (NEED): $100.00", content)
        self.assertNotIn("Coffee (WANT)", content)
        self.assertIn("...and 1 more categories", content)

    def test_build_yearly_summary_content_shows_all_when_5_or_fewer_categories(self):
        summary_data: YearlySummaryData = {
            "totals_by_category": [
                {"category": "Groceries (NEED)", "total": 500.0},
                {"category": "Rent (NEED)", "total": 400.0},
                {"category": "Entertainment (WANT)", "total": 300.0},
            ],
            "grand_total": 1200.0,
            "total_income": 2000.0,
            "total_expenses": 1200.0,
            "net_income": 800.0,
        }

        content = build_yearly_summary_content(self.user, summary_data)

        self.assertIn("Groceries (NEED): $500.00", content)
        self.assertIn("Rent (NEED): $400.00", content)
        self.assertIn("Entertainment (WANT): $300.00", content)
        self.assertNotIn("...and", content)

    def test_build_yearly_summary_content_with_no_transactions(self):
        summary_data: YearlySummaryData = {
            "totals_by_category": [],
            "grand_total": 0.0,
            "total_income": 0.0,
            "total_expenses": 0.0,
            "net_income": 0.0,
        }

        content = build_yearly_summary_content(self.user, summary_data)

        self.assertIn("No transactions recorded this year", content)

    def test_build_yearly_summary_content_includes_preferences_info(self):
        summary_data: YearlySummaryData = {
            "totals_by_category": [],
            "grand_total": 0.0,
            "total_income": 0.0,
            "total_expenses": 0.0,
            "net_income": 0.0,
        }

        content = build_yearly_summary_content(self.user, summary_data)

        self.assertIn("manage your email preferences", content)

    def test_build_yearly_summary_content_includes_year_in_closing(self):
        current_date = timezone.now()
        year = current_date.year

        summary_data: YearlySummaryData = {
            "totals_by_category": [],
            "grand_total": 0.0,
            "total_income": 0.0,
            "total_expenses": 0.0,
            "net_income": 0.0,
        }

        content = build_yearly_summary_content(self.user, summary_data)

        self.assertIn(f"throughout {year}", content)
