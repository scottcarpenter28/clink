from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from datetime import datetime

from finance.models import Budget, Category
from finance.utilities.transaction_utils import TransactionProcessor


def handle_invalid_transaction_type(request):
    messages.error(request, 'Invalid transaction type.')
    return redirect('finance:dashboard')


def handle_successful_transaction(request, processor, transaction):
    success_message = processor.get_success_message(transaction)
    messages.success(request, success_message)

    # For income transactions, check if there's a budget for this month
    if processor.transaction_type == 'income':
        # Get current month (first day of month)
        today = timezone.now().date()
        month_start = datetime(today.year, today.month, 1).date()

        # Check if a budget exists for this month
        budget_exists = Budget.objects.filter(
            user=request.user,
            month=month_start,
            is_active=True
        ).exists()

        if not budget_exists:
            # Calculate the total income for this month
            category_ids = Category.objects.filter(category_type='income').values_list('id', flat=True)
            income_amount = transaction.amount  # Start with this transaction

            # Offer budget setup with this income amount
            messages.info(
                request,
                f"Would you like to create a budget for {month_start.strftime('%B %Y')} "
                f"with your income of ${income_amount:.2f}?"
            )

            # Redirect to budget setup with pre-filled income
            session_data = {
                'setup_budget_income': income_amount,
                'setup_budget_month': month_start.isoformat()
            }
            request.session['budget_setup'] = session_data

            return redirect('finance:budget_setup')

    return redirect('finance:dashboard')


@login_required
def add_transaction_view(request, transaction_type):
    processor = TransactionProcessor(request.user, transaction_type)

    if not processor.is_valid_type():
        return handle_invalid_transaction_type(request)

    cancel_url = reverse('finance:dashboard')

    if request.method == 'POST':
        transaction, context = processor.handle_post_request(request.POST, cancel_url)

        if transaction:
            return handle_successful_transaction(request, processor, transaction)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        context = processor.handle_get_request(cancel_url)

    return render(request, 'finance/add_transaction.html', context.dict())
