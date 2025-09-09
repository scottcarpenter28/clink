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
from finance.models.income_or_expense import IncomeOrExpense


class TestUtilityFunctions(TestCase):
    """Test utility functions in dashboard_utils"""

    @patch('finance.utilities.dashboard_utils.timezone')
    def test_get_current_month_year(self, mock_timezone):
        """Test get_current_month_year returns current month and year"""
        mock_now = Mock()
        mock_now.month = 6
        mock_now.year = 2024
        mock_timezone.now.return_value = mock_now

        month, year = get_current_month_year()

        self.assertEqual(month, 6)
        self.assertEqual(year, 2024)
        mock_timezone.now.assert_called_once()

    @patch('finance.utilities.dashboard_utils.timezone')
    def test_get_current_month_year_january(self, mock_timezone):
        """Test get_current_month_year for January"""
        mock_now = Mock()
        mock_now.month = 1
        mock_now.year = 2024
        mock_timezone.now.return_value = mock_now

        month, year = get_current_month_year()

        self.assertEqual(month, 1)
        self.assertEqual(year, 2024)

    @patch('finance.utilities.dashboard_utils.timezone')
    def test_get_current_month_year_december(self, mock_timezone):
        """Test get_current_month_year for December"""
        mock_now = Mock()
        mock_now.month = 12
        mock_now.year = 2023
        mock_timezone.now.return_value = mock_now

        month, year = get_current_month_year()

        self.assertEqual(month, 12)
        self.assertEqual(year, 2023)

    def test_calculate_total_amount_empty_queryset(self):
        """Test calculate_total_amount with empty queryset"""
        mock_queryset = Mock(spec=QuerySet)
        mock_queryset.__iter__ = Mock(return_value=iter([]))

        total = calculate_total_amount(mock_queryset)

        self.assertEqual(total, 0.0)

    def test_calculate_total_amount_single_transaction(self):
        """Test calculate_total_amount with single transaction"""
        mock_transaction = Mock()
        mock_transaction.amount = 100.50

        mock_queryset = Mock(spec=QuerySet)
        mock_queryset.__iter__ = Mock(return_value=iter([mock_transaction]))

        total = calculate_total_amount(mock_queryset)

        self.assertEqual(total, 100.50)

    def test_calculate_total_amount_multiple_transactions(self):
        """Test calculate_total_amount with multiple transactions"""
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

    def test_calculate_total_amount_zero_amounts(self):
        """Test calculate_total_amount with zero amounts"""
        mock_transaction1 = Mock()
        mock_transaction1.amount = 0.0
        mock_transaction2 = Mock()
        mock_transaction2.amount = 0.0

        mock_queryset = Mock(spec=QuerySet)
        mock_queryset.__iter__ = Mock(return_value=iter([mock_transaction1, mock_transaction2]))

        total = calculate_total_amount(mock_queryset)

        self.assertEqual(total, 0.0)

    def test_format_month_year_january(self):
        """Test format_month_year for January"""
        formatted = format_month_year(1, 2024)
        self.assertEqual(formatted, 'January 2024')

    def test_format_month_year_december(self):
        """Test format_month_year for December"""
        formatted = format_month_year(12, 2023)
        self.assertEqual(formatted, 'December 2023')

    def test_format_month_year_june(self):
        """Test format_month_year for June"""
        formatted = format_month_year(6, 2024)
        self.assertEqual(formatted, 'June 2024')

    def test_format_month_year_february_leap_year(self):
        """Test format_month_year for February in leap year"""
        formatted = format_month_year(2, 2024)
        self.assertEqual(formatted, 'February 2024')


