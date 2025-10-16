from decimal import Decimal
from typing import Optional

from django.db.models import Sum, QuerySet
from django.contrib.auth.models import User

from finance.models import Budget, Transaction, InternalTransfer
from finance.enums.transaction_enums import TransactionType


class BudgetLineItem:
    def __init__(
        self,
        budget: Budget,
        actual_spent_cents: int,
        carried_over_cents: int = 0,
        net_transfer_cents: int = 0,
    ):
        self.id = budget.id
        self.category = budget.category
        self.expected = Decimal(str(budget.amount_dollars))
        self.actual = Decimal(actual_spent_cents) / 100
        self.carried_over = Decimal(carried_over_cents) / 100
        self.net_transfers = Decimal(net_transfer_cents) / 100
        self.available = self.expected + self.carried_over + self.net_transfers
        self.remaining = self.expected - self.actual
        self.true_remaining = self.available - self.actual
        self.allow_carry_over = budget.allow_carry_over

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "category": self.category,
            "expected": self.expected,
            "actual": self.actual,
            "carried_over": self.carried_over,
            "net_transfers": self.net_transfers,
            "available": self.available,
            "remaining": self.remaining,
            "true_remaining": self.true_remaining,
            "allow_carry_over": self.allow_carry_over,
        }


def calculate_actual_spent_for_budget(
    budget: Budget, transactions: QuerySet[Transaction]
) -> int:
    result = transactions.filter(type=budget.type, category=budget.category).aggregate(
        total=Sum("amount_in_cents")
    )["total"]
    return result or 0


def calculate_carry_over_for_budget(
    user: User, category: str, transaction_type: str, year: int, month: int
) -> int:
    if month == 1:
        prev_year = year - 1
        prev_month = 12
    else:
        prev_year = year
        prev_month = month - 1

    try:
        previous_budget = Budget.objects.get(
            user=user,
            category=category,
            type=transaction_type,
            budget_year=prev_year,
            budget_month=prev_month,
        )
    except Budget.DoesNotExist:
        return 0

    if not previous_budget.allow_carry_over:
        return 0

    previous_transactions = Transaction.objects.filter(
        user=user,
        date_of_expense__year=prev_year,
        date_of_expense__month=prev_month,
    )

    previous_actual_spent = calculate_actual_spent_for_budget(
        previous_budget, previous_transactions
    )

    previous_net_transfers = calculate_net_transfers_for_budget(previous_budget)

    carry_over_amount = (
        previous_budget.amount_in_cents
        + previous_budget.carried_over_amount_in_cents
        + previous_net_transfers
        - previous_actual_spent
    )

    return max(0, carry_over_amount)


def calculate_net_transfers_for_budget(budget: Budget) -> int:
    incoming = InternalTransfer.objects.filter(destination_budget=budget).aggregate(
        total=Sum("amount_in_cents")
    )["total"]

    outgoing = InternalTransfer.objects.filter(source_budget=budget).aggregate(
        total=Sum("amount_in_cents")
    )["total"]

    return (incoming or 0) - (outgoing or 0)


def create_budget_line_items_for_type(
    transaction_type: TransactionType,
    budgets: QuerySet[Budget],
    transactions: QuerySet[Transaction],
    user: User,
    year: int,
    month: int,
) -> list[dict]:
    type_budgets = budgets.filter(type=transaction_type.name)
    budget_items = []

    for budget in type_budgets:
        actual_spent_cents = calculate_actual_spent_for_budget(budget, transactions)
        carried_over_cents = calculate_carry_over_for_budget(
            user, budget.category, budget.type, year, month
        )
        net_transfer_cents = calculate_net_transfers_for_budget(budget)

        line_item = BudgetLineItem(
            budget, actual_spent_cents, carried_over_cents, net_transfer_cents
        )
        budget_items.append(line_item.to_dict())

    return budget_items


def calculate_totals_for_budget_items(budget_items: list[dict]) -> dict:
    total_expected = sum(item["expected"] for item in budget_items)
    total_actual = sum(item["actual"] for item in budget_items)
    total_carried_over = sum(item["carried_over"] for item in budget_items)
    total_net_transfers = sum(item["net_transfers"] for item in budget_items)
    total_available = sum(item["available"] for item in budget_items)
    total_remaining = sum(item["remaining"] for item in budget_items)
    total_true_remaining = sum(item["true_remaining"] for item in budget_items)

    return {
        "expected": total_expected,
        "actual": total_actual,
        "carried_over": total_carried_over,
        "net_transfers": total_net_transfers,
        "available": total_available,
        "remaining": total_remaining,
        "true_remaining": total_true_remaining,
    }


def group_budgets_with_actuals(
    budgets: QuerySet[Budget],
    transactions: QuerySet[Transaction],
    user: User,
    year: int,
    month: int,
) -> dict[str, list[dict]]:
    budget_groups = {}

    for transaction_type in TransactionType:
        budget_groups[transaction_type.value] = create_budget_line_items_for_type(
            transaction_type, budgets, transactions, user, year, month
        )

    return budget_groups


def calculate_unallocated_income(budgets: QuerySet[Budget]) -> dict:
    total_income_cents = budgets.filter(type=TransactionType.INCOME.name).aggregate(
        total=Sum("amount_in_cents")
    )["total"]

    total_income = Decimal(total_income_cents or 0) / 100

    budget_types_to_exclude = [TransactionType.INCOME.name]
    total_allocated_cents = budgets.exclude(type__in=budget_types_to_exclude).aggregate(
        total=Sum("amount_in_cents")
    )["total"]

    total_allocated = Decimal(total_allocated_cents or 0) / 100
    unallocated = total_income - total_allocated

    percent_allocated = (
        float((total_allocated / total_income * 100)) if total_income > 0 else 0.0
    )

    return {
        "total_income": total_income,
        "total_allocated": total_allocated,
        "unallocated": unallocated,
        "percent_allocated": percent_allocated,
    }


def calculate_budget_distribution(budgets: QuerySet[Budget]) -> dict:
    distribution = {}

    budget_types = [
        TransactionType.NEED,
        TransactionType.WANT,
        TransactionType.DEBTS,
        TransactionType.SAVINGS,
        TransactionType.INVESTING,
    ]

    for budget_type in budget_types:
        total = budgets.filter(type=budget_type.name).aggregate(
            total=Sum("amount_in_cents")
        )["total"]

        total_dollars = Decimal(total or 0) / 100

        if total_dollars > 0:
            distribution[budget_type.value] = total_dollars

    return distribution
