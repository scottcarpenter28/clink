from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.contrib.auth.forms import UserCreationForm


class RegisterViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('finance:register')

        self.existing_user = User.objects.create_user(
            username='existinguser',
            password='existingpass123',
            email='existing@example.com'
        )

    def test_register_view_get_request_anonymous_user(self):
        response = self.client.get(self.register_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form')
        self.assertIsInstance(response.context['form'], UserCreationForm)
        self.assertTemplateUsed(response, 'finance/register.html')

    def test_register_view_get_request_authenticated_user(self):
        self.client.login(username='existinguser', password='existingpass123')

        response = self.client.get(self.register_url)

        self.assertEqual(response.status_code, 302)
        dashboard_url = reverse('finance:dashboard')
        self.assertEqual(response.url, dashboard_url)

    def test_register_view_post_request_valid_data(self):
        response = self.client.post(self.register_url, {
            'username': 'newuser',
            'password1': 'complexpass123',
            'password2': 'complexpass123'
        })

        self.assertEqual(response.status_code, 302)
        dashboard_url = reverse('finance:dashboard')
        self.assertEqual(response.url, dashboard_url)

        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Account created for newuser!')

        user = response.wsgi_request.user
        self.assertTrue(user.is_authenticated)
        self.assertEqual(user.username, 'newuser')

        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_register_view_post_request_existing_username(self):
        response = self.client.post(self.register_url, {
            'username': 'existinguser',
            'password1': 'complexpass123',
            'password2': 'complexpass123'
        })

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'finance/register.html')

        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Please correct the errors below.')

        user = response.wsgi_request.user
        self.assertFalse(user.is_authenticated)

    def test_register_view_post_request_password_mismatch(self):
        response = self.client.post(self.register_url, {
            'username': 'newuser',
            'password1': 'complexpass123',
            'password2': 'differentpass123'
        })

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'finance/register.html')

        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Please correct the errors below.')

        user = response.wsgi_request.user
        self.assertFalse(user.is_authenticated)

        self.assertFalse(User.objects.filter(username='newuser').exists())

    def test_register_view_post_request_weak_password(self):
        response = self.client.post(self.register_url, {
            'username': 'newuser',
            'password1': '123',
            'password2': '123'
        })

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'finance/register.html')

        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Please correct the errors below.')

        user = response.wsgi_request.user
        self.assertFalse(user.is_authenticated)

        self.assertFalse(User.objects.filter(username='newuser').exists())

    def test_register_view_post_request_empty_form(self):
        response = self.client.post(self.register_url, {
            'username': '',
            'password1': '',
            'password2': ''
        })

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'finance/register.html')

        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Please correct the errors below.')

        user = response.wsgi_request.user
        self.assertFalse(user.is_authenticated)

    def test_register_view_post_request_missing_password2(self):
        response = self.client.post(self.register_url, {
            'username': 'newuser',
            'password1': 'complexpass123'
        })

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'finance/register.html')

        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Please correct the errors below.')

        user = response.wsgi_request.user
        self.assertFalse(user.is_authenticated)

        self.assertFalse(User.objects.filter(username='newuser').exists())

    def test_register_view_context_data(self):
        response = self.client.get(self.register_url)

        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'], UserCreationForm)

    def test_authenticated_user_redirect_flow(self):
        self.client.login(username='existinguser', password='existingpass123')

        response = self.client.post(self.register_url, {
            'username': 'newuser',
            'password1': 'complexpass123',
            'password2': 'complexpass123'
        })

        self.assertEqual(response.status_code, 302)
        dashboard_url = reverse('finance:dashboard')
        self.assertEqual(response.url, dashboard_url)
