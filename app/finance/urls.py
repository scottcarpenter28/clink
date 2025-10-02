from django.urls import path

from finance.views import login_view, signup_view, logout_view, home_view

urlpatterns = [
    path("login/", login_view, name="login"),
    path("signup/", signup_view, name="signup"),
    path("logout/", logout_view, name="logout"),
    path("", home_view, name="home"),
]
