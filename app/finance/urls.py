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
]
