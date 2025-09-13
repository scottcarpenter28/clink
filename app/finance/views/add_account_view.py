from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages


@login_required(login_url='finance:login')
def add_account_view(request):
    """
    Placeholder view for adding new accounts.
    This functionality will be implemented later.
    """
    messages.info(request, "Add Account functionality is coming soon!")
    return redirect('finance:dashboard')
