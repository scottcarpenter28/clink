from typing import List
from datetime import datetime

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from finance.utilities.dashboard_utils import MonthlyTransactionUtils, MonthlyDashboard
from finance.utilities.account_utils import get_latest_user_account_balances, CurrentAccountBalance
from finance.models import Budget
from finance.utilities.budget_utils import get_budget_summary


@login_required(login_url='finance:login')
def dashboard_view(request):
    user_accounts = request.user.accounts.all()
    account_monthly_transactions = MonthlyTransactionUtils(user_accounts)
    context: MonthlyDashboard = account_monthly_transactions.get_months_dashboard()
    account_balances: List[CurrentAccountBalance] = get_latest_user_account_balances(request.user)

    dashboard_context = context.model_dump()
    dashboard_context['account_balances'] = [balance.model_dump() for balance in account_balances]

    # Add current month budget if exists
    today = timezone.now().date()
    month_start = datetime(today.year, today.month, 1).date()
    current_budget = Budget.objects.filter(
        user=request.user,
        month=month_start,
        is_active=True
    ).first()

    dashboard_context['current_budget'] = current_budget

    if current_budget:
        # Get budget summary for dashboard
        budget_summary = get_budget_summary(current_budget)
        dashboard_context['budget_summary'] = budget_summary

    return render(request, 'finance/dashboard.html', dashboard_context)
