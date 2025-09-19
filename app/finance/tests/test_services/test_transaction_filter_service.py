from unittest.mock import Mock, patch
from django.test import TestCase
from django.contrib.auth.models import User

from finance.services.transaction_filter_service import TransactionFilterService
from finance.models.transaction import Transaction
from finance.models.category import Category


class TestTransactionFilterService(TestCase):

    def setUp(self):
        self.service = TransactionFilterService()
        self.user = Mock(spec=User)
        self.mock_transactions = Mock()

    def test_filter_by_date(self):
        result = self.service.filter_by_date(self.mock_transactions, 2024, 6)

        self.mock_transactions.filter.assert_called_once_with(
            transaction_date__year=2024,
            transaction_date__month=6
        )

    def test_filter_by_type_all(self):
        result = self.service.filter_by_type(self.mock_transactions, 'all')

        self.assertEqual(result, self.mock_transactions)
        self.mock_transactions.filter.assert_not_called()

    @patch('finance.services.transaction_filter_service.Category')
    def test_filter_by_type_specific(self, mock_category):
        mock_categories = Mock()
        mock_category.objects.filter.return_value = mock_categories

        result = self.service.filter_by_type(self.mock_transactions, 'income')

        mock_category.objects.filter.assert_called_once_with(category_type='income')
        self.mock_transactions.filter.assert_called_once_with(category__in=mock_categories)

    def test_filter_by_category_all(self):
        result = self.service.filter_by_category(self.mock_transactions, 'all')

        self.assertEqual(result, self.mock_transactions)
        self.mock_transactions.filter.assert_not_called()

    def test_filter_by_category_specific(self):
        result = self.service.filter_by_category(self.mock_transactions, '123')

        self.mock_transactions.filter.assert_called_once_with(category_id='123')

    def test_filter_by_account_all(self):
        result = self.service.filter_by_account(self.mock_transactions, 'all')

        self.assertEqual(result, self.mock_transactions)
        self.mock_transactions.filter.assert_not_called()

    def test_filter_by_account_specific(self):
        result = self.service.filter_by_account(self.mock_transactions, 'uuid-123')

        self.mock_transactions.filter.assert_called_once_with(account__uid='uuid-123')

    @patch('finance.services.transaction_filter_service.Transaction')
    def test_apply_all_filters(self, mock_transaction):
        mock_queryset = Mock()
        mock_transaction.objects.filter.return_value = mock_queryset
        mock_queryset.select_related.return_value = mock_queryset

        filters = {
            'year': 2024,
            'month': 6,
            'type': 'income',
            'category': '123',
            'account': 'uuid-123'
        }

        with patch.object(self.service, 'filter_by_date') as mock_date, \
             patch.object(self.service, 'filter_by_type') as mock_type, \
             patch.object(self.service, 'filter_by_category') as mock_category, \
             patch.object(self.service, 'filter_by_account') as mock_account:

            mock_date.return_value = mock_queryset
            mock_type.return_value = mock_queryset
            mock_category.return_value = mock_queryset
            mock_account.return_value = mock_queryset

            result = self.service.apply_all_filters(self.user, filters)

            mock_transaction.objects.filter.assert_called_once_with(account__owner=self.user)
            mock_date.assert_called_once_with(mock_queryset, 2024, 6)
            mock_type.assert_called_once_with(mock_queryset, 'income')
            mock_category.assert_called_once_with(mock_queryset, '123')
            mock_account.assert_called_once_with(mock_queryset, 'uuid-123')
