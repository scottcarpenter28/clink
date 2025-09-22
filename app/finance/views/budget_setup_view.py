from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.db import transaction
from datetime import datetime

from finance.models import Budget, BudgetAllocation, Category
from finance.forms import BudgetSetupForm, BudgetAllocationFormSet
from finance.services.budget_service import BudgetService
from finance.utilities.budget_utils import get_user_previous_allocations, get_expense_categories


@login_required
def budget_setup_view(request, year=None, month=None):
    """
    View for creating or editing a budget for a specific month.
    If year and month are provided, tries to load an existing budget.
    Otherwise, defaults to creating a budget for the current month.
    """
    # Determine if we're creating a new budget or editing an existing one
    existing_budget = None

    # Check if we have session data from an income transaction
    budget_setup_data = request.session.pop('budget_setup', None)
    initial_income = None
    budget_month = None

    if budget_setup_data:
        # Use the income amount from the session
        initial_income = float(budget_setup_data.get('setup_budget_income', 0))
        # Get the month from the session data
        month_str = budget_setup_data.get('setup_budget_month')
        if month_str:
            budget_month = datetime.fromisoformat(month_str).date()

    if year and month and not budget_month:
        # Try to find an existing budget for the specified month
        budget_month = datetime(int(year), int(month), 1).date()
    elif not budget_month:
        # Use current month as default
        today = datetime.now().date()
        budget_month = datetime(today.year, today.month, 1).date()

    existing_budget = Budget.objects.filter(
        user=request.user,
        month=budget_month,
        is_active=True
    ).first()

    # Initialize the form with the existing budget if found
    if request.method == 'POST':
        # Prepare initial data for POST requests
        initial_data = {}
        if not existing_budget:
            initial_data['month'] = budget_month
            if initial_income:
                initial_data['total_income'] = initial_income

        form = BudgetSetupForm(
            user=request.user,
            data=request.POST,
            instance=existing_budget,
            initial=initial_data
        )

        if form.is_valid():
            # Save the budget
            budget = form.save()

            # Redirect to the allocation page
            messages.success(request, f"Budget for {budget.month.strftime('%B %Y')} created successfully.")
            return redirect('finance:budget_allocate', budget_uid=budget.uid)
        else:
            # Add form errors to messages for debugging
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        # For GET requests, initialize form with existing budget or defaults
        initial_data = {}

        if existing_budget:
            # Editing existing budget
            form = BudgetSetupForm(instance=existing_budget)
        else:
            # New budget
            initial_data = {
                'month': budget_month,
            }

            # Add income from transaction if available
            if initial_income:
                initial_data['total_income'] = initial_income

            form = BudgetSetupForm(user=request.user, initial=initial_data)

    context = {
        'form': form,
        'is_new_budget': existing_budget is None,
        'cancel_url': reverse('finance:dashboard'),
    }

    return render(request, 'finance/budget_setup.html', context)


@login_required
def budget_allocation_view(request, budget_uid):
    """
    View for allocating a budget to different expense categories.
    """
    # Get the budget or 404
    budget = get_object_or_404(Budget, uid=budget_uid, user=request.user)

    # Get expense categories for this user
    categories = get_expense_categories(request.user)

    # Get existing allocations for this budget
    existing_allocations = BudgetAllocation.objects.filter(budget=budget)

    if request.method == 'POST':
        formset = BudgetAllocationFormSet(
            budget=budget,
            user=request.user,
            data=request.POST
        )

        if formset.is_valid():
            # Process the allocations
            with transaction.atomic():
                # Delete existing allocations
                existing_allocations.delete()

                # Create new allocations from the form data
                for form in formset:
                    if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                        category = form.cleaned_data['category']
                        amount = form.cleaned_data['allocated_amount']

                        BudgetAllocation.objects.create(
                            budget=budget,
                            category=category,
                            allocated_amount=amount
                        )

            messages.success(request, "Budget allocations saved successfully.")
            return redirect('finance:budget_dashboard')
    else:
        # For GET requests, initialize formset with existing allocations
        initial_data = []

        if existing_allocations.exists():
            # Use existing allocations
            for allocation in existing_allocations:
                initial_data.append({
                    'category': allocation.category,
                    'allocated_amount': allocation.allocated_amount,
                    'rollover_from_previous': allocation.rollover_from_previous,
                    'spent_amount': allocation.spent_amount,
                    'remaining_amount': allocation.remaining_amount,
                    'allocation_uid': allocation.uid
                })
        else:
            # No existing allocations, try to use previous month's allocations as template
            previous_allocations = get_user_previous_allocations(request.user, budget.month)

            if previous_allocations:
                # Create form data from previous allocations
                for category_id, amount in previous_allocations.items():
                    try:
                        category = Category.objects.get(id=category_id)
                        initial_data.append({
                            'category': category,
                            'allocated_amount': amount,
                            'rollover_from_previous': 0,
                            'spent_amount': 0,
                            'remaining_amount': 0
                        })
                    except Category.DoesNotExist:
                        continue

            # If no previous allocations or empty after filtering
            if not initial_data:
                # Add an empty row for each expense category
                for category in categories:
                    initial_data.append({
                        'category': category,
                        'allocated_amount': 0,
                        'rollover_from_previous': 0,
                        'spent_amount': 0,
                        'remaining_amount': 0
                    })

        formset = BudgetAllocationFormSet(
            budget=budget,
            user=request.user,
            initial=initial_data
        )

    context = {
        'budget': budget,
        'formset': formset,
        'total_income': budget.total_income,
        'categories': categories,
        'cancel_url': reverse('finance:budget_dashboard'),
    }

    return render(request, 'finance/budget_allocation.html', context)
