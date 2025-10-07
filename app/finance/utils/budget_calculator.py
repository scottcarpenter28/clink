from decimal import Decimal

from django.db.models import Sum, QuerySet

from finance.models import Budget, Transaction
from finance.enums.transaction_enums import TransactionType


class BudgetLineItem:
    def __init__(self, budget: Budget, actual_spent_cents: int):
        self.id = budget.id
        self.category = budget.category
        self.expected = Decimal(str(budget.amount_dollars))
        self.actual = Decimal(actual_spent_cents) / 100
        self.remaining = self.expected - self.actual

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "category": self.category,
            "expected": self.expected,
            "actual": self.actual,
            "remaining": self.remaining,
        }


def calculate_actual_spent_for_budget(
    budget: Budget, transactions: QuerySet[Transaction]
) -> int:
    result = transactions.filter(type=budget.type, category=budget.category).aggregate(
        total=Sum("amount_in_cents")
    )["total"]
    return result or 0


def create_budget_line_items_for_type(
    transaction_type: TransactionType,
    budgets: QuerySet[Budget],
    transactions: QuerySet[Transaction],
) -> list[dict]:
    type_budgets = budgets.filter(type=transaction_type.name)
    budget_items = []

    for budget in type_budgets:
        actual_spent_cents = calculate_actual_spent_for_budget(budget, transactions)
        line_item = BudgetLineItem(budget, actual_spent_cents)
        budget_items.append(line_item.to_dict())

    return budget_items


def calculate_totals_for_budget_items(budget_items: list[dict]) -> dict:
    total_expected = sum(item["expected"] for item in budget_items)
    total_actual = sum(item["actual"] for item in budget_items)
    total_remaining = sum(item["remaining"] for item in budget_items)

    return {
        "expected": total_expected,
        "actual": total_actual,
        "remaining": total_remaining,
    }


def group_budgets_with_actuals(
    budgets: QuerySet[Budget], transactions: QuerySet[Transaction]
) -> dict[str, list[dict]]:
    budget_groups = {}

    for transaction_type in TransactionType:
        budget_groups[transaction_type.value] = create_budget_line_items_for_type(
            transaction_type, budgets, transactions
        )

    return budget_groups


def calculate_unallocated_income(
    transactions: QuerySet[Transaction], budgets: QuerySet[Budget]
) -> dict:
    from finance.utils.transaction_calculator import calculate_total_income

    total_income = calculate_total_income(transactions)

    budget_types_to_exclude = [TransactionType.INCOME.name]
    total_allocated = budgets.exclude(type__in=budget_types_to_exclude).aggregate(
        total=Sum("amount_in_cents")
    )["total"]

    total_allocated_dollars = Decimal(total_allocated or 0) / 100
    unallocated = total_income - total_allocated_dollars

    percent_allocated = (
        float((total_allocated_dollars / total_income * 100))
        if total_income > 0
        else 0.0
    )

    return {
        "total_income": total_income,
        "total_allocated": total_allocated_dollars,
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
