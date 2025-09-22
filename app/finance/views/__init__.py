from .login_view import login_view
from .register_view import register_view
from .dashboard_view import dashboard_view
from .add_transaction_view import add_transaction_view
from .add_account_view import add_account_view
from .transaction_list_view import transaction_list_view
from .budget_setup_view import budget_setup_view, budget_allocation_view
from .budget_dashboard_view import budget_dashboard_view

__all__ = [
    'login_view',
    'register_view',
    'dashboard_view',
    'add_transaction_view',
    'add_account_view',
    'transaction_list_view',
    'budget_setup_view',
    'budget_allocation_view',
    'budget_dashboard_view'
]