class TestMonthlyDashboard(TestCase):
    """Test MonthlyDashboard Pydantic model"""

    def setUp(self):
        # Create proper QuerySet mocks that pass isinstance checks
        self.mock_income_queryset = Mock()
        self.mock_income_queryset.__class__ = QuerySet
        self.mock_expense_queryset = Mock()
        self.mock_expense_queryset.__class__ = QuerySet

    def test_monthly_dashboard_creation(self):
        """Test creating a MonthlyDashboard instance"""
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

    def test_monthly_dashboard_negative_net_income(self):
        """Test MonthlyDashboard with negative net income"""
        dashboard = MonthlyDashboard(
            monthly_income=self.mock_income_queryset,
            monthly_expenses=self.mock_expense_queryset,
            total_income=500.00,
            total_expenses=800.00,
            net_income=-300.00,
            current_month='July 2024'
        )

        self.assertEqual(dashboard.net_income, -300.00)

    def test_monthly_dashboard_zero_values(self):
        """Test MonthlyDashboard with zero values"""
        dashboard = MonthlyDashboard(
            monthly_income=self.mock_income_queryset,
            monthly_expenses=self.mock_expense_queryset,
            total_income=0.0,
            total_expenses=0.0,
            net_income=0.0,
            current_month='January 2024'
        )

        self.assertEqual(dashboard.total_income, 0.0)
        self.assertEqual(dashboard.total_expenses, 0.0)
        self.assertEqual(dashboard.net_income, 0.0)

    def test_monthly_dashboard_arbitrary_types_allowed(self):
        """Test that arbitrary types are allowed for QuerySet fields"""
        # Create proper QuerySet mocks
        mock_income = Mock()
        mock_income.__class__ = QuerySet
        mock_expense = Mock()
        mock_expense.__class__ = QuerySet

        # This should not raise a validation error
        dashboard = MonthlyDashboard(
            monthly_income=mock_income,
            monthly_expenses=mock_expense,
            total_income=100.0,
            total_expenses=50.0,
            net_income=50.0,
            current_month='Test Month'
        )
        self.assertIsNotNone(dashboard)


