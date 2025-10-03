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
    type_budgets = budgets.filter(type=transaction_type.value)
    budget_items = []

    for budget in type_budgets:
        actual_spent_cents = calculate_actual_spent_for_budget(budget, transactions)
        line_item = BudgetLineItem(budget, actual_spent_cents)
        budget_items.append(line_item.to_dict())

    return budget_items


def group_budgets_with_actuals(
    budgets: QuerySet[Budget], transactions: QuerySet[Transaction]
) -> dict[str, list[dict]]:
    budget_groups = {}

    for transaction_type in TransactionType:
        budget_groups[transaction_type.value] = create_budget_line_items_for_type(
            transaction_type, budgets, transactions
        )

    return budget_groups
