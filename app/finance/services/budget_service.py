from datetime import datetime
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from finance.models import Budget, BudgetAllocation, Transaction, Category
from finance.utilities.budget_utils import (
    validate_zero_based_allocation,
    get_user_previous_allocations,
    calculate_category_spending
)


class BudgetService:
    """Service class for budget-related operations."""

    @staticmethod
    def create_budget_from_income(user, income_amount, month=None,
                                  previous_allocations=None):
        """
        Create a new budget with the given income amount.
        If month is not provided, current month is used.

        Args:
            user: User object
            income_amount: Total income to allocate
            month: Optional datetime for budget month (defaults to current month)
            previous_allocations: Optional dict of category_id: amount mappings

        Returns:
            New Budget object
        """
        if month is None:
            # Default to the first day of current month
            today = timezone.now().date()
            month = datetime(today.year, today.month, 1).date()

        # Check if a budget already exists for this user and month
        existing = Budget.objects.filter(user=user, month=month).first()
        if existing:
            return existing

        with transaction.atomic():
            # Create a new budget
            budget = Budget.objects.create(
                user=user,
                month=month,
                total_income=income_amount,
                is_active=True
            )

            # If previous allocations provided, create allocation objects
            if previous_allocations:
                for category_id, amount in previous_allocations.items():
                    try:
                        category = Category.objects.get(id=category_id)
                        if category.category_type == 'expense':
                            BudgetAllocation.objects.create(
                                budget=budget,
                                category=category,
                                allocated_amount=amount
                            )
                    except Category.DoesNotExist:
                        continue

        return budget

    @staticmethod
    def get_active_budget_for_month(user, year=None, month=None):
        """
        Get the active budget for the specified month.
        If year and month are not provided, returns current month's budget.

        Args:
            user: User object
            year: Optional year (int)
            month: Optional month (int, 1-12)

        Returns:
            Budget object or None if not found
        """
        if year is None or month is None:
            today = timezone.now().date()
            year = year or today.year
            month = month or today.month

        budget_month = datetime(year, month, 1).date()

        return Budget.objects.filter(
            user=user,
            month=budget_month,
            is_active=True
        ).first()

    @staticmethod
    def calculate_spent_amounts(budget):
        """
        Calculate and return spent amounts for each category in the budget.

        Args:
            budget: Budget object

        Returns:
            Dictionary of {category_id: spent_amount}
        """
        month_start = budget.month
        # Get next month's first day
        if month_start.month == 12:
            month_end = datetime(month_start.year + 1, 1, 1).date()
        else:
            month_end = datetime(month_start.year, month_start.month + 1, 1).date()

        # Get all expense transactions for this user in this month
        transactions = Transaction.objects.filter(
            account__owner=budget.user,
            transaction_date__gte=month_start,
            transaction_date__lt=month_end,
            category__category_type='expense'
        )

        # Group by category and sum amounts
        spent_by_category = {}
        for transaction in transactions:
            category_id = transaction.category_id
            if category_id not in spent_by_category:
                spent_by_category[category_id] = 0
            spent_by_category[category_id] += transaction.amount

        return spent_by_category

    @staticmethod
    def process_monthly_rollover(user, from_month=None, to_month=None):
        """
        Process rollover from one month to the next.
        If months not specified, processes from previous to current month.

        Args:
            user: User object
            from_month: Optional source month datetime
            to_month: Optional destination month datetime

        Returns:
            Dictionary of {category_id: rollover_amount} applied to the new month
        """
        today = timezone.now().date()

        # Default to rolling over from last month to this month
        if not to_month:
            to_month = datetime(today.year, today.month, 1).date()

        if not from_month:
            # Previous month
            if today.month == 1:
                from_month = datetime(today.year - 1, 12, 1).date()
            else:
                from_month = datetime(today.year, today.month - 1, 1).date()

        # Get the budgets for both months
        from_budget = Budget.objects.filter(
            user=user,
            month=from_month,
            is_active=True
        ).first()

        to_budget = Budget.objects.filter(
            user=user,
            month=to_month,
            is_active=True
        ).first()

        if not from_budget or not to_budget:
            return {}

        # Calculate remaining amounts in previous month's budget
        rollovers = {}

        # For each allocation in previous month
        for allocation in BudgetAllocation.objects.filter(budget=from_budget):
            # Calculate remaining amount (allocated + rollover - spent)
            remaining = (allocation.allocated_amount +
                        allocation.rollover_from_previous -
                        allocation.spent_amount)

            if remaining > 0:
                rollovers[allocation.category_id] = remaining

                # Find or create allocation in the new month's budget
                to_allocation, created = BudgetAllocation.objects.get_or_create(
                    budget=to_budget,
                    category=allocation.category,
                    defaults={'allocated_amount': 0, 'rollover_from_previous': 0}
                )

                # Update rollover amount
                to_allocation.rollover_from_previous = remaining
                to_allocation.save()

        return rollovers

    @staticmethod
    def update_budget_allocations(budget, allocations):
        """
        Update budget allocations with provided values.

        Args:
            budget: Budget object
            allocations: Dictionary of {category_id: allocated_amount}

        Returns:
            Boolean indicating if update was successful
        """
        # Validate that allocations match total income
        if not validate_zero_based_allocation(allocations, budget.total_income):
            return False

        with transaction.atomic():
            # Delete existing allocations
            BudgetAllocation.objects.filter(budget=budget).delete()

            # Create new allocations
            for category_id, amount in allocations.items():
                try:
                    category = Category.objects.get(id=category_id)
                    if category.category_type == 'expense':
                        BudgetAllocation.objects.create(
                            budget=budget,
                            category=category,
                            allocated_amount=amount
                        )
                except Category.DoesNotExist:
                    continue

        return True
