from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from django.db.models import QuerySet

from finance.utilities.dashboard_utils import (
    get_current_month_year,
    calculate_total_amount,
    format_month_year,
    MonthlyDashboard,
    MonthlyTransactionUtils
)
from finance.models.transaction import Transaction


class TestUtilityFunctions(TestCase):

    @patch('finance.utilities.dashboard_utils.timezone')
    def test_get_current_month_year(self, mock_timezone):
        mock_now = Mock()
        mock_now.month = 6
        mock_now.year = 2024
        mock_timezone.now.return_value = mock_now

        month, year = get_current_month_year()

        self.assertEqual(month, 6)
        self.assertEqual(year, 2024)
        mock_timezone.now.assert_called_once()

    def test_calculate_total_amount_multiple_transactions(self):
        mock_transaction1 = Mock()
        mock_transaction1.amount = 100.50
        mock_transaction2 = Mock()
        mock_transaction2.amount = 75.25
        mock_transaction3 = Mock()
        mock_transaction3.amount = 200.00

        mock_queryset = Mock(spec=QuerySet)
        mock_queryset.__iter__ = Mock(return_value=iter([mock_transaction1, mock_transaction2, mock_transaction3]))

        total = calculate_total_amount(mock_queryset)

        self.assertEqual(total, 375.75)

    def test_format_month_year(self):
        formatted = format_month_year(1, 2024)
        self.assertEqual(formatted, 'January 2024')


class TestMonthlyDashboard(TestCase):
    """Test MonthlyDashboard Pydantic model"""

    def setUp(self):
        self.mock_income_queryset = Mock()
        self.mock_income_queryset.__class__ = QuerySet
        self.mock_expense_queryset = Mock()
        self.mock_expense_queryset.__class__ = QuerySet

    def test_monthly_dashboard_creation(self):
        dashboard = MonthlyDashboard(
            monthly_income=self.mock_income_queryset,
            monthly_expenses=self.mock_expense_queryset,
            total_income=1500.00,
            total_expenses=800.50,
            net_income=699.50,
            current_month='June 2024'
        )

        self.assertEqual(dashboard.monthly_income, self.mock_income_queryset)
        self.assertEqual(dashboard.monthly_expenses, self.mock_expense_queryset)
        self.assertEqual(dashboard.total_income, 1500.00)
        self.assertEqual(dashboard.total_expenses, 800.50)
        self.assertEqual(dashboard.net_income, 699.50)
        self.assertEqual(dashboard.current_month, 'June 2024')


