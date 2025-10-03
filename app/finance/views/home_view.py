from datetime import datetime
from typing import Optional

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse

from finance.models import Budget, Transaction
from finance.utils.transaction_calculator import (
    calculate_total_income,
    calculate_total_spent,
    calculate_total_saved,
)
from finance.utils.budget_calculator import group_budgets_with_actuals


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


def build_home_context(user, year: int, month: int) -> dict:
    budgets = get_budgets_for_month(user, year, month)
    transactions = get_transactions_for_month(user, year, month)

    return {
        "year": year,
        "month": month,
        "total_income": calculate_total_income(transactions),
        "total_spent": calculate_total_spent(transactions),
        "total_saved": calculate_total_saved(transactions),
        "budget_data": group_budgets_with_actuals(budgets, transactions),
    }


@login_required
def home_view(
    request: HttpRequest, year: Optional[int] = None, month: Optional[int] = None
) -> HttpResponse:
    year, month = get_current_year_and_month(year, month)
    context = build_home_context(request.user, year, month)
    return render(request, "home.html", context)
