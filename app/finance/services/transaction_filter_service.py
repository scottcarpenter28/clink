from typing import Any, Dict
from django.db.models import QuerySet
from django.contrib.auth.models import User

from finance.models.transaction import Transaction
from finance.models.category import Category


class TransactionFilterService:

    def filter_by_date(self, transactions: QuerySet, year: int, month: int) -> QuerySet:
        return transactions.filter(
            transaction_date__year=year,
            transaction_date__month=month
        )

    def filter_by_type(self, transactions: QuerySet, transaction_type: str) -> QuerySet:
        if transaction_type == 'all':
            return transactions

        categories = Category.objects.filter(category_type=transaction_type)
        return transactions.filter(category__in=categories)

    def filter_by_category(self, transactions: QuerySet, category_id: str) -> QuerySet:
        if category_id == 'all':
            return transactions

        return transactions.filter(category_id=category_id)

    def filter_by_account(self, transactions: QuerySet, account_uid: str) -> QuerySet:
        if account_uid == 'all':
            return transactions

        return transactions.filter(account__uid=account_uid)

    def apply_all_filters(self, user: User, filters_dict: Dict[str, Any]) -> QuerySet:
        year = filters_dict.get('year')
        month = filters_dict.get('month')
        transaction_type = filters_dict.get('type', 'all')
        category_id = filters_dict.get('category', 'all')
        account_uid = filters_dict.get('account', 'all')

        transactions = Transaction.objects.filter(
            account__owner=user
        ).select_related('category', 'account')

        transactions = self.filter_by_date(transactions, year, month)
        transactions = self.filter_by_type(transactions, transaction_type)
        transactions = self.filter_by_category(transactions, category_id)
        transactions = self.filter_by_account(transactions, account_uid)

        return transactions
