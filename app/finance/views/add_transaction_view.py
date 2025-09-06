from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from ..forms import IncomeForm, ExpenseForm


@login_required
def add_transaction_view(request, transaction_type):
    """
    View for adding income or expense transactions.

    Args:
        transaction_type (str): Either 'income' or 'expense'
    """
    if transaction_type not in ['income', 'expense']:
        messages.error(request, 'Invalid transaction type.')
        return redirect('finance:dashboard')

    # Determine which form to use
    FormClass = IncomeForm if transaction_type == 'income' else ExpenseForm

    if request.method == 'POST':
        form = FormClass(request.POST, user=request.user)
        if form.is_valid():
            transaction = form.save()
            messages.success(
                request,
                f'{transaction_type.title()} of ${transaction.amount:.2f} added successfully!'
            )
            return redirect('finance:dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = FormClass(user=request.user)

    context = {
        'form': form,
        'transaction_type': transaction_type,
        'page_title': f'Add {transaction_type.title()}',
        'submit_text': f'Add {transaction_type.title()}',
        'cancel_url': reverse('finance:dashboard'),
    }

    return render(request, 'finance/add_transaction.html', context)
