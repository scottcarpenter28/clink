from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from ..models.income_or_expense import IncomeOrExpense


@login_required(login_url='finance:login')
def dashboard_view(request):
    # Get current month and year
    now = timezone.now()
    current_month = now.month
    current_year = now.year

    # Get user's accounts
    user_accounts = request.user.accounts.all()

    # Query for income transactions this month
    monthly_income = IncomeOrExpense.objects.filter(
        account__in=user_accounts,
        category__category_type='income',
        created__month=current_month,
        created__year=current_year
    ).select_related('category', 'account').order_by('-created')

    # Query for expense transactions this month
    monthly_expenses = IncomeOrExpense.objects.filter(
        account__in=user_accounts,
        category__category_type='expense',
        created__month=current_month,
        created__year=current_year
    ).select_related('category', 'account').order_by('-created')

    # Calculate totals
    total_income = sum(transaction.amount for transaction in monthly_income)
    total_expenses = sum(transaction.amount for transaction in monthly_expenses)
    net_income = total_income - total_expenses

    context = {
        'monthly_income': monthly_income,
        'monthly_expenses': monthly_expenses,
        'total_income': total_income,
        'total_expenses': total_expenses,
        'net_income': net_income,
        'current_month': now.strftime('%B %Y'),
    }

    return render(request, 'finance/dashboard.html', context)
