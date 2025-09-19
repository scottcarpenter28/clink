from unittest.mock import Mock, patch
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User

from finance.views.transaction_list_view import transaction_list_view, parse_filter_parameters


class TestTransactionListView(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.user = Mock(spec=User)
        self.user.accounts.all.return_value.order_by.return_value = []

    def test_parse_filter_parameters_default_values(self):
        request = self.factory.get('/transactions/')

        with patch('finance.views.transaction_list_view.datetime') as mock_datetime:
            mock_datetime.now.return_value.year = 2024
            mock_datetime.now.return_value.month = 6

            result = parse_filter_parameters(request)

            expected = {
                'year': 2024,
                'month': 6,
                'type': 'all',
                'category': 'all',
                'account': 'all',
            }

            self.assertEqual(result, expected)

    def test_parse_filter_parameters_with_values(self):
        request = self.factory.get('/transactions/?year=2023&month=3&type=income&category=123&account=uuid-456')

        result = parse_filter_parameters(request)

        expected = {
            'year': 2023,
            'month': 3,
            'type': 'income',
            'category': '123',
            'account': 'uuid-456',
        }

        self.assertEqual(result, expected)

    @patch('finance.views.transaction_list_view.render')
    @patch('finance.views.transaction_list_view.MonthlyTransactionUtils')
    @patch('finance.views.transaction_list_view.TransactionContextBuilder')
    @patch('finance.views.transaction_list_view.TransactionFilterService')
    @patch('finance.views.transaction_list_view.parse_filter_parameters')
    def test_transaction_list_view(self, mock_parse_filters, mock_filter_service_class,
                                 mock_context_builder_class, mock_monthly_utils_class, mock_render):
        request = self.factory.get('/transactions/')
        request.user = self.user

        mock_filters = {'year': 2024, 'month': 6}
        mock_parse_filters.return_value = mock_filters

        mock_filter_service = Mock()
        mock_filter_service_class.return_value = mock_filter_service
        mock_transactions = Mock()
        mock_filter_service.apply_all_filters.return_value = mock_transactions

        mock_context_builder = Mock()
        mock_context_builder_class.return_value = mock_context_builder
        mock_context = {'key': 'value'}
        mock_context_builder.build_complete_context.return_value = mock_context

        mock_monthly_utils = Mock()
        mock_monthly_utils_class.return_value = mock_monthly_utils
        mock_dashboard_data = Mock()
        mock_monthly_utils.get_months_dashboard.return_value = mock_dashboard_data

        mock_render.return_value = 'rendered_template'

        result = transaction_list_view(request)

        mock_parse_filters.assert_called_once_with(request)
        mock_filter_service.apply_all_filters.assert_called_once_with(self.user, mock_filters)
        mock_monthly_utils_class.assert_called_once_with(
            self.user.accounts.all().order_by(), month=6, year=2024
        )
        mock_context_builder.build_complete_context.assert_called_once_with(
            self.user, mock_transactions, mock_filters, mock_dashboard_data
        )
        mock_render.assert_called_once_with(request, 'finance/transaction_list.html', mock_context)
        self.assertEqual(result, 'rendered_template')