class TestMonthlyTransactionUtils(TestCase):

    def setUp(self):
        self.mock_user_accounts = Mock()
        self.mock_user_accounts.__class__ = QuerySet

    @patch('finance.utilities.dashboard_utils.get_current_month_year')
    def test_init_with_no_month_year(self, mock_get_current_month_year):
        mock_get_current_month_year.return_value = (6, 2024)

        utils = MonthlyTransactionUtils(self.mock_user_accounts)

        self.assertEqual(utils.user_accounts, self.mock_user_accounts)
        self.assertEqual(utils.month, 6)
        self.assertEqual(utils.year, 2024)
        mock_get_current_month_year.assert_called_once()

    @patch('finance.utilities.dashboard_utils.get_current_month_year')
    def test_init_with_month_year_provided(self, mock_get_current_month_year):
        utils = MonthlyTransactionUtils(self.mock_user_accounts, month=3, year=2023)

        self.assertEqual(utils.user_accounts, self.mock_user_accounts)
        self.assertEqual(utils.month, 3)
        self.assertEqual(utils.year, 2023)
        mock_get_current_month_year.assert_not_called()

    @patch('finance.utilities.dashboard_utils.get_current_month_year')
    def test_init_with_only_month_provided(self, mock_get_current_month_year):
        mock_get_current_month_year.return_value = (6, 2024)

        utils = MonthlyTransactionUtils(self.mock_user_accounts, month=5)

        self.assertEqual(utils.month, 6)
        self.assertEqual(utils.year, 2024)
        mock_get_current_month_year.assert_called_once()

    @patch('finance.utilities.dashboard_utils.get_current_month_year')
    def test_init_with_only_year_provided(self, mock_get_current_month_year):
        mock_get_current_month_year.return_value = (6, 2024)

        utils = MonthlyTransactionUtils(self.mock_user_accounts, year=2023)

        self.assertEqual(utils.month, 6)
        self.assertEqual(utils.year, 2024)
        mock_get_current_month_year.assert_called_once()

    @patch('finance.utilities.dashboard_utils.Transaction')
    def test_get_monthly_transactions_by_type_income(self, mock_transaction):
        mock_queryset = Mock()
        mock_transaction.objects.filter.return_value.select_related.return_value.order_by.return_value = mock_queryset

        utils = MonthlyTransactionUtils(self.mock_user_accounts, month=6, year=2024)
        result = utils._MonthlyTransactionUtils__get_monthly_transactions_by_type('income')

        mock_transaction.objects.filter.assert_called_once_with(
            account__in=self.mock_user_accounts,
            category__category_type='income',
            transaction_date__month=6,
            transaction_date__year=2024
        )
        mock_transaction.objects.filter.return_value.select_related.assert_called_once_with('category', 'account')
        mock_transaction.objects.filter.return_value.select_related.return_value.order_by.assert_called_once_with('-transaction_date', '-created')

        self.assertEqual(result, mock_queryset)

    @patch('finance.utilities.dashboard_utils.Transaction')
    def test_get_monthly_transactions_by_type_expense(self, mock_transaction):
        mock_queryset = Mock()
        mock_transaction.objects.filter.return_value.select_related.return_value.order_by.return_value = mock_queryset

        utils = MonthlyTransactionUtils(self.mock_user_accounts, month=12, year=2023)
        result = utils._MonthlyTransactionUtils__get_monthly_transactions_by_type('expense')

        mock_transaction.objects.filter.assert_called_once_with(
            account__in=self.mock_user_accounts,
            category__category_type='expense',
            transaction_date__month=12,
            transaction_date__year=2023
        )

        self.assertEqual(result, mock_queryset)

    def test_get_monthly_income(self):
        utils = MonthlyTransactionUtils(self.mock_user_accounts, month=6, year=2024)

        with patch.object(utils, '_MonthlyTransactionUtils__get_monthly_transactions_by_type') as mock_get_transactions:
            mock_queryset = Mock()
            mock_get_transactions.return_value = mock_queryset

            result = utils.get_monthly_income()

            mock_get_transactions.assert_called_once_with('income')
            self.assertEqual(result, mock_queryset)

    def test_get_monthly_expenses(self):
        utils = MonthlyTransactionUtils(self.mock_user_accounts, month=6, year=2024)

        with patch.object(utils, '_MonthlyTransactionUtils__get_monthly_transactions_by_type') as mock_get_transactions:
            mock_queryset = Mock()
            mock_get_transactions.return_value = mock_queryset

            result = utils.get_monthly_expenses()

            mock_get_transactions.assert_called_once_with('expense')
            self.assertEqual(result, mock_queryset)

    @patch('finance.utilities.dashboard_utils.calculate_total_amount')
    @patch('finance.utilities.dashboard_utils.format_month_year')
    def test_get_months_dashboard(self, mock_format_month_year, mock_calculate_total_amount):
        mock_income_queryset = Mock()
        mock_income_queryset.__class__ = QuerySet
        mock_expense_queryset = Mock()
        mock_expense_queryset.__class__ = QuerySet
        mock_format_month_year.return_value = 'June 2024'
        mock_calculate_total_amount.side_effect = [1500.00, 800.50]

        utils = MonthlyTransactionUtils(self.mock_user_accounts, month=6, year=2024)

        with patch.object(utils, 'get_monthly_income', return_value=mock_income_queryset) as mock_get_income:
            with patch.object(utils, 'get_monthly_expenses', return_value=mock_expense_queryset) as mock_get_expenses:
                result = utils.get_months_dashboard()

                mock_get_income.assert_called_once()
                mock_get_expenses.assert_called_once()
                mock_format_month_year.assert_called_once_with(6, 2024)

                self.assertEqual(mock_calculate_total_amount.call_count, 2)
                mock_calculate_total_amount.assert_any_call(mock_income_queryset)
                mock_calculate_total_amount.assert_any_call(mock_expense_queryset)

                self.assertIsInstance(result, MonthlyDashboard)
                self.assertEqual(result.monthly_income, mock_income_queryset)
                self.assertEqual(result.monthly_expenses, mock_expense_queryset)
                self.assertEqual(result.total_income, 1500.00)
                self.assertEqual(result.total_expenses, 800.50)
                self.assertEqual(result.net_income, 699.50)
                self.assertEqual(result.current_month, 'June 2024')

    @patch('finance.utilities.dashboard_utils.calculate_total_amount')
    @patch('finance.utilities.dashboard_utils.format_month_year')
    def test_get_months_dashboard_negative_net_income(self, mock_format_month_year, mock_calculate_total_amount):
        mock_income_queryset = Mock()
        mock_income_queryset.__class__ = QuerySet
        mock_expense_queryset = Mock()
        mock_expense_queryset.__class__ = QuerySet
        mock_format_month_year.return_value = 'July 2024'
        mock_calculate_total_amount.side_effect = [500.00, 800.00]

        utils = MonthlyTransactionUtils(self.mock_user_accounts, month=7, year=2024)

        with patch.object(utils, 'get_monthly_income', return_value=mock_income_queryset):
            with patch.object(utils, 'get_monthly_expenses', return_value=mock_expense_queryset):
                result = utils.get_months_dashboard()

                self.assertEqual(result.total_income, 500.00)
                self.assertEqual(result.total_expenses, 800.00)
                self.assertEqual(result.net_income, -300.00)


