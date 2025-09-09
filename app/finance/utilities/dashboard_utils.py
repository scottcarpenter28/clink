from typing import Optional

from django.utils import timezone
from django.db.models import QuerySet
from pydantic import BaseModel

from finance.models.income_or_expense import IncomeOrExpense


def get_current_month_year() -> tuple[int, int]:
    now = timezone.now()
    return now.month, now.year


def calculate_total_amount(transactions: QuerySet) -> float:
    return sum(transaction.amount for transaction in transactions)


def format_month_year(month: int, year: int) -> str:
    from datetime import datetime
    date_obj = datetime(year, month, 1)
    return date_obj.strftime('%B %Y')


class MonthlyDashboard(BaseModel):
    monthly_income: QuerySet
    monthly_expenses: QuerySet
    total_income: float
    total_expenses: float
    net_income: float
    current_month: str

    model_config = {
        "arbitrary_types_allowed": True
    }


class MonthlyTransactionUtils:
    def __init__(self, user_accounts: QuerySet, month: Optional[int] = None, year: Optional[int] = None):
        self.user_accounts = user_accounts

        if month is None or year is None:
            month, year = get_current_month_year()

        self.month = month
        self.year = year

    def __get_monthly_transactions_by_type(self, category_type: str) -> QuerySet:
        return IncomeOrExpense.objects.filter(
            account__in=self.user_accounts,
            category__category_type=category_type,
            created__month=self.month,
            created__year=self.year
        ).select_related('category', 'account').order_by('-created')

    def get_monthly_income(self) -> QuerySet:
        return self.__get_monthly_transactions_by_type('income')

    def get_monthly_expenses(self) -> QuerySet:
        return self.__get_monthly_transactions_by_type('expense')

    def get_months_dashboard(self) -> MonthlyDashboard:
        monthly_income = self.get_monthly_income()
        monthly_expenses = self.get_monthly_expenses()

        total_income = calculate_total_amount(monthly_income)
        total_expenses = calculate_total_amount(monthly_expenses)
        net_income = total_income - total_expenses

        return MonthlyDashboard(
            monthly_income=monthly_income,
            monthly_expenses=monthly_expenses,
            total_income=total_income,
            total_expenses=total_expenses,
            net_income=net_income,
            current_month=format_month_year(self.month, self.year)
        )
