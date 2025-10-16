from datetime import date

from django.test import TestCase
from django.contrib.auth.models import User

from finance.models import Budget, Transaction, InternalTransfer
from finance.enums.transaction_enums import TransactionType
from finance.utils.budget_calculator import process_month_end_carry_over


class ProcessMonthEndCarryOverTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

    def test_processes_budget_with_surplus(self):
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
            amount_in_cents=30000,
            date_of_expense=date(2025, 1, 15),
        )

        results = process_month_end_carry_over(self.user, 2025, 1)

        self.assertEqual(results["processed"], 1)
        self.assertEqual(results["created"], 1)

        next_budget = Budget.objects.get(
            user=self.user,
            category="Emergency Fund",
            type=TransactionType.SAVINGS.name,
            budget_year=2025,
            budget_month=2,
        )

        self.assertEqual(next_budget.carried_over_amount_in_cents, 70000)

    def test_processes_budget_with_deficit(self):
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
            amount_in_cents=150000,
            date_of_expense=date(2025, 1, 15),
        )

        results = process_month_end_carry_over(self.user, 2025, 1)

        self.assertEqual(results["processed"], 1)
        self.assertEqual(results["created"], 1)

        next_budget = Budget.objects.get(
            user=self.user,
            category="Emergency Fund",
            type=TransactionType.SAVINGS.name,
            budget_year=2025,
            budget_month=2,
        )

        self.assertEqual(next_budget.carried_over_amount_in_cents, 0)

    def test_skips_budget_without_allow_carry_over(self):
        Budget.objects.create(
            user=self.user,
            type=TransactionType.NEED.name,
            category="Groceries",
            amount_in_cents=50000,
            budget_year=2025,
            budget_month=1,
            allow_carry_over=False,
        )

        results = process_month_end_carry_over(self.user, 2025, 1)

        self.assertEqual(results["processed"], 0)
        self.assertFalse(
            Budget.objects.filter(
                user=self.user,
                category="Groceries",
                budget_year=2025,
                budget_month=2,
            ).exists()
        )

    def test_handles_year_boundary(self):
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
            date_of_expense=date(2025, 12, 15),
        )

        results = process_month_end_carry_over(self.user, 2025, 12)

        self.assertEqual(results["processed"], 1)
        self.assertEqual(results["created"], 1)

        next_budget = Budget.objects.get(
            user=self.user,
            category="Index Fund",
            type=TransactionType.INVESTING.name,
            budget_year=2026,
            budget_month=1,
        )

        self.assertEqual(next_budget.carried_over_amount_in_cents, 100000)

    def test_updates_existing_next_month_budget(self):
        Budget.objects.create(
            user=self.user,
            type=TransactionType.SAVINGS.name,
            category="Vacation",
            amount_in_cents=100000,
            budget_year=2025,
            budget_month=1,
            allow_carry_over=True,
        )

        Budget.objects.create(
            user=self.user,
            type=TransactionType.SAVINGS.name,
            category="Vacation",
            amount_in_cents=100000,
            budget_year=2025,
            budget_month=2,
            allow_carry_over=True,
            carried_over_amount_in_cents=0,
        )

        Transaction.objects.create(
            user=self.user,
            type=TransactionType.SAVINGS.name,
            category="Vacation",
            amount_in_cents=25000,
            date_of_expense=date(2025, 1, 20),
        )

        results = process_month_end_carry_over(self.user, 2025, 1)

        self.assertEqual(results["processed"], 1)
        self.assertEqual(results["created"], 0)
        self.assertEqual(results["updated"], 1)

        next_budget = Budget.objects.get(
            user=self.user,
            category="Vacation",
            type=TransactionType.SAVINGS.name,
            budget_year=2025,
            budget_month=2,
        )

        self.assertEqual(next_budget.carried_over_amount_in_cents, 75000)

    def test_skips_if_carry_over_unchanged(self):
        Budget.objects.create(
            user=self.user,
            type=TransactionType.SAVINGS.name,
            category="Vacation",
            amount_in_cents=100000,
            budget_year=2025,
            budget_month=1,
            allow_carry_over=True,
        )

        Budget.objects.create(
            user=self.user,
            type=TransactionType.SAVINGS.name,
            category="Vacation",
            amount_in_cents=100000,
            budget_year=2025,
            budget_month=2,
            allow_carry_over=True,
            carried_over_amount_in_cents=100000,
        )

        results = process_month_end_carry_over(self.user, 2025, 1)

        self.assertEqual(results["processed"], 1)
        self.assertEqual(results["created"], 0)
        self.assertEqual(results["updated"], 0)
        self.assertEqual(results["skipped"], 1)

    def test_includes_internal_transfers_in_calculation(self):
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
            amount_in_cents=20000,
            transfer_date=date(2025, 1, 10),
        )

        results = process_month_end_carry_over(self.user, 2025, 1)

        self.assertEqual(results["processed"], 2)

        emergency_budget = Budget.objects.get(
            user=self.user,
            category="Emergency Fund",
            budget_year=2025,
            budget_month=2,
        )
        self.assertEqual(emergency_budget.carried_over_amount_in_cents, 80000)

        vacation_budget = Budget.objects.get(
            user=self.user,
            category="Vacation",
            budget_year=2025,
            budget_month=2,
        )
        self.assertEqual(vacation_budget.carried_over_amount_in_cents, 70000)

    def test_chain_carry_over_across_multiple_months(self):
        Budget.objects.create(
            user=self.user,
            type=TransactionType.SAVINGS.name,
            category="House Down Payment",
            amount_in_cents=200000,
            budget_year=2025,
            budget_month=1,
            allow_carry_over=True,
        )

        Transaction.objects.create(
            user=self.user,
            type=TransactionType.SAVINGS.name,
            category="House Down Payment",
            amount_in_cents=50000,
            date_of_expense=date(2025, 1, 15),
        )

        process_month_end_carry_over(self.user, 2025, 1)

        feb_budget = Budget.objects.get(
            user=self.user,
            category="House Down Payment",
            budget_year=2025,
            budget_month=2,
        )
        self.assertEqual(feb_budget.carried_over_amount_in_cents, 150000)

        Transaction.objects.create(
            user=self.user,
            type=TransactionType.SAVINGS.name,
            category="House Down Payment",
            amount_in_cents=30000,
            date_of_expense=date(2025, 2, 10),
        )

        process_month_end_carry_over(self.user, 2025, 2)

        mar_budget = Budget.objects.get(
            user=self.user,
            category="House Down Payment",
            budget_year=2025,
            budget_month=3,
        )

        expected_carry_over = 200000 + 150000 - 30000
        self.assertEqual(mar_budget.carried_over_amount_in_cents, expected_carry_over)

    def test_processes_multiple_budgets(self):
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
            type=TransactionType.INVESTING.name,
            category="Retirement",
            amount_in_cents=150000,
            budget_year=2025,
            budget_month=1,
            allow_carry_over=True,
        )

        Budget.objects.create(
            user=self.user,
            type=TransactionType.NEED.name,
            category="Rent",
            amount_in_cents=120000,
            budget_year=2025,
            budget_month=1,
            allow_carry_over=False,
        )

        results = process_month_end_carry_over(self.user, 2025, 1)

        self.assertEqual(results["processed"], 2)
        self.assertEqual(len(results["budgets_processed"]), 2)

    def test_isolates_users(self):
        other_user = User.objects.create_user(
            username="otheruser", password="testpass123"
        )

        Budget.objects.create(
            user=self.user,
            type=TransactionType.SAVINGS.name,
            category="Savings",
            amount_in_cents=100000,
            budget_year=2025,
            budget_month=1,
            allow_carry_over=True,
        )

        Budget.objects.create(
            user=other_user,
            type=TransactionType.SAVINGS.name,
            category="Savings",
            amount_in_cents=200000,
            budget_year=2025,
            budget_month=1,
            allow_carry_over=True,
        )

        results = process_month_end_carry_over(self.user, 2025, 1)

        self.assertEqual(results["processed"], 1)

        self.assertTrue(
            Budget.objects.filter(
                user=self.user, budget_year=2025, budget_month=2
            ).exists()
        )
        self.assertFalse(
            Budget.objects.filter(
                user=other_user, budget_year=2025, budget_month=2
            ).exists()
        )

    def test_idempotency(self):
        Budget.objects.create(
            user=self.user,
            type=TransactionType.SAVINGS.name,
            category="Emergency Fund",
            amount_in_cents=100000,
            budget_year=2025,
            budget_month=1,
            allow_carry_over=True,
        )

        results1 = process_month_end_carry_over(self.user, 2025, 1)
        results2 = process_month_end_carry_over(self.user, 2025, 1)

        self.assertEqual(results1["processed"], 1)
        self.assertEqual(results2["processed"], 1)

        self.assertEqual(results1["created"], 1)
        self.assertEqual(results2["created"], 0)
        self.assertEqual(results2["skipped"], 1)

        budgets = Budget.objects.filter(
            user=self.user,
            category="Emergency Fund",
            budget_year=2025,
            budget_month=2,
        )

        self.assertEqual(budgets.count(), 1)
        self.assertEqual(budgets.first().carried_over_amount_in_cents, 100000)
