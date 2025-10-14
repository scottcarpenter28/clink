from decimal import Decimal
from typing import Any

from django.db.models import Sum, QuerySet
from django.contrib.auth.models import User

from finance.models import Budget, Transaction
from finance.enums.transaction_enums import TransactionType


def get_budgets_for_year(user: User, year: int) -> QuerySet[Budget]:
    return Budget.objects.filter(user=user, budget_year=year)


def get_transactions_for_year(user: User, year: int) -> QuerySet[Transaction]:
    return Transaction.objects.filter(user=user, date_of_expense__year=year)


def calculate_monthly_totals_for_transactions(
    transactions: QuerySet[Transaction], transaction_type: str, category: str = None
) -> list[Decimal]:
    monthly_totals = [Decimal("0.00")] * 12

    for month in range(1, 13):
        filters = {"type": transaction_type, "date_of_expense__month": month}
        if category is not None:
            filters["category"] = category

        month_transactions = transactions.filter(**filters)
        total_cents = month_transactions.aggregate(total=Sum("amount_in_cents"))[
            "total"
        ]
        monthly_totals[month - 1] = Decimal(total_cents or 0) / 100

    return monthly_totals


def add_totals_and_average(monthly_totals: list[Decimal]) -> list[Decimal]:
    year_total = sum(monthly_totals)
    non_zero_months = sum(1 for total in monthly_totals if total > 0)
    average = year_total / non_zero_months if non_zero_months > 0 else Decimal("0.00")
    return monthly_totals + [year_total, average]


def aggregate_by_month_and_type(
    budgets: QuerySet[Budget], transactions: QuerySet[Transaction]
) -> dict[str, list[Decimal]]:
    result = {}

    for transaction_type in TransactionType:
        monthly_totals = calculate_monthly_totals_for_transactions(
            transactions, transaction_type.name
        )
        result[transaction_type.value] = add_totals_and_average(monthly_totals)

    return result


def aggregate_by_category_and_month(
    budgets: QuerySet[Budget],
    transactions: QuerySet[Transaction],
    transaction_type: TransactionType,
) -> dict[str, dict[str, Any]]:
    result = {}

    type_budgets = budgets.filter(type=transaction_type.name)
    budget_categories = set(type_budgets.values_list("category", flat=True).distinct())

    type_transactions = transactions.filter(type=transaction_type.name)
    transaction_categories = set(
        type_transactions.values_list("category", flat=True).distinct()
    )

    all_categories = budget_categories.union(transaction_categories)

    for category in all_categories:
        monthly_totals = calculate_monthly_totals_for_transactions(
            transactions, transaction_type.name, category
        )

        year_total = sum(monthly_totals)
        non_zero_months = sum(1 for total in monthly_totals if total > 0)
        average = (
            year_total / non_zero_months if non_zero_months > 0 else Decimal("0.00")
        )

        result[category] = {
            "months": monthly_totals,
            "total": year_total,
            "average": average,
        }

    return result
