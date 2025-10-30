from django.contrib.auth.models import User
from django.db.models import Sum
from django.utils import timezone
from typing import TypedDict
from finance.models.transaction import Transaction


class CategoryTotal(TypedDict):
    category: str
    total: float


class YearlySummaryData(TypedDict):
    totals_by_category: list[CategoryTotal]
    grand_total: float
    total_income: float
    total_expenses: float
    net_income: float


def calculate_yearly_totals(user: User) -> YearlySummaryData:
    current_date = timezone.now()

    transactions = Transaction.objects.filter(
        user=user,
        date_of_expense__year=current_date.year,
    )

    category_totals = (
        transactions.values("category", "type")
        .annotate(total_cents=Sum("amount_in_cents"))
        .order_by("-total_cents")
    )

    totals_by_category = [
        {
            "category": f"{ct['category']} ({ct['type']})",
            "total": ct["total_cents"] / 100,
        }
        for ct in category_totals
    ]

    income_transactions = transactions.filter(type="INCOME")
    expense_transactions = transactions.exclude(type="INCOME")

    total_income = (
        income_transactions.aggregate(total=Sum("amount_in_cents"))["total"] or 0
    ) / 100

    total_expenses = (
        expense_transactions.aggregate(total=Sum("amount_in_cents"))["total"] or 0
    ) / 100

    grand_total = total_income + total_expenses
    net_income = total_income - total_expenses

    return {
        "totals_by_category": totals_by_category,
        "grand_total": grand_total,
        "total_income": total_income,
        "total_expenses": total_expenses,
        "net_income": net_income,
    }
