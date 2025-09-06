from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from finance.utilities.transaction_utils import MonthlyTransactionUtils, MonthlyDashboard


@login_required(login_url='finance:login')
def dashboard_view(request):
    account_monthly_transactions = MonthlyTransactionUtils(request.user.accounts.all())
    context: MonthlyDashboard = account_monthly_transactions.get_months_dashboard()
    return render(request, 'finance/dashboard.html', context.dict())
