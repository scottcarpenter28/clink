from django.urls import path
from django.views.generic import RedirectView

from finance.views import (
    login_view,
    signup_view,
    logout_view,
    home_view,
    year_review_view,
    create_budget,
    update_budget,
    get_budget,
    delete_budget,
    get_budget_categories,
    create_transaction,
    update_transaction,
    get_transaction,
    delete_transaction,
)
from finance.views.internal_transfer_views import (
    create_internal_transfer,
    get_internal_transfers,
    delete_internal_transfer,
)

urlpatterns = [
    path("login/", login_view, name="login"),
    path("signup/", signup_view, name="signup"),
    path("logout/", logout_view, name="logout"),
    path("home/", home_view, name="home"),
    path("<int:year>/<int:month>/", home_view, name="home_with_date"),
    path("review/", year_review_view, name="year_review"),
    path("review/<int:year>/", year_review_view, name="year_review_with_year"),
    path("budgets/create/", create_budget, name="create_budget"),
    path("budgets/<int:budget_id>/", get_budget, name="get_budget"),
    path("budgets/<int:budget_id>/update/", update_budget, name="update_budget"),
    path("budgets/<int:budget_id>/delete/", delete_budget, name="delete_budget"),
    path(
        "budgets/<int:year>/<int:month>/<str:type>/categories/",
        get_budget_categories,
        name="get_budget_categories",
    ),
    path(
        "transfers/create/", create_internal_transfer, name="create_internal_transfer"
    ),
    path("transfers/", get_internal_transfers, name="get_internal_transfers"),
    path(
        "transfers/<int:transfer_id>/delete/",
        delete_internal_transfer,
        name="delete_internal_transfer",
    ),
    path("transactions/create/", create_transaction, name="create_transaction"),
    path("transactions/<int:transaction_id>/", get_transaction, name="get_transaction"),
    path(
        "transactions/<int:transaction_id>/update/",
        update_transaction,
        name="update_transaction",
    ),
    path(
        "transactions/<int:transaction_id>/delete/",
        delete_transaction,
        name="delete_transaction",
    ),
    path("", RedirectView.as_view(pattern_name="home"), name="root"),
]
