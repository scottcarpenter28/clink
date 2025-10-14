from decimal import Decimal

from django.test import TestCase
from django.contrib.auth.models import User

from finance.models import Budget, Transaction
from finance.enums.transaction_enums import TransactionType
from finance.utils.year_aggregation import (
    get_budgets_for_year,
    get_transactions_for_year,
    aggregate_by_month_and_type,
    aggregate_by_category_and_month,
)


def create_transaction(user, transaction_type, category, amount_cents, date):
    return Transaction.objects.create(
        user=user,
        type=transaction_type.name,
        category=category,
        amount_in_cents=amount_cents,
        date_of_expense=date,
    )


def create_budget(user, transaction_type, category, amount_cents, year, month):
    return Budget.objects.create(
        user=user,
        type=transaction_type.name,
        category=category,
        amount_in_cents=amount_cents,
        budget_year=year,
        budget_month=month,
    )


class GetBudgetsForYearTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

    def test_returns_budgets_for_specified_year(self):
        create_budget(self.user, TransactionType.NEED, "Rent", 150000, 2025, 1)
        create_budget(self.user, TransactionType.NEED, "Rent", 150000, 2024, 1)

        budgets = get_budgets_for_year(self.user, 2025)
        self.assertEqual(budgets.count(), 1)
        self.assertEqual(budgets.first().budget_year, 2025)

    def test_returns_empty_queryset_when_no_budgets_for_year(self):
        budgets = get_budgets_for_year(self.user, 2025)
        self.assertEqual(budgets.count(), 0)


class GetTransactionsForYearTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

    def test_returns_transactions_for_specified_year(self):
        create_transaction(
            self.user, TransactionType.NEED, "Rent", 150000, "2025-01-01"
        )
        create_transaction(
            self.user, TransactionType.NEED, "Rent", 150000, "2024-01-01"
        )

        transactions = get_transactions_for_year(self.user, 2025)
        self.assertEqual(transactions.count(), 1)
        self.assertEqual(transactions.first().date_of_expense.year, 2025)

    def test_returns_empty_queryset_when_no_transactions_for_year(self):
        transactions = get_transactions_for_year(self.user, 2025)
        self.assertEqual(transactions.count(), 0)


class AggregateByMonthAndTypeTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

    def test_returns_all_transaction_types(self):
        budgets = Budget.objects.filter(user=self.user)
        transactions = Transaction.objects.filter(user=self.user)

        result = aggregate_by_month_and_type(budgets, transactions)

        expected_keys = [
            "Income",
            "Need",
            "Want",
            "Debts",
            "Savings",
            "Investing",
        ]
        self.assertEqual(list(result.keys()), expected_keys)

    def test_returns_14_values_per_type(self):
        budgets = Budget.objects.filter(user=self.user)
        transactions = Transaction.objects.filter(user=self.user)

        result = aggregate_by_month_and_type(budgets, transactions)

        for transaction_type in result.values():
            self.assertEqual(len(transaction_type), 14)

    def test_aggregates_transactions_by_month(self):
        create_transaction(
            self.user, TransactionType.NEED, "Rent", 100000, "2025-01-15"
        )
        create_transaction(
            self.user, TransactionType.NEED, "Groceries", 50000, "2025-01-20"
        )
        create_transaction(
            self.user, TransactionType.NEED, "Rent", 100000, "2025-02-15"
        )

        budgets = Budget.objects.filter(user=self.user)
        transactions = Transaction.objects.filter(user=self.user)

        result = aggregate_by_month_and_type(budgets, transactions)

        self.assertEqual(result["Need"][0], Decimal("1500.00"))
        self.assertEqual(result["Need"][1], Decimal("1000.00"))
        self.assertEqual(result["Need"][2], Decimal("0.00"))

    def test_calculates_year_total_correctly(self):
        create_transaction(
            self.user, TransactionType.INCOME, "Salary", 500000, "2025-01-15"
        )
        create_transaction(
            self.user, TransactionType.INCOME, "Salary", 500000, "2025-06-15"
        )

        budgets = Budget.objects.filter(user=self.user)
        transactions = Transaction.objects.filter(user=self.user)

        result = aggregate_by_month_and_type(budgets, transactions)

        self.assertEqual(result["Income"][12], Decimal("10000.00"))

    def test_calculates_average_correctly(self):
        create_transaction(
            self.user, TransactionType.WANT, "Entertainment", 120000, "2025-01-15"
        )

        budgets = Budget.objects.filter(user=self.user)
        transactions = Transaction.objects.filter(user=self.user)

        result = aggregate_by_month_and_type(budgets, transactions)

        self.assertEqual(result["Want"][13], Decimal("1200.00"))

    def test_returns_zero_when_no_transactions(self):
        budgets = Budget.objects.filter(user=self.user)
        transactions = Transaction.objects.filter(user=self.user)

        result = aggregate_by_month_and_type(budgets, transactions)

        for month_index in range(12):
            self.assertEqual(result["Need"][month_index], Decimal("0.00"))
        self.assertEqual(result["Need"][12], Decimal("0.00"))
        self.assertEqual(result["Need"][13], Decimal("0.00"))


class AggregateByCategoryAndMonthTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

    def test_returns_categories_from_budgets(self):
        create_budget(self.user, TransactionType.NEED, "Rent", 150000, 2025, 1)
        create_budget(self.user, TransactionType.NEED, "Groceries", 50000, 2025, 1)

        budgets = Budget.objects.filter(user=self.user)
        transactions = Transaction.objects.filter(user=self.user)

        result = aggregate_by_category_and_month(
            budgets, transactions, TransactionType.NEED
        )

        self.assertIn("Rent", result)
        self.assertIn("Groceries", result)

    def test_aggregates_transactions_by_category_and_month(self):
        create_budget(self.user, TransactionType.NEED, "Rent", 150000, 2025, 1)
        create_transaction(
            self.user, TransactionType.NEED, "Rent", 100000, "2025-01-15"
        )
        create_transaction(self.user, TransactionType.NEED, "Rent", 50000, "2025-02-15")

        budgets = Budget.objects.filter(user=self.user)
        transactions = Transaction.objects.filter(user=self.user)

        result = aggregate_by_category_and_month(
            budgets, transactions, TransactionType.NEED
        )

        self.assertEqual(result["Rent"]["months"][0], Decimal("1000.00"))
        self.assertEqual(result["Rent"]["months"][1], Decimal("500.00"))
        self.assertEqual(result["Rent"]["months"][2], Decimal("0.00"))

    def test_calculates_total_for_category(self):
        create_budget(
            self.user, TransactionType.SAVINGS, "Emergency Fund", 100000, 2025, 1
        )
        create_transaction(
            self.user, TransactionType.SAVINGS, "Emergency Fund", 100000, "2025-01-15"
        )
        create_transaction(
            self.user, TransactionType.SAVINGS, "Emergency Fund", 100000, "2025-06-15"
        )

        budgets = Budget.objects.filter(user=self.user)
        transactions = Transaction.objects.filter(user=self.user)

        result = aggregate_by_category_and_month(
            budgets, transactions, TransactionType.SAVINGS
        )

        self.assertEqual(result["Emergency Fund"]["total"], Decimal("2000.00"))

    def test_calculates_average_for_category(self):
        create_budget(self.user, TransactionType.WANT, "Dining Out", 50000, 2025, 1)
        create_transaction(
            self.user, TransactionType.WANT, "Dining Out", 120000, "2025-01-15"
        )

        budgets = Budget.objects.filter(user=self.user)
        transactions = Transaction.objects.filter(user=self.user)

        result = aggregate_by_category_and_month(
            budgets, transactions, TransactionType.WANT
        )

        self.assertEqual(result["Dining Out"]["average"], Decimal("1200.00"))

    def test_returns_empty_dict_when_no_budgets_for_type(self):
        budgets = Budget.objects.filter(user=self.user)
        transactions = Transaction.objects.filter(user=self.user)

        result = aggregate_by_category_and_month(
            budgets, transactions, TransactionType.NEED
        )

        self.assertEqual(result, {})

    def test_excludes_other_transaction_types(self):
        create_budget(self.user, TransactionType.NEED, "Rent", 150000, 2025, 1)
        create_transaction(
            self.user, TransactionType.NEED, "Rent", 100000, "2025-01-15"
        )
        create_transaction(self.user, TransactionType.WANT, "Rent", 50000, "2025-01-15")

        budgets = Budget.objects.filter(user=self.user)
        transactions = Transaction.objects.filter(user=self.user)

        result = aggregate_by_category_and_month(
            budgets, transactions, TransactionType.NEED
        )

        self.assertEqual(result["Rent"]["months"][0], Decimal("1000.00"))
