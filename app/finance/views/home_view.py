from datetime import datetime
from typing import Optional
import calendar

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse

from finance.models import Budget, Transaction
from finance.utils.transaction_calculator import (
    calculate_total_income,
    calculate_total_spent,
    calculate_total_saved,
)
from finance.utils.budget_calculator import (
    group_budgets_with_actuals,
    calculate_totals_for_budget_items,
    calculate_unallocated_income,
    calculate_budget_distribution,
    process_month_end_carry_over,
)


def get_current_year_and_month(
    year: Optional[int], month: Optional[int]
) -> tuple[int, int]:
    now = datetime.now()
    return year or now.year, month or now.month


def get_budgets_for_month(user, year: int, month: int):
    return Budget.objects.filter(user=user, budget_year=year, budget_month=month)


def get_transactions_for_month(user, year: int, month: int):
    return Transaction.objects.filter(
        user=user, date_of_expense__year=year, date_of_expense__month=month
    )


def get_previous_month(year: int, month: int) -> tuple[int, int]:
    if month == 1:
        return year - 1, 12
    return year, month - 1


def get_next_month(year: int, month: int) -> tuple[int, int]:
    if month == 12:
        return year + 1, 1
    return year, month + 1


def build_home_context(user, year: int, month: int) -> dict:
    prev_year, prev_month = get_previous_month(year, month)
    process_month_end_carry_over(user, prev_year, prev_month)

    budgets = get_budgets_for_month(user, year, month)
    transactions = get_transactions_for_month(user, year, month)

    next_year, next_month = get_next_month(year, month)
    month_name = calendar.month_name[month]

    budget_data = group_budgets_with_actuals(budgets, transactions, user, year, month)
    budget_totals = {
        budget_type: calculate_totals_for_budget_items(items)
        for budget_type, items in budget_data.items()
    }

    unallocated_income_data = calculate_unallocated_income(budgets)
    budget_distribution_data = calculate_budget_distribution(budgets)

    return {
        "year": year,
        "month": month,
        "month_name": month_name,
        "prev_year": prev_year,
        "prev_month": prev_month,
        "next_year": next_year,
        "next_month": next_month,
        "total_income": calculate_total_income(transactions),
        "total_spent": calculate_total_spent(transactions),
        "total_saved": calculate_total_saved(transactions),
        "budget_data": budget_data,
        "budget_totals": budget_totals,
        "transactions": transactions,
        "unallocated_income_data": unallocated_income_data,
        "budget_distribution_data": budget_distribution_data,
    }


@login_required
def home_view(
    request: HttpRequest, year: Optional[int] = None, month: Optional[int] = None
) -> HttpResponse:
    year, month = get_current_year_and_month(year, month)
    context = build_home_context(request.user, year, month)
    return render(request, "home.html", context)
