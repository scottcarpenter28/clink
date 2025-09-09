from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse

from finance.utilities.transaction_utils import TransactionProcessor


def handle_invalid_transaction_type(request):
    messages.error(request, 'Invalid transaction type.')
    return redirect('finance:dashboard')


def handle_successful_transaction(request, processor, transaction):
    success_message = processor.get_success_message(transaction)
    messages.success(request, success_message)
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
