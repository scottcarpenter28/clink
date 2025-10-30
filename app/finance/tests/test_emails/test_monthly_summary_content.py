from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone

from finance.emails.monthly_summary.content import (
    build_monthly_summary_subject,
    build_monthly_summary_content,
)
from finance.emails.monthly_summary.calculations import MonthlySummaryData


class MonthlySummaryContentTests(TestCase):
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

    def test_build_monthly_summary_subject_includes_month_name(self):
        current_date = timezone.now()
        month_name = current_date.strftime("%B")

        subject = build_monthly_summary_subject()

        self.assertEqual(subject, f"Your {month_name} Financial Summary")

    def test_build_monthly_summary_content_with_first_name(self):
        current_date = timezone.now()
        month_name = current_date.strftime("%B")

        summary_data: MonthlySummaryData = {
            "totals_by_type": [],
            "income": 5000.0,
            "savings": 1000.0,
            "investing": 750.0,
            "needs": 250.0,
            "wants": 150.0,
            "debts": 100.0,
            "total_expenses": 2250.0,
        }

        content = build_monthly_summary_content(self.user, summary_data)

        self.assertIn("Hello John", content)
        self.assertIn(f"summary for {month_name}", content)

    def test_build_monthly_summary_content_with_username_fallback(self):
        summary_data: MonthlySummaryData = {
            "totals_by_type": [],
            "income": 0.0,
            "savings": 0.0,
            "investing": 0.0,
            "needs": 0.0,
            "wants": 0.0,
            "debts": 0.0,
            "total_expenses": 0.0,
        }

        content = build_monthly_summary_content(self.user_no_name, summary_data)

        self.assertIn("Hello user_no_name", content)

    def test_build_monthly_summary_content_includes_income_and_expenses(self):
        summary_data: MonthlySummaryData = {
            "totals_by_type": [],
            "income": 5000.0,
            "savings": 1000.0,
            "investing": 750.0,
            "needs": 250.0,
            "wants": 150.0,
            "debts": 100.0,
            "total_expenses": 2250.0,
        }

        content = build_monthly_summary_content(self.user, summary_data)

        self.assertIn("Income: $5000.00", content)
        self.assertIn("Total Expenses: $2250.00", content)

    def test_build_monthly_summary_content_calculates_net_positive(self):
        summary_data: MonthlySummaryData = {
            "totals_by_type": [],
            "income": 5000.0,
            "savings": 1000.0,
            "investing": 750.0,
            "needs": 250.0,
            "wants": 150.0,
            "debts": 100.0,
            "total_expenses": 2250.0,
        }

        content = build_monthly_summary_content(self.user, summary_data)

        self.assertIn("Net: +$2750.00", content)

    def test_build_monthly_summary_content_calculates_net_negative(self):
        summary_data: MonthlySummaryData = {
            "totals_by_type": [],
            "income": 2000.0,
            "savings": 1000.0,
            "investing": 750.0,
            "needs": 250.0,
            "wants": 150.0,
            "debts": 100.0,
            "total_expenses": 2250.0,
        }

        content = build_monthly_summary_content(self.user, summary_data)

        self.assertIn("Net: -$250.00", content)

    def test_build_monthly_summary_content_includes_breakdown(self):
        summary_data: MonthlySummaryData = {
            "totals_by_type": [],
            "income": 5000.0,
            "savings": 1000.0,
            "investing": 750.0,
            "needs": 250.0,
            "wants": 150.0,
            "debts": 100.0,
            "total_expenses": 2250.0,
        }

        content = build_monthly_summary_content(self.user, summary_data)

        self.assertIn("Savings: $1000.00", content)
        self.assertIn("Investing: $750.00", content)
        self.assertIn("Needs: $250.00", content)
        self.assertIn("Wants: $150.00", content)
        self.assertIn("Debts: $100.00", content)

    def test_build_monthly_summary_content_excludes_zero_amounts(self):
        summary_data: MonthlySummaryData = {
            "totals_by_type": [],
            "income": 5000.0,
            "savings": 0.0,
            "investing": 0.0,
            "needs": 250.0,
            "wants": 0.0,
            "debts": 0.0,
            "total_expenses": 250.0,
        }

        content = build_monthly_summary_content(self.user, summary_data)

        self.assertNotIn("Savings:", content)
        self.assertNotIn("Investing:", content)
        self.assertNotIn("Wants:", content)
        self.assertNotIn("Debts:", content)
        self.assertIn("Needs: $250.00", content)

    def test_build_monthly_summary_content_with_no_expenses(self):
        summary_data: MonthlySummaryData = {
            "totals_by_type": [],
            "income": 0.0,
            "savings": 0.0,
            "investing": 0.0,
            "needs": 0.0,
            "wants": 0.0,
            "debts": 0.0,
            "total_expenses": 0.0,
        }

        content = build_monthly_summary_content(self.user, summary_data)

        self.assertIn("No expenses recorded this month", content)

    def test_build_monthly_summary_content_includes_preferences_info(self):
        summary_data: MonthlySummaryData = {
            "totals_by_type": [],
            "income": 0.0,
            "savings": 0.0,
            "investing": 0.0,
            "needs": 0.0,
            "wants": 0.0,
            "debts": 0.0,
            "total_expenses": 0.0,
        }

        content = build_monthly_summary_content(self.user, summary_data)

        self.assertIn("manage your email preferences", content)
