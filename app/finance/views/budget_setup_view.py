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
    existing_budget = None
    budget_setup_data = request.session.pop('budget_setup', None)
    initial_income = None
    budget_month = None

    if budget_setup_data:
        initial_income = float(budget_setup_data.get('setup_budget_income', 0))
        month_str = budget_setup_data.get('setup_budget_month')
        if month_str:
            budget_month = datetime.fromisoformat(month_str).date()

    if year and month and not budget_month:
        budget_month = datetime(int(year), int(month), 1).date()
    elif not budget_month:
        today = datetime.now().date()
        budget_month = datetime(today.year, today.month, 1).date()

    existing_budget = Budget.objects.filter(
        user=request.user,
        month=budget_month,
        is_active=True
    ).first()

    if request.method == 'POST':
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
        initial_data = {}

        if existing_budget:
            form = BudgetSetupForm(instance=existing_budget)
        else:
            initial_data = {
                'month': budget_month,
            }
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
    budget = get_object_or_404(Budget, uid=budget_uid, user=request.user)
    categories = get_expense_categories(request.user)

    existing_allocations = BudgetAllocation.objects.filter(budget=budget)
    if request.method == 'POST':
        formset = BudgetAllocationFormSet(
            budget=budget,
            user=request.user,
            data=request.POST
        )

        if formset.is_valid():
            with transaction.atomic():
                existing_allocations.delete()

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
            previous_allocations = get_user_previous_allocations(request.user, budget.month)

            if previous_allocations:
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

            if not initial_data:
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
