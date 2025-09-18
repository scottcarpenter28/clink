from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Min, Max

from finance.models.transaction import Transaction
from finance.models.category import Category
from finance.models.account import Account
from finance.utilities.dashboard_utils import MonthlyTransactionUtils

# Todo: Clean this code up (my god did the AI write horrible stuff, albeit working.)
@login_required
def transaction_list_view(request):
    year = int(request.GET.get('year', datetime.now().year))
    month = int(request.GET.get('month', datetime.now().month))
    transaction_type = request.GET.get('type', 'all')
    category_id = request.GET.get('category', 'all')
    account_uid = request.GET.get('account', 'all')

    # Base query for transactions
    transactions = Transaction.objects.filter(
        account__owner=request.user,
        transaction_date__year=year,
        transaction_date__month=month
    ).select_related('category', 'account')

    # Apply transaction type filter
    if transaction_type != 'all':
        categories = Category.objects.filter(category_type=transaction_type)
        transactions = transactions.filter(category__in=categories)

    # Apply category filter if selected
    if category_id != 'all':
        transactions = transactions.filter(category_id=category_id)

    # Apply account filter if selected
    if account_uid != 'all':
        transactions = transactions.filter(account__uid=account_uid)

    # Get transaction date range for this user
    date_range = Transaction.objects.filter(account__owner=request.user).aggregate(
        min_date=Min('transaction_date'),
        max_date=Max('transaction_date')
    )

    # Generate year options based on user's transaction history
    if date_range['min_date'] and date_range['max_date']:
        min_year = date_range['min_date'].year
        max_year = date_range['max_date'].year
        years = range(min_year, max_year + 1)
    else:
        # If no transactions yet, use current year
        current_year = datetime.now().year
        years = range(current_year - 1, current_year + 1)

    months = range(1, 13)

    month_names = {
        1: 'January', 2: 'February', 3: 'March', 4: 'April',
        5: 'May', 6: 'June', 7: 'July', 8: 'August',
        9: 'September', 10: 'October', 11: 'November', 12: 'December'
    }

    # Get all categories for this user
    income_categories = Category.objects.filter(category_type='income').order_by('name')
    expense_categories = Category.objects.filter(category_type='expense').order_by('name')

    # Get all accounts for this user
    user_accounts = request.user.accounts.all().order_by('name')

    # Calculate summary totals for the selected month
    monthly_utils = MonthlyTransactionUtils(user_accounts, month=month, year=year)
    dashboard_data = monthly_utils.get_months_dashboard()

    context = {
        'transactions': transactions,
        'selected_year': year,
        'selected_month': month,
        'selected_type': transaction_type,
        'selected_category': category_id,
        'selected_account': account_uid,
        'years': years,
        'months': [(i, month_names[i]) for i in months],
        'month_name': month_names[month],
        'income_categories': income_categories,
        'expense_categories': expense_categories,
        'accounts': user_accounts,
        'total_income': dashboard_data.total_income,
        'total_expenses': dashboard_data.total_expenses,
        'net_income': dashboard_data.net_income,
    }

    return render(request, 'finance/transaction_list.html', context)
