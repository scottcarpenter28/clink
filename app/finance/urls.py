from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

app_name = 'finance'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', LogoutView.as_view(next_page='finance:login'), name='logout'),
    path('add/<str:transaction_type>/', views.add_transaction_view, name='add_transaction'),
    path('accounts/add/', views.add_account_view, name='add_account'),
    path('transactions/', views.transaction_list_view, name='transaction_list'),
    # Budget URLs
    path('budget/setup/', views.budget_setup_view, name='budget_setup'),
    path('budget/setup/<int:year>/<int:month>/', views.budget_setup_view, name='budget_setup_month'),
    path('budget/dashboard/', views.budget_dashboard_view, name='budget_dashboard'),
    path('budget/allocate/<uuid:budget_uid>/', views.budget_allocation_view, name='budget_allocate'),
]
