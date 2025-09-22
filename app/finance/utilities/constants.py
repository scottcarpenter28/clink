MONTH_NAMES = {
    1: 'January', 2: 'February', 3: 'March', 4: 'April',
    5: 'May', 6: 'June', 7: 'July', 8: 'August',
    9: 'September', 10: 'October', 11: 'November', 12: 'December'
}

TRANSACTION_TYPES = ['income', 'expense']

# Budget constants
BUDGET_STATUS_CHOICES = [
    ('on_track', 'On Track'),
    ('warning', 'Warning'),
    ('over_budget', 'Over Budget'),
    ('unallocated', 'Unallocated')
]

# Progress bar colors for different budget statuses
BUDGET_STATUS_COLORS = {
    'on_track': 'success',    # Green
    'warning': 'warning',     # Yellow
    'over_budget': 'danger',  # Red
    'unallocated': 'info'     # Blue
}

# Thresholds for budget warnings (percentage of allocation spent)
BUDGET_WARNING_THRESHOLD = 80   # Show warning when 80% of budget is spent
BUDGET_DANGER_THRESHOLD = 100   # Show danger when 100% of budget is spent