class TestMonthlyTransactionUtils(TestCase):
    """Test MonthlyTransactionUtils class"""

    def setUp(self):
        self.mock_user_accounts = Mock()
        self.mock_user_accounts.__class__ = QuerySet

    @patch('finance.utilities.dashboard_utils.get_current_month_year')
    def test_init_with_no_month_year(self, mock_get_current_month_year):
        """Test initialization without providing month and year"""
        mock_get_current_month_year.return_value = (6, 2024)

        utils = MonthlyTransactionUtils(self.mock_user_accounts)

        self.assertEqual(utils.user_accounts, self.mock_user_accounts)
        self.assertEqual(utils.month, 6)
        self.assertEqual(utils.year, 2024)
        mock_get_current_month_year.assert_called_once()

    @patch('finance.utilities.dashboard_utils.get_current_month_year')
    def test_init_with_month_year_provided(self, mock_get_current_month_year):
        """Test initialization with provided month and year"""
        utils = MonthlyTransactionUtils(self.mock_user_accounts, month=3, year=2023)

        self.assertEqual(utils.user_accounts, self.mock_user_accounts)
        self.assertEqual(utils.month, 3)
        self.assertEqual(utils.year, 2023)
        # Should not call get_current_month_year when both are provided
        mock_get_current_month_year.assert_not_called()

    @patch('finance.utilities.dashboard_utils.get_current_month_year')
    def test_init_with_only_month_provided(self, mock_get_current_month_year):
        """Test initialization with only month provided"""
        mock_get_current_month_year.return_value = (6, 2024)

        utils = MonthlyTransactionUtils(self.mock_user_accounts, month=5)

        self.assertEqual(utils.month, 6)  # Should use current month/year
        self.assertEqual(utils.year, 2024)
        mock_get_current_month_year.assert_called_once()

    @patch('finance.utilities.dashboard_utils.get_current_month_year')
    def test_init_with_only_year_provided(self, mock_get_current_month_year):
        """Test initialization with only year provided"""
        mock_get_current_month_year.return_value = (6, 2024)

        utils = MonthlyTransactionUtils(self.mock_user_accounts, year=2023)

        self.assertEqual(utils.month, 6)  # Should use current month/year
        self.assertEqual(utils.year, 2024)
        mock_get_current_month_year.assert_called_once()

    @patch('finance.utilities.dashboard_utils.IncomeOrExpense')
    def test_get_monthly_transactions_by_type_income(self, mock_income_or_expense):
        """Test private method __get_monthly_transactions_by_type for income"""
        mock_queryset = Mock()
        mock_income_or_expense.objects.filter.return_value.select_related.return_value.order_by.return_value = mock_queryset

        utils = MonthlyTransactionUtils(self.mock_user_accounts, month=6, year=2024)
        result = utils._MonthlyTransactionUtils__get_monthly_transactions_by_type('income')

        # Verify the filter chain was called correctly
        mock_income_or_expense.objects.filter.assert_called_once_with(
            account__in=self.mock_user_accounts,
            category__category_type='income',
            created__month=6,
            created__year=2024
        )
        mock_income_or_expense.objects.filter.return_value.select_related.assert_called_once_with('category', 'account')
        mock_income_or_expense.objects.filter.return_value.select_related.return_value.order_by.assert_called_once_with('-created')

        self.assertEqual(result, mock_queryset)

    @patch('finance.utilities.dashboard_utils.IncomeOrExpense')
    def test_get_monthly_transactions_by_type_expense(self, mock_income_or_expense):
        """Test private method __get_monthly_transactions_by_type for expense"""
        mock_queryset = Mock()
        mock_income_or_expense.objects.filter.return_value.select_related.return_value.order_by.return_value = mock_queryset

        utils = MonthlyTransactionUtils(self.mock_user_accounts, month=12, year=2023)
        result = utils._MonthlyTransactionUtils__get_monthly_transactions_by_type('expense')

        mock_income_or_expense.objects.filter.assert_called_once_with(
            account__in=self.mock_user_accounts,
            category__category_type='expense',
            created__month=12,
            created__year=2023
        )

        self.assertEqual(result, mock_queryset)

    def test_get_monthly_income(self):
        """Test get_monthly_income method"""
        utils = MonthlyTransactionUtils(self.mock_user_accounts, month=6, year=2024)

        with patch.object(utils, '_MonthlyTransactionUtils__get_monthly_transactions_by_type') as mock_get_transactions:
            mock_queryset = Mock()
            mock_get_transactions.return_value = mock_queryset

            result = utils.get_monthly_income()

            mock_get_transactions.assert_called_once_with('income')
            self.assertEqual(result, mock_queryset)

    def test_get_monthly_expenses(self):
        """Test get_monthly_expenses method"""
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
        """Test get_months_dashboard method"""
        # Setup mocks
        mock_income_queryset = Mock()
        mock_income_queryset.__class__ = QuerySet
        mock_expense_queryset = Mock()
        mock_expense_queryset.__class__ = QuerySet
        mock_format_month_year.return_value = 'June 2024'
        mock_calculate_total_amount.side_effect = [1500.00, 800.50]  # income, then expenses

        utils = MonthlyTransactionUtils(self.mock_user_accounts, month=6, year=2024)

        with patch.object(utils, 'get_monthly_income', return_value=mock_income_queryset) as mock_get_income:
            with patch.object(utils, 'get_monthly_expenses', return_value=mock_expense_queryset) as mock_get_expenses:
                result = utils.get_months_dashboard()

                # Verify method calls
                mock_get_income.assert_called_once()
                mock_get_expenses.assert_called_once()
                mock_format_month_year.assert_called_once_with(6, 2024)

                # Verify calculate_total_amount was called for both querysets
                self.assertEqual(mock_calculate_total_amount.call_count, 2)
                mock_calculate_total_amount.assert_any_call(mock_income_queryset)
                mock_calculate_total_amount.assert_any_call(mock_expense_queryset)

                # Verify the returned dashboard
                self.assertIsInstance(result, MonthlyDashboard)
                self.assertEqual(result.monthly_income, mock_income_queryset)
                self.assertEqual(result.monthly_expenses, mock_expense_queryset)
                self.assertEqual(result.total_income, 1500.00)
                self.assertEqual(result.total_expenses, 800.50)
                self.assertEqual(result.net_income, 699.50)  # 1500 - 800.50
                self.assertEqual(result.current_month, 'June 2024')

    @patch('finance.utilities.dashboard_utils.calculate_total_amount')
    @patch('finance.utilities.dashboard_utils.format_month_year')
    def test_get_months_dashboard_negative_net_income(self, mock_format_month_year, mock_calculate_total_amount):
        """Test get_months_dashboard with expenses higher than income"""
        mock_income_queryset = Mock()
        mock_income_queryset.__class__ = QuerySet
        mock_expense_queryset = Mock()
        mock_expense_queryset.__class__ = QuerySet
        mock_format_month_year.return_value = 'July 2024'
        mock_calculate_total_amount.side_effect = [500.00, 800.00]  # income lower than expenses

        utils = MonthlyTransactionUtils(self.mock_user_accounts, month=7, year=2024)

        with patch.object(utils, 'get_monthly_income', return_value=mock_income_queryset):
            with patch.object(utils, 'get_monthly_expenses', return_value=mock_expense_queryset):
                result = utils.get_months_dashboard()

                self.assertEqual(result.total_income, 500.00)
                self.assertEqual(result.total_expenses, 800.00)
                self.assertEqual(result.net_income, -300.00)  # Negative net income

    @patch('finance.utilities.dashboard_utils.calculate_total_amount')
    @patch('finance.utilities.dashboard_utils.format_month_year')
    def test_get_months_dashboard_zero_amounts(self, mock_format_month_year, mock_calculate_total_amount):
        """Test get_months_dashboard with zero amounts"""
        mock_income_queryset = Mock()
        mock_income_queryset.__class__ = QuerySet
        mock_expense_queryset = Mock()
        mock_expense_queryset.__class__ = QuerySet
        mock_format_month_year.return_value = 'January 2024'
        mock_calculate_total_amount.side_effect = [0.0, 0.0]  # No income or expenses

        utils = MonthlyTransactionUtils(self.mock_user_accounts, month=1, year=2024)

        with patch.object(utils, 'get_monthly_income', return_value=mock_income_queryset):
            with patch.object(utils, 'get_monthly_expenses', return_value=mock_expense_queryset):
                result = utils.get_months_dashboard()

                self.assertEqual(result.total_income, 0.0)
                self.assertEqual(result.total_expenses, 0.0)
                self.assertEqual(result.net_income, 0.0)


