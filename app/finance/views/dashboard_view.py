from typing import List

from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from finance.utilities.dashboard_utils import MonthlyTransactionUtils, MonthlyDashboard
from finance.utilities.account_utils import get_latest_user_account_balances, CurrentAccountBalance


@login_required(login_url='finance:login')
def dashboard_view(request):
    user_accounts = request.user.accounts.all()
    account_monthly_transactions = MonthlyTransactionUtils(user_accounts)
    context: MonthlyDashboard = account_monthly_transactions.get_months_dashboard()
    account_balances: List[CurrentAccountBalance] = get_latest_user_account_balances(request.user)

    dashboard_context = context.model_dump()
    dashboard_context['account_balances'] = [balance.model_dump() for balance in account_balances]

    return render(request, 'finance/dashboard.html', dashboard_context)
