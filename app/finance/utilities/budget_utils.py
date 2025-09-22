from decimal import Decimal
from django.utils import timezone
from django.db.models import Sum
from finance.models import BudgetAllocation, Transaction, Category


def validate_zero_based_allocation(allocations, total_income):
    """
    Validate that the sum of all allocations equals the total income.

    Args:
        allocations: Dictionary of category_id: amount mappings
        total_income: Total income amount to compare against

    Returns:
        Boolean indicating if allocations sum to total income
    """
    # Convert to Decimal for precision
    income = Decimal(str(total_income)).quantize(Decimal('0.01'))
    total_allocated = Decimal('0.00')

    for amount in allocations.values():
        total_allocated += Decimal(str(amount)).quantize(Decimal('0.01'))

    # Allow a small tolerance for floating point precision issues
    return abs(total_allocated - income) < Decimal('0.01')


def get_user_previous_allocations(user, month=None):
    """
    Get a user's previous budget allocations to use as template for new budget.

    Args:
        user: User object
        month: Optional month to look back from (defaults to current month)

    Returns:
        Dictionary of category_id: amount mappings from most recent budget
    """
    if month is None:
        # Default to current month
        today = timezone.now().date()
        month = today.replace(day=1)

    # Find the most recent budget before the specified month
    from finance.models import Budget

    previous_budget = Budget.objects.filter(
        user=user,
        month__lt=month,
        is_active=True
    ).order_by('-month').first()

    if not previous_budget:
        return {}

    # Get the allocations from that budget
    allocations = {}
    for allocation in BudgetAllocation.objects.filter(budget=previous_budget):
        allocations[allocation.category_id] = allocation.allocated_amount

    return allocations


def calculate_category_spending(budget, category):
    """
    Calculate the total spending in a specific category for a budget period.

    Args:
        budget: Budget object
        category: Category object

    Returns:
        Float amount spent in the category for the budget period
    """
    month_start = budget.month

    # Calculate month end (first day of next month)
    if month_start.month == 12:
        month_end = month_start.replace(year=month_start.year + 1, month=1, day=1)
    else:
        month_end = month_start.replace(month=month_start.month + 1, day=1)

    # Sum all transactions for this category in the budget's month
    transactions_sum = Transaction.objects.filter(
        account__owner=budget.user,
        category=category,
        transaction_date__gte=month_start,
        transaction_date__lt=month_end
    ).aggregate(total=Sum('amount'))['total'] or 0

    return transactions_sum


def get_budget_summary(budget):
    """
    Get summary statistics for a budget including total allocated,
    total spent, and percentage used.

    Args:
        budget: Budget object

    Returns:
        Dictionary with summary statistics
    """
    allocations = BudgetAllocation.objects.filter(budget=budget)

    total_allocated = sum(a.allocated_amount for a in allocations)
    total_rollover = sum(a.rollover_from_previous for a in allocations)
    total_available = total_allocated + total_rollover

    # Get all spent amounts
    spent_amounts = {a.category_id: a.spent_amount for a in allocations}
    total_spent = sum(spent_amounts.values())

    # Calculate remaining
    total_remaining = total_available - total_spent

    # Calculate percentage spent
    percent_spent = (total_spent / total_available * 100) if total_available > 0 else 0

    return {
        'total_income': budget.total_income,
        'total_allocated': total_allocated,
        'total_rollover': total_rollover,
        'total_available': total_available,
        'total_spent': total_spent,
        'total_remaining': total_remaining,
        'percent_spent': percent_spent
    }


def get_unallocated_amount(budget):
    """
    Calculate the amount of income not yet allocated in the budget.

    Args:
        budget: Budget object

    Returns:
        Float representing unallocated amount
    """
    total_allocated = BudgetAllocation.objects.filter(budget=budget).aggregate(
        total=Sum('allocated_amount')
    )['total'] or 0

    return budget.total_income - total_allocated


def get_expense_categories(user=None):
    """
    Get all expense categories, optionally filtering by those used by a user.

    Args:
        user: Optional User object to filter categories

    Returns:
        QuerySet of Category objects
    """
    categories = Category.objects.filter(category_type='expense')

    if user:
        # Get only categories that have been used by this user
        used_category_ids = Transaction.objects.filter(
            account__owner=user,
            category__category_type='expense'
        ).values_list('category_id', flat=True).distinct()

        # Include all categories this user has already created budget allocations for
        budget_category_ids = BudgetAllocation.objects.filter(
            budget__user=user
        ).values_list('category_id', flat=True).distinct()

        # Combine both sets of IDs
        used_category_ids = set(list(used_category_ids) + list(budget_category_ids))

        if used_category_ids:
            return categories.filter(id__in=used_category_ids)

    return categories.all()
