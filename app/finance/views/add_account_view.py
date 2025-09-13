from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from finance.forms.account_forms import AccountForm


@login_required(login_url='finance:login')
def add_account_view(request):
    if request.method == 'POST':
        form = AccountForm(request.user, request.POST)
        if form.is_valid():
            account = form.save()
            messages.success(request, f'Account "{account.name}" has been created successfully!')
            return redirect('finance:dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AccountForm(request.user)

    return render(request, 'finance/add_account.html', {'form': form})
