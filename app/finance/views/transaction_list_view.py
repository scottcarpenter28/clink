from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Q

from ..models.transaction import Transaction
from ..models.category import Category


@login_required
def transaction_list_view(request):
    year = int(request.GET.get('year', datetime.now().year))
    month = int(request.GET.get('month', datetime.now().month))
    transaction_type = request.GET.get('type', 'all')

    transactions = Transaction.objects.filter(
        account__owner=request.user,
        transaction_date__year=year,
        transaction_date__month=month
    )

    if transaction_type != 'all':
        categories = Category.objects.filter(category_type=transaction_type)
        transactions = transactions.filter(category__in=categories)

    years = range(datetime.now().year - 5, datetime.now().year + 1)
    months = range(1, 13)

    month_names = {
        1: 'January', 2: 'February', 3: 'March', 4: 'April',
        5: 'May', 6: 'June', 7: 'July', 8: 'August',
        9: 'September', 10: 'October', 11: 'November', 12: 'December'
    }

    context = {
        'transactions': transactions,
        'selected_year': year,
        'selected_month': month,
        'selected_type': transaction_type,
        'years': years,
        'months': [(i, month_names[i]) for i in months],
        'month_name': month_names[month],
    }

    return render(request, 'finance/transaction_list.html', context)
