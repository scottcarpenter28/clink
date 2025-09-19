from unittest.mock import Mock, patch
from datetime import datetime
from django.test import TestCase
from django.contrib.auth.models import User

from finance.services.date_range_service import DateRangeService


class TestDateRangeService(TestCase):

    def setUp(self):
        self.service = DateRangeService()
        self.user = Mock(spec=User)

    @patch('finance.services.date_range_service.Transaction')
    def test_get_user_transaction_date_range(self, mock_transaction):
        mock_date_range = {
            'min_date': datetime(2023, 1, 1),
            'max_date': datetime(2024, 12, 31)
        }
        mock_transaction.objects.filter.return_value.aggregate.return_value = mock_date_range

        min_date, max_date = self.service.get_user_transaction_date_range(self.user)

        mock_transaction.objects.filter.assert_called_once_with(account__owner=self.user)
        self.assertEqual(min_date, datetime(2023, 1, 1))
        self.assertEqual(max_date, datetime(2024, 12, 31))

    def test_generate_year_options_with_dates(self):
        min_date = datetime(2022, 5, 15)
        max_date = datetime(2024, 8, 20)

        result = self.service.generate_year_options(min_date, max_date)

        self.assertEqual(list(result), [2022, 2023, 2024])

    @patch('finance.services.date_range_service.datetime')
    def test_generate_year_options_no_dates(self, mock_datetime):
        mock_datetime.now.return_value.year = 2024

        result = self.service.generate_year_options(None, None)

        self.assertEqual(list(result), [2023, 2024])

    @patch('finance.services.date_range_service.MONTH_NAMES')
    def test_get_month_options_with_names(self, mock_month_names):
        mock_month_names.__getitem__.side_effect = lambda x: f'Month{x}'

        result = self.service.get_month_options_with_names()

        expected = [(i, f'Month{i}') for i in range(1, 13)]
        self.assertEqual(result, expected)
