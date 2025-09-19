from datetime import datetime
from typing import Any, Dict

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from finance.utilities.dashboard_utils import MonthlyTransactionUtils
from finance.services.transaction_filter_service import TransactionFilterService
from finance.services.transaction_context_builder import TransactionContextBuilder


def parse_filter_parameters(request) -> Dict[str, Any]:
    """Parse filter parameters from request."""
    return {
        'year': int(request.GET.get('year', datetime.now().year)),
        'month': int(request.GET.get('month', datetime.now().month)),
        'type': request.GET.get('type', 'all'),
        'category': request.GET.get('category', 'all'),
        'account': request.GET.get('account', 'all'),
    }


@login_required
def transaction_list_view(request):
    filters = parse_filter_parameters(request)

    filter_service = TransactionFilterService()
    context_builder = TransactionContextBuilder()

    transactions = filter_service.apply_all_filters(request.user, filters)

    user_accounts = request.user.accounts.all().order_by('name')
    monthly_utils = MonthlyTransactionUtils(user_accounts, month=filters['month'], year=filters['year'])
    dashboard_data = monthly_utils.get_months_dashboard()

    context = context_builder.build_complete_context(
        request.user, transactions, filters, dashboard_data
    )

    return render(request, 'finance/transaction_list.html', context)
