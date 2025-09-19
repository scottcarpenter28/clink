from unittest.mock import Mock, patch
from django.test import TestCase
from django.contrib.auth.models import User

from finance.services.transaction_context_builder import TransactionContextBuilder


class TestTransactionContextBuilder(TestCase):

    def setUp(self):
        self.builder = TransactionContextBuilder()
        self.user = Mock(spec=User)
        self.user.accounts.all.return_value.order_by.return_value = []

    @patch('finance.services.transaction_context_builder.Category')
    def test_build_filter_context(self, mock_category):
        mock_income_categories = Mock()
        mock_expense_categories = Mock()
        mock_category.objects.filter.side_effect = [mock_income_categories, mock_expense_categories]

        filters = {
            'year': 2024,
            'month': 6,
            'type': 'income',
            'category': '123',
            'account': 'uuid-123'
        }

        with patch.object(self.builder.date_service, 'get_user_transaction_date_range') as mock_date_range, \
             patch.object(self.builder.date_service, 'generate_year_options') as mock_years, \
             patch.object(self.builder.date_service, 'get_month_options_with_names') as mock_months:

            mock_date_range.return_value = (None, None)
            mock_years.return_value = range(2023, 2025)
            mock_months.return_value = [(1, 'January'), (2, 'February')]

            result = self.builder.build_filter_context(self.user, filters)

            self.assertEqual(result['selected_year'], 2024)
            self.assertEqual(result['selected_month'], 6)
            self.assertEqual(result['selected_type'], 'income')
            self.assertEqual(result['selected_category'], '123')
            self.assertEqual(result['selected_account'], 'uuid-123')
            self.assertEqual(result['income_categories'], mock_income_categories)
            self.assertEqual(result['expense_categories'], mock_expense_categories)

    @patch('finance.services.transaction_context_builder.MONTH_NAMES')
    def test_build_transaction_context(self, mock_month_names):
        mock_month_names.get.return_value = 'June'
        mock_transactions = Mock()
        filters = {'month': 6}

        result = self.builder.build_transaction_context(mock_transactions, filters)

        self.assertEqual(result['transactions'], mock_transactions)
        self.assertEqual(result['month_name'], 'June')
        mock_month_names.get.assert_called_once_with(6, '')

    def test_build_complete_context(self):
        mock_transactions = Mock()
        mock_dashboard_data = Mock()
        mock_dashboard_data.total_income = 1000.0
        mock_dashboard_data.total_expenses = 500.0
        mock_dashboard_data.net_income = 500.0

        filters = {'month': 6, 'year': 2024}

        with patch.object(self.builder, 'build_filter_context') as mock_filter_context, \
             patch.object(self.builder, 'build_transaction_context') as mock_transaction_context:

            mock_filter_context.return_value = {'filter_key': 'filter_value'}
            mock_transaction_context.return_value = {'transaction_key': 'transaction_value'}

            result = self.builder.build_complete_context(
                self.user, mock_transactions, filters, mock_dashboard_data
            )

            expected = {
                'filter_key': 'filter_value',
                'transaction_key': 'transaction_value',
                'total_income': 1000.0,
                'total_expenses': 500.0,
                'net_income': 500.0,
            }

            self.assertEqual(result, expected)
            mock_filter_context.assert_called_once_with(self.user, filters)
            mock_transaction_context.assert_called_once_with(mock_transactions, filters)
