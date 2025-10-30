from django.contrib.auth.models import User
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
from typing import TypedDict
from finance.models.transaction import Transaction
from finance.models.budget import Budget


class CategoryTotal(TypedDict):
    category: str
    total: float


class BudgetRemaining(TypedDict):
    category: str
    budget: float
    spent: float
    remaining: float


class WeeklySummaryData(TypedDict):
    totals_by_category: list[CategoryTotal]
    remaining_budgets: list[BudgetRemaining]
    grand_total: float


def calculate_weekly_totals(user: User) -> WeeklySummaryData:
    seven_days_ago = timezone.now() - timedelta(days=7)

    transactions = Transaction.objects.filter(
        user=user, date_of_expense__gte=seven_days_ago.date()
    )

    category_totals = (
        transactions.values("category")
        .annotate(total_cents=Sum("amount_in_cents"))
        .order_by("-total_cents")
    )

    totals_by_category = [
        {"category": ct["category"], "total": ct["total_cents"] / 100}
        for ct in category_totals
    ]

    grand_total = sum(ct["total"] for ct in totals_by_category)

    remaining_budgets = calculate_remaining_budgets(user, seven_days_ago)

    return {
        "totals_by_category": totals_by_category,
        "remaining_budgets": remaining_budgets,
        "grand_total": grand_total,
    }


def calculate_remaining_budgets(
    user: User, seven_days_ago: timezone.datetime
) -> list[BudgetRemaining]:
    current_date = timezone.now()

    budgets = Budget.objects.filter(
        user=user,
        budget_year=current_date.year,
        budget_month=current_date.month,
    )

    remaining_budgets = []

    for budget in budgets:
        spent_cents = (
            Transaction.objects.filter(
                user=user,
                category=budget.category,
                type=budget.type,
                date_of_expense__year=current_date.year,
                date_of_expense__month=current_date.month,
            ).aggregate(total=Sum("amount_in_cents"))["total"]
            or 0
        )

        budget_amount = budget.amount_in_cents + budget.carried_over_amount_in_cents
        spent_amount = spent_cents / 100
        budget_dollars = budget_amount / 100
        remaining = budget_dollars - spent_amount

        remaining_budgets.append(
            {
                "category": budget.category,
                "budget": budget_dollars,
                "spent": spent_amount,
                "remaining": remaining,
            }
        )

    return sorted(remaining_budgets, key=lambda x: x["remaining"])
