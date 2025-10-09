from datetime import datetime
from typing import Optional

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse

from finance.utils.year_aggregation import (
    get_budgets_for_year,
    get_transactions_for_year,
    aggregate_by_month_and_type,
    aggregate_by_category_and_month,
)
from finance.enums.transaction_enums import TransactionType


def get_current_year() -> int:
    return datetime.now().year


def get_previous_year(year: int) -> int:
    return year - 1


def get_next_year(year: int) -> int:
    return year + 1


def build_year_review_context(user, year: int) -> dict:
    budgets = get_budgets_for_year(user, year)
    transactions = get_transactions_for_year(user, year)

    type_breakdown = aggregate_by_month_and_type(budgets, transactions)

    category_breakdowns = {}
    for transaction_type in TransactionType:
        if transaction_type != TransactionType.INCOME:
            category_breakdowns[transaction_type.value] = (
                aggregate_by_category_and_month(budgets, transactions, transaction_type)
            )

    prev_year = get_previous_year(year)
    next_year = get_next_year(year)

    return {
        "year": year,
        "prev_year": prev_year,
        "next_year": next_year,
        "type_breakdown": type_breakdown,
        "category_breakdowns": category_breakdowns,
        "has_data": budgets.exists() or transactions.exists(),
    }


@login_required
def year_review_view(request: HttpRequest, year: Optional[int] = None) -> HttpResponse:
    if year is None:
        year = get_current_year()

    context = build_year_review_context(request.user, year)
    return render(request, "year_review.html", context)
