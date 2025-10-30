from django.contrib.auth.models import User
from django.db.models import Sum
from django.utils import timezone
from typing import TypedDict
from finance.models.transaction import Transaction
from finance.enums import TransactionType


class TypeTotal(TypedDict):
    type: str
    total: float


class MonthlySummaryData(TypedDict):
    totals_by_type: list[TypeTotal]
    income: float
    savings: float
    investing: float
    needs: float
    wants: float
    debts: float
    total_expenses: float


def calculate_monthly_totals(user: User) -> MonthlySummaryData:
    current_date = timezone.now()

    transactions = Transaction.objects.filter(
        user=user,
        date_of_expense__year=current_date.year,
        date_of_expense__month=current_date.month,
    )

    type_totals = (
        transactions.values("type")
        .annotate(total_cents=Sum("amount_in_cents"))
        .order_by("-total_cents")
    )

    totals_dict = {tt["type"]: tt["total_cents"] / 100 for tt in type_totals}

    income = totals_dict.get(TransactionType.INCOME.name, 0.0)
    savings = totals_dict.get(TransactionType.SAVINGS.name, 0.0)
    investing = totals_dict.get(TransactionType.INVESTING.name, 0.0)
    needs = totals_dict.get(TransactionType.NEED.name, 0.0)
    wants = totals_dict.get(TransactionType.WANT.name, 0.0)
    debts = totals_dict.get(TransactionType.DEBTS.name, 0.0)

    total_expenses = savings + investing + needs + wants + debts

    totals_by_type = [
        {"type": TransactionType[type_name].value, "total": total}
        for type_name, total in totals_dict.items()
    ]

    return {
        "totals_by_type": totals_by_type,
        "income": income,
        "savings": savings,
        "investing": investing,
        "needs": needs,
        "wants": wants,
        "debts": debts,
        "total_expenses": total_expenses,
    }
