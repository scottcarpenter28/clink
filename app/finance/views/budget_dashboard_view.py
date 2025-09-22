from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import datetime

from finance.models import Budget, BudgetAllocation
from finance.services.budget_service import BudgetService
from finance.forms import BudgetFilterForm
from finance.utilities.budget_utils import get_budget_summary
from finance.utilities.constants import BUDGET_WARNING_THRESHOLD, BUDGET_DANGER_THRESHOLD, BUDGET_STATUS_COLORS


@login_required
def budget_dashboard_view(request):
    """
    View for displaying the user's budget dashboard with allocations and spending progress.
    """
    # Get filter form
    filter_form = BudgetFilterForm(user=request.user, data=request.GET)

    # Get all active budgets for this user, ordered by month (newest first)
    budgets = Budget.objects.filter(user=request.user, is_active=True).order_by('-month')

    # Apply filters if provided
    if filter_form.is_valid():
        filter_data = filter_form.cleaned_data

        if filter_data.get('year'):
            budgets = budgets.filter(month__year=int(filter_data['year']))

        if filter_data.get('month'):
            budgets = budgets.filter(month__month=int(filter_data['month']))

    # Get current month budget
    today = timezone.now().date()
    current_month = datetime(today.year, today.month, 1).date()
    current_budget = budgets.filter(month=current_month).first()

    # Get budget summaries
    budget_summaries = []
    for budget in budgets[:12]:  # Limit to 12 most recent budgets
        summary = get_budget_summary(budget)

        # Determine status color based on percentage spent
        if summary['total_available'] == 0:
            status = 'unallocated'
        elif summary['percent_spent'] >= BUDGET_DANGER_THRESHOLD:
            status = 'over_budget'
        elif summary['percent_spent'] >= BUDGET_WARNING_THRESHOLD:
            status = 'warning'
        else:
            status = 'on_track'

        summary['status'] = status
        summary['color'] = BUDGET_STATUS_COLORS[status]
        summary['budget'] = budget
        summary['month_name'] = budget.month.strftime('%B %Y')

        budget_summaries.append(summary)

    # Get allocations for current month with spending data
    current_allocations = []
    if current_budget:
        allocations = BudgetAllocation.objects.filter(budget=current_budget).select_related('category')

        for allocation in allocations:
            # Calculate percent spent
            total_available = allocation.allocated_amount + allocation.rollover_from_previous

            if total_available > 0:
                percent_spent = (allocation.spent_amount / total_available) * 100
            else:
                percent_spent = 0

            # Determine status color
            if total_available == 0:
                status = 'unallocated'
            elif percent_spent >= BUDGET_DANGER_THRESHOLD:
                status = 'over_budget'
            elif percent_spent >= BUDGET_WARNING_THRESHOLD:
                status = 'warning'
            else:
                status = 'on_track'

            current_allocations.append({
                'allocation': allocation,
                'percent_spent': percent_spent,
                'status': status,
                'color': BUDGET_STATUS_COLORS[status]
            })

    context = {
        'filter_form': filter_form,
        'budget_summaries': budget_summaries,
        'current_budget': current_budget,
        'current_allocations': current_allocations,
        'current_month_name': current_month.strftime('%B %Y')
    }

    return render(request, 'finance/budget_dashboard.html', context)
