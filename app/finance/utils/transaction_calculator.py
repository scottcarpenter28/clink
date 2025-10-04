from decimal import Decimal

from django.db.models import Sum, QuerySet

from finance.models import Transaction
from finance.enums.transaction_enums import TransactionType


def calculate_total_by_types(
    transactions: QuerySet[Transaction], types: list[TransactionType]
) -> Decimal:
    result = transactions.filter(type__in=[t.name for t in types]).aggregate(
        total=Sum("amount_in_cents")
    )["total"]
    return Decimal(result or 0) / 100


def calculate_total_income(transactions: QuerySet[Transaction]) -> Decimal:
    return calculate_total_by_types(transactions, [TransactionType.INCOME])


def calculate_total_spent(transactions: QuerySet[Transaction]) -> Decimal:
    return calculate_total_by_types(
        transactions,
        [TransactionType.NEED, TransactionType.WANT, TransactionType.DEBTS],
    )


def calculate_total_saved(transactions: QuerySet[Transaction]) -> Decimal:
    return calculate_total_by_types(
        transactions, [TransactionType.SAVINGS, TransactionType.INVESTING]
    )
