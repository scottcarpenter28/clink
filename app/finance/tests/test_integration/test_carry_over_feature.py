from datetime import date

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

from finance.models import Budget, Transaction, InternalTransfer
from finance.enums.transaction_enums import TransactionType
from finance.utils.budget_calculator import process_month_end_carry_over


class CarryOverAcrossMultipleMonthsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

    def test_carry_over_across_three_consecutive_months(self):
        Budget.objects.create(
            user=self.user,
            type=TransactionType.SAVINGS.name,
            category="Emergency Fund",
            amount_in_cents=100000,
            budget_year=2025,
            budget_month=1,
            allow_carry_over=True,
        )

        Transaction.objects.create(
            user=self.user,
            type=TransactionType.SAVINGS.name,
            category="Emergency Fund",
            amount_in_cents=25000,
            date_of_expense=date(2025, 1, 15),
        )

        process_month_end_carry_over(self.user, 2025, 1)

        feb_budget = Budget.objects.get(
            user=self.user,
            category="Emergency Fund",
            budget_year=2025,
            budget_month=2,
        )
        self.assertEqual(feb_budget.carried_over_amount_in_cents, 75000)
        self.assertEqual(feb_budget.amount_in_cents, 100000)

        Transaction.objects.create(
            user=self.user,
            type=TransactionType.SAVINGS.name,
            category="Emergency Fund",
            amount_in_cents=50000,
            date_of_expense=date(2025, 2, 10),
        )

        process_month_end_carry_over(self.user, 2025, 2)

        mar_budget = Budget.objects.get(
            user=self.user,
            category="Emergency Fund",
            budget_year=2025,
            budget_month=3,
        )

        expected_march_carry_over = 100000 + 75000 - 50000
        self.assertEqual(
            mar_budget.carried_over_amount_in_cents, expected_march_carry_over
        )

        Transaction.objects.create(
            user=self.user,
            type=TransactionType.SAVINGS.name,
            category="Emergency Fund",
            amount_in_cents=30000,
            date_of_expense=date(2025, 3, 5),
        )

        process_month_end_carry_over(self.user, 2025, 3)

        apr_budget = Budget.objects.get(
            user=self.user,
            category="Emergency Fund",
            budget_year=2025,
            budget_month=4,
        )

        expected_april_carry_over = 100000 + expected_march_carry_over - 30000
        self.assertEqual(
            apr_budget.carried_over_amount_in_cents, expected_april_carry_over
        )


class YearBoundaryCarryOverTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

    def test_carry_over_from_december_to_january(self):
        Budget.objects.create(
            user=self.user,
            type=TransactionType.INVESTING.name,
            category="Index Fund",
            amount_in_cents=200000,
            budget_year=2025,
            budget_month=12,
            allow_carry_over=True,
        )

        Transaction.objects.create(
            user=self.user,
            type=TransactionType.INVESTING.name,
            category="Index Fund",
            amount_in_cents=100000,
            date_of_expense=date(2025, 12, 20),
        )

        process_month_end_carry_over(self.user, 2025, 12)

        jan_budget = Budget.objects.get(
            user=self.user,
            category="Index Fund",
            budget_year=2026,
            budget_month=1,
        )

        self.assertEqual(jan_budget.carried_over_amount_in_cents, 100000)
        self.assertEqual(jan_budget.budget_year, 2026)
        self.assertEqual(jan_budget.budget_month, 1)


class CarryOverWithInternalTransfersTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

    def test_carry_over_with_outgoing_transfer(self):
        source_budget = Budget.objects.create(
            user=self.user,
            type=TransactionType.SAVINGS.name,
            category="Emergency Fund",
            amount_in_cents=100000,
            budget_year=2025,
            budget_month=1,
            allow_carry_over=True,
        )

        dest_budget = Budget.objects.create(
            user=self.user,
            type=TransactionType.SAVINGS.name,
            category="Vacation",
            amount_in_cents=50000,
            budget_year=2025,
            budget_month=1,
            allow_carry_over=True,
        )

        InternalTransfer.objects.create(
            user=self.user,
            source_budget=source_budget,
            destination_budget=dest_budget,
            amount_in_cents=30000,
            transfer_date=date(2025, 1, 15),
        )

        process_month_end_carry_over(self.user, 2025, 1)

        feb_emergency = Budget.objects.get(
            user=self.user,
            category="Emergency Fund",
            budget_year=2025,
            budget_month=2,
        )

        feb_vacation = Budget.objects.get(
            user=self.user,
            category="Vacation",
            budget_year=2025,
            budget_month=2,
        )

        self.assertEqual(feb_emergency.carried_over_amount_in_cents, 70000)
        self.assertEqual(feb_vacation.carried_over_amount_in_cents, 80000)

    def test_carry_over_with_use_funds_transfer(self):
        budget = Budget.objects.create(
            user=self.user,
            type=TransactionType.SAVINGS.name,
            category="Emergency Fund",
            amount_in_cents=100000,
            budget_year=2025,
            budget_month=1,
            allow_carry_over=True,
        )

        InternalTransfer.objects.create(
            user=self.user,
            source_budget=budget,
            destination_budget=None,
            amount_in_cents=25000,
            transfer_date=date(2025, 1, 10),
        )

        process_month_end_carry_over(self.user, 2025, 1)

        feb_budget = Budget.objects.get(
            user=self.user,
            category="Emergency Fund",
            budget_year=2025,
            budget_month=2,
        )

        self.assertEqual(feb_budget.carried_over_amount_in_cents, 75000)

    def test_carry_over_with_multiple_transfers(self):
        emergency = Budget.objects.create(
            user=self.user,
            type=TransactionType.SAVINGS.name,
            category="Emergency Fund",
            amount_in_cents=100000,
            budget_year=2025,
            budget_month=1,
            allow_carry_over=True,
        )

        vacation = Budget.objects.create(
            user=self.user,
            type=TransactionType.SAVINGS.name,
            category="Vacation",
            amount_in_cents=50000,
            budget_year=2025,
            budget_month=1,
            allow_carry_over=True,
        )

        car = Budget.objects.create(
            user=self.user,
            type=TransactionType.SAVINGS.name,
            category="Car Fund",
            amount_in_cents=75000,
            budget_year=2025,
            budget_month=1,
            allow_carry_over=True,
        )

        InternalTransfer.objects.create(
            user=self.user,
            source_budget=emergency,
            destination_budget=vacation,
            amount_in_cents=20000,
            transfer_date=date(2025, 1, 5),
        )

        InternalTransfer.objects.create(
            user=self.user,
            source_budget=emergency,
            destination_budget=car,
            amount_in_cents=15000,
            transfer_date=date(2025, 1, 10),
        )

        InternalTransfer.objects.create(
            user=self.user,
            source_budget=emergency,
            destination_budget=None,
            amount_in_cents=10000,
            transfer_date=date(2025, 1, 15),
        )

        process_month_end_carry_over(self.user, 2025, 1)

        feb_emergency = Budget.objects.get(
            user=self.user, category="Emergency Fund", budget_year=2025, budget_month=2
        )
        feb_vacation = Budget.objects.get(
            user=self.user, category="Vacation", budget_year=2025, budget_month=2
        )
        feb_car = Budget.objects.get(
            user=self.user, category="Car Fund", budget_year=2025, budget_month=2
        )

        self.assertEqual(feb_emergency.carried_over_amount_in_cents, 55000)
        self.assertEqual(feb_vacation.carried_over_amount_in_cents, 70000)
        self.assertEqual(feb_car.carried_over_amount_in_cents, 90000)


class MultipleBudgetsWithDifferentSettingsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

    def test_multiple_budgets_with_mixed_carry_over_settings(self):
        Budget.objects.create(
            user=self.user,
            type=TransactionType.SAVINGS.name,
            category="Emergency Fund",
            amount_in_cents=100000,
            budget_year=2025,
            budget_month=1,
            allow_carry_over=True,
        )

        Budget.objects.create(
            user=self.user,
            type=TransactionType.NEED.name,
            category="Groceries",
            amount_in_cents=50000,
            budget_year=2025,
            budget_month=1,
            allow_carry_over=False,
        )

        Budget.objects.create(
            user=self.user,
            type=TransactionType.INVESTING.name,
            category="Retirement",
            amount_in_cents=150000,
            budget_year=2025,
            budget_month=1,
            allow_carry_over=True,
        )

        process_month_end_carry_over(self.user, 2025, 1)

        self.assertTrue(
            Budget.objects.filter(
                user=self.user,
                category="Emergency Fund",
                budget_year=2025,
                budget_month=2,
            ).exists()
        )

        self.assertTrue(
            Budget.objects.filter(
                user=self.user,
                category="Retirement",
                budget_year=2025,
                budget_month=2,
            ).exists()
        )

        self.assertFalse(
            Budget.objects.filter(
                user=self.user,
                category="Groceries",
                budget_year=2025,
                budget_month=2,
            ).exists()
        )


class RetroactiveTransactionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

    def test_retroactive_transaction_updates_carry_over(self):
        Budget.objects.create(
            user=self.user,
            type=TransactionType.SAVINGS.name,
            category="Emergency Fund",
            amount_in_cents=100000,
            budget_year=2025,
            budget_month=1,
            allow_carry_over=True,
        )

        process_month_end_carry_over(self.user, 2025, 1)

        feb_budget = Budget.objects.get(
            user=self.user,
            category="Emergency Fund",
            budget_year=2025,
            budget_month=2,
        )
        self.assertEqual(feb_budget.carried_over_amount_in_cents, 100000)

        Transaction.objects.create(
            user=self.user,
            type=TransactionType.SAVINGS.name,
            category="Emergency Fund",
            amount_in_cents=40000,
            date_of_expense=date(2025, 1, 20),
        )

        process_month_end_carry_over(self.user, 2025, 1)

        feb_budget.refresh_from_db()
        self.assertEqual(feb_budget.carried_over_amount_in_cents, 60000)


class DashboardViewCarryOverTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.client.login(username="testuser", password="testpass123")

    def test_dashboard_triggers_carry_over_processing(self):
        jan_budget = Budget.objects.create(
            user=self.user,
            type=TransactionType.SAVINGS.name,
            category="Emergency Fund",
            amount_in_cents=100000,
            budget_year=2025,
            budget_month=1,
            allow_carry_over=True,
        )

        self.assertFalse(
            Budget.objects.filter(
                user=self.user,
                category="Emergency Fund",
                budget_year=2025,
                budget_month=2,
            ).exists()
        )

        response = self.client.get(
            reverse("home_with_date", kwargs={"year": 2025, "month": 2})
        )
        self.assertEqual(response.status_code, 200)

        self.assertTrue(
            Budget.objects.filter(
                user=self.user,
                category="Emergency Fund",
                budget_year=2025,
                budget_month=2,
            ).exists()
        )

        feb_budget = Budget.objects.get(
            user=self.user,
            category="Emergency Fund",
            budget_year=2025,
            budget_month=2,
        )
        self.assertEqual(feb_budget.carried_over_amount_in_cents, 100000)
