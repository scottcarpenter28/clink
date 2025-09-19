from typing import Dict, Any
from django.contrib.auth.models import User
from django.db.models import QuerySet

from finance.models.category import Category
from finance.utilities.constants import MONTH_NAMES
from finance.utilities.dashboard_utils import MonthlyTransactionUtils
from .date_range_service import DateRangeService


class TransactionContextBuilder:

    def __init__(self):
        self.date_service = DateRangeService()

    def build_filter_context(self, user: User, current_filters: Dict[str, Any]) -> Dict[str, Any]:
        min_date, max_date = self.date_service.get_user_transaction_date_range(user)
        years = self.date_service.generate_year_options(min_date, max_date)
        months = self.date_service.get_month_options_with_names()

        income_categories = Category.objects.filter(category_type='income').order_by('name')
        expense_categories = Category.objects.filter(category_type='expense').order_by('name')
        user_accounts = user.accounts.all().order_by('name')

        return {
            'years': years,
            'months': months,
            'income_categories': income_categories,
            'expense_categories': expense_categories,
            'accounts': user_accounts,
            'selected_year': current_filters.get('year'),
            'selected_month': current_filters.get('month'),
            'selected_type': current_filters.get('type', 'all'),
            'selected_category': current_filters.get('category', 'all'),
            'selected_account': current_filters.get('account', 'all'),
        }

    def build_transaction_context(self, transactions: QuerySet, filters: Dict[str, Any]) -> Dict[str, Any]:
        month = filters.get('month')
        return {
            'transactions': transactions,
            'month_name': MONTH_NAMES.get(month, ''),
        }

    def build_complete_context(self, user: User, transactions: QuerySet,
                             filters: Dict[str, Any], dashboard_data: Any) -> Dict[str, Any]:
        filter_context = self.build_filter_context(user, filters)
        transaction_context = self.build_transaction_context(transactions, filters)

        summary_context = {
            'total_income': dashboard_data.total_income,
            'total_expenses': dashboard_data.total_expenses,
            'net_income': dashboard_data.net_income,
        }

        return {**filter_context, **transaction_context, **summary_context}