class TestMonthlyTransactionUtilsIntegration(TestCase):
    """Integration tests for MonthlyTransactionUtils"""

    def setUp(self):
        self.mock_user_accounts = Mock()
        self.mock_user_accounts.__class__ = QuerySet

    @patch('finance.utilities.dashboard_utils.get_current_month_year')
    @patch('finance.utilities.dashboard_utils.IncomeOrExpense')
    @patch('finance.utilities.dashboard_utils.calculate_total_amount')
    @patch('finance.utilities.dashboard_utils.format_month_year')
    def test_complete_dashboard_workflow(self, mock_format_month_year, mock_calculate_total_amount,
                                       mock_income_or_expense, mock_get_current_month_year):
        """Test complete dashboard creation workflow"""
        # Setup mocks
        mock_get_current_month_year.return_value = (6, 2024)
        mock_format_month_year.return_value = 'June 2024'
        mock_calculate_total_amount.side_effect = [2000.00, 1200.00]

        mock_income_queryset = Mock()
        mock_income_queryset.__class__ = QuerySet
        mock_expense_queryset = Mock()
        mock_expense_queryset.__class__ = QuerySet
        mock_income_or_expense.objects.filter.return_value.select_related.return_value.order_by.return_value = Mock()

        # Create utils instance
        utils = MonthlyTransactionUtils(self.mock_user_accounts)

        # Mock the methods to return our test querysets
        with patch.object(utils, 'get_monthly_income', return_value=mock_income_queryset):
            with patch.object(utils, 'get_monthly_expenses', return_value=mock_expense_queryset):
                dashboard = utils.get_months_dashboard()

                # Verify initialization used current month/year
                self.assertEqual(utils.month, 6)
                self.assertEqual(utils.year, 2024)

                # Verify dashboard creation
                self.assertIsInstance(dashboard, MonthlyDashboard)
                self.assertEqual(dashboard.total_income, 2000.00)
                self.assertEqual(dashboard.total_expenses, 1200.00)
                self.assertEqual(dashboard.net_income, 800.00)
                self.assertEqual(dashboard.current_month, 'June 2024')

    def test_manual_month_year_workflow(self):
        """Test workflow with manually specified month and year"""
        with patch('finance.utilities.dashboard_utils.get_current_month_year') as mock_get_current:
            # Create utils with specific month/year
            utils = MonthlyTransactionUtils(self.mock_user_accounts, month=3, year=2023)

            # Verify it didn't call get_current_month_year
            mock_get_current.assert_not_called()
            self.assertEqual(utils.month, 3)
            self.assertEqual(utils.year, 2023)