class TestMonthlyTransactionUtilsIntegration(TestCase):

    def setUp(self):
        self.mock_user_accounts = Mock()
        self.mock_user_accounts.__class__ = QuerySet

    @patch('finance.utilities.dashboard_utils.get_current_month_year')
    @patch('finance.utilities.dashboard_utils.Transaction')
    @patch('finance.utilities.dashboard_utils.calculate_total_amount')
    @patch('finance.utilities.dashboard_utils.format_month_year')
    def test_complete_dashboard_workflow(self, mock_format_month_year, mock_calculate_total_amount,
                                       mock_transaction, mock_get_current_month_year):
        mock_get_current_month_year.return_value = (6, 2024)
        mock_format_month_year.return_value = 'June 2024'
        mock_calculate_total_amount.side_effect = [2000.00, 1200.00]

        mock_income_queryset = Mock()
        mock_income_queryset.__class__ = QuerySet
        mock_expense_queryset = Mock()
        mock_expense_queryset.__class__ = QuerySet
        mock_transaction.objects.filter.return_value.select_related.return_value.order_by.return_value = Mock()

        utils = MonthlyTransactionUtils(self.mock_user_accounts)

        with patch.object(utils, 'get_monthly_income', return_value=mock_income_queryset):
            with patch.object(utils, 'get_monthly_expenses', return_value=mock_expense_queryset):
                dashboard = utils.get_months_dashboard()

                self.assertEqual(utils.month, 6)
                self.assertEqual(utils.year, 2024)

                self.assertIsInstance(dashboard, MonthlyDashboard)
                self.assertEqual(dashboard.total_income, 2000.00)
                self.assertEqual(dashboard.total_expenses, 1200.00)
                self.assertEqual(dashboard.net_income, 800.00)
                self.assertEqual(dashboard.current_month, 'June 2024')

    def test_manual_month_year_workflow(self):
        """Test workflow with manually specified month and year"""
        with patch('finance.utilities.dashboard_utils.get_current_month_year') as mock_get_current:
            utils = MonthlyTransactionUtils(self.mock_user_accounts, month=3, year=2023)

            mock_get_current.assert_not_called()
            self.assertEqual(utils.month, 3)
            self.assertEqual(utils.year, 2023)
