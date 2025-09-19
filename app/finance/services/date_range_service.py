from datetime import datetime
from typing import Tuple, List
from django.contrib.auth.models import User
from django.db.models import Min, Max

from finance.models.transaction import Transaction
from finance.utilities.constants import MONTH_NAMES


class DateRangeService:

    def get_user_transaction_date_range(self, user: User) -> Tuple[datetime, datetime]:
        date_range = Transaction.objects.filter(account__owner=user).aggregate(
            min_date=Min('transaction_date'),
            max_date=Max('transaction_date')
        )
        return date_range['min_date'], date_range['max_date']

    def generate_year_options(self, min_date: datetime, max_date: datetime) -> range:
        if min_date and max_date:
            min_year = min_date.year
            max_year = max_date.year
            return range(min_year, max_year + 1)
        else:
            current_year = datetime.now().year
            return range(current_year - 1, current_year + 1)

    def get_month_options_with_names(self) -> List[Tuple[int, str]]:
        return [(i, MONTH_NAMES[i]) for i in range(1, 13)]