class TestEdgeCases(TestCase):
    """Test edge cases and boundary conditions"""

    def setUp(self):
        self.mock_user_accounts = Mock()
        self.mock_user_accounts.__class__ = QuerySet

    def test_calculate_total_amount_with_decimal_amounts(self):
        """Test calculate_total_amount with decimal precision"""
        mock_transaction1 = Mock()
        mock_transaction1.amount = 100.33
        mock_transaction2 = Mock()
        mock_transaction2.amount = 200.67
        mock_transaction3 = Mock()
        mock_transaction3.amount = 50.50

        mock_queryset = Mock(spec=QuerySet)
        mock_queryset.__iter__ = Mock(return_value=iter([mock_transaction1, mock_transaction2, mock_transaction3]))

        total = calculate_total_amount(mock_queryset)

        self.assertEqual(total, 351.50)

    def test_format_month_year_edge_months(self):
        """Test format_month_year for all months"""
        expected_months = [
            (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
            (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
            (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')
        ]

        for month_num, month_name in expected_months:
            formatted = format_month_year(month_num, 2024)
            self.assertEqual(formatted, f'{month_name} 2024')

    def test_monthly_transaction_utils_boundary_months(self):
        """Test MonthlyTransactionUtils with boundary month values"""
        # Test January (month 1)
        utils_jan = MonthlyTransactionUtils(self.mock_user_accounts, month=1, year=2024)
        self.assertEqual(utils_jan.month, 1)

        # Test December (month 12)
        utils_dec = MonthlyTransactionUtils(self.mock_user_accounts, month=12, year=2024)
        self.assertEqual(utils_dec.month, 12)

    @patch('finance.utilities.dashboard_utils.timezone')
    def test_get_current_month_year_timezone_handling(self, mock_timezone):
        """Test get_current_month_year handles timezone correctly"""
        # Mock timezone with specific datetime
        mock_now = Mock()
        mock_now.month = 11
        mock_now.year = 2024
        mock_timezone.now.return_value = mock_now

        month, year = get_current_month_year()

        # Verify timezone.now() was called (not datetime.now())
        mock_timezone.now.assert_called_once()
        self.assertEqual(month, 11)
        self.assertEqual(year, 2024)

    def test_dashboard_with_large_amounts(self):
        """Test dashboard with very large transaction amounts"""
        mock_income_queryset = Mock()
        mock_income_queryset.__class__ = QuerySet
        mock_expense_queryset = Mock()
        mock_expense_queryset.__class__ = QuerySet

        dashboard = MonthlyDashboard(
            monthly_income=mock_income_queryset,
            monthly_expenses=mock_expense_queryset,
            total_income=999999.99,
            total_expenses=500000.50,
            net_income=499999.49,
            current_month='December 2024'
        )

        self.assertEqual(dashboard.total_income, 999999.99)
        self.assertEqual(dashboard.net_income, 499999.49)

    @patch('finance.utilities.dashboard_utils.calculate_total_amount')
    def test_calculate_total_amount_called_with_correct_querysets(self, mock_calculate_total_amount):
        """Test that calculate_total_amount is called with the correct querysets in dashboard creation"""
        mock_calculate_total_amount.side_effect = [1000.0, 600.0]

        utils = MonthlyTransactionUtils(self.mock_user_accounts, month=6, year=2024)

        mock_income_queryset = Mock()
        mock_income_queryset.__class__ = QuerySet
        mock_expense_queryset = Mock()
        mock_expense_queryset.__class__ = QuerySet

        with patch.object(utils, 'get_monthly_income', return_value=mock_income_queryset):
            with patch.object(utils, 'get_monthly_expenses', return_value=mock_expense_queryset):
                with patch('finance.utilities.dashboard_utils.format_month_year', return_value='June 2024'):
                    dashboard = utils.get_months_dashboard()

                    # Verify calculate_total_amount was called with the exact querysets
                    calls = mock_calculate_total_amount.call_args_list
                    self.assertEqual(len(calls), 2)
                    self.assertEqual(calls[0][0][0], mock_income_queryset)  # First call with income queryset
                    self.assertEqual(calls[1][0][0], mock_expense_queryset)  # Second call with expense queryset
