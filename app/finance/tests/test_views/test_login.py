from django.test import TestCase, Client
from django.urls import reverse, NoReverseMatch
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.contrib.auth.forms import AuthenticationForm


class LoginViewTestCase(TestCase):
    def setUp(self):
        """Set up test data for each test case"""
        self.client = Client()
        self.login_url = reverse('finance:login')

        # Create a test user
        self.test_user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )

    def test_login_view_get_request_anonymous_user(self):
        """Test GET request to login view for anonymous user"""
        response = self.client.get(self.login_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form')
        self.assertIsInstance(response.context['form'], AuthenticationForm)
        self.assertTemplateUsed(response, 'finance/login.html')

    def test_login_view_post_request_valid_credentials(self):
        """Test POST request with valid credentials"""
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'testpass123'
        })

        self.assertEqual(response.status_code, 302)
        dashboard_url = reverse('finance:dashboard')
        self.assertEqual(response.url, dashboard_url)

        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Welcome back, testuser!')

        user = response.wsgi_request.user
        self.assertTrue(user.is_authenticated)
        self.assertEqual(user.username, 'testuser')

    def test_login_view_post_request_invalid_username(self):
        """Test POST request with invalid username"""
        response = self.client.post(self.login_url, {
            'username': 'nonexistentuser',
            'password': 'testpass123'
        })

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'finance/login.html')

        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Invalid username or password.')

    def test_login_view_post_request_invalid_password(self):
        """Test POST request with invalid password"""
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'wrongpassword'
        })

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'finance/login.html')

        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Invalid username or password.')

    def test_login_view_post_request_empty_form(self):
        """Test POST request with empty form data"""
        response = self.client.post(self.login_url, {
            'username': '',
            'password': ''
        })

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'finance/login.html')

        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Invalid username or password.')

    def test_login_view_context_data(self):
        """Test that the view passes the correct context data"""
        response = self.client.get(self.login_url)

        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'], AuthenticationForm)
