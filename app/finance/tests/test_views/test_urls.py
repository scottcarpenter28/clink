from django.test import TestCase
from django.urls import reverse, resolve
from django.contrib.auth.models import User

from finance.views import (
    home_view,
    login_view,
    signup_view,
    logout_view,
    create_budget,
    update_budget,
    delete_budget,
    create_transaction,
    update_transaction,
    delete_transaction,
)


class URLRoutingTests(TestCase):
    def test_home_url_resolves_to_home_view(self):
        url = reverse("home")
        self.assertEqual(resolve(url).func, home_view)

    def test_home_with_date_url_resolves_to_home_view(self):
        url = reverse("home_with_date", kwargs={"year": 2025, "month": 10})
        self.assertEqual(resolve(url).func, home_view)

    def test_root_url_redirects_to_home(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith(reverse("home")))

    def test_login_url_resolves(self):
        url = reverse("login")
        self.assertEqual(resolve(url).func, login_view)

    def test_signup_url_resolves(self):
        url = reverse("signup")
        self.assertEqual(resolve(url).func, signup_view)

    def test_logout_url_resolves(self):
        url = reverse("logout")
        self.assertEqual(resolve(url).func, logout_view)

    def test_create_budget_url_resolves(self):
        url = reverse("create_budget")
        self.assertEqual(resolve(url).func, create_budget)

    def test_update_budget_url_resolves(self):
        url = reverse("update_budget", kwargs={"budget_id": 1})
        self.assertEqual(resolve(url).func, update_budget)

    def test_delete_budget_url_resolves(self):
        url = reverse("delete_budget", kwargs={"budget_id": 1})
        self.assertEqual(resolve(url).func, delete_budget)

    def test_create_transaction_url_resolves(self):
        url = reverse("create_transaction")
        self.assertEqual(resolve(url).func, create_transaction)

    def test_update_transaction_url_resolves(self):
        url = reverse("update_transaction", kwargs={"transaction_id": 1})
        self.assertEqual(resolve(url).func, update_transaction)

    def test_delete_transaction_url_resolves(self):
        url = reverse("delete_transaction", kwargs={"transaction_id": 1})
        self.assertEqual(resolve(url).func, delete_transaction)
