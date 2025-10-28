from django.test import TestCase
from django.contrib.auth.models import User

from finance.models import UserSettings


class UserSettingsModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

    def test_user_settings_creation(self):
        settings = UserSettings.objects.create(user=self.user)

        self.assertEqual(settings.user, self.user)
        self.assertTrue(settings.weekly_reminder_enabled)
        self.assertTrue(settings.weekly_summary_enabled)
        self.assertTrue(settings.monthly_summary_enabled)
        self.assertTrue(settings.yearly_summary_enabled)
        self.assertIsNotNone(settings.date_created)
        self.assertIsNotNone(settings.date_updated)

    def test_user_settings_string_representation(self):
        settings = UserSettings.objects.create(user=self.user)

        expected_string = "testuser - Email Settings"
        self.assertEqual(str(settings), expected_string)

    def test_user_settings_custom_values(self):
        settings = UserSettings.objects.create(
            user=self.user,
            weekly_reminder_enabled=False,
            weekly_summary_enabled=True,
            monthly_summary_enabled=False,
            yearly_summary_enabled=True,
        )

        self.assertFalse(settings.weekly_reminder_enabled)
        self.assertTrue(settings.weekly_summary_enabled)
        self.assertFalse(settings.monthly_summary_enabled)
        self.assertTrue(settings.yearly_summary_enabled)

    def test_user_settings_one_to_one_relationship(self):
        settings = UserSettings.objects.create(user=self.user)

        retrieved_settings = self.user.email_settings
        self.assertEqual(settings, retrieved_settings)

    def test_user_settings_update(self):
        settings = UserSettings.objects.create(user=self.user)
        original_updated = settings.date_updated

        settings.weekly_reminder_enabled = False
        settings.save()

        self.assertFalse(settings.weekly_reminder_enabled)
        self.assertGreater(settings.date_updated, original_updated)

    def test_user_settings_cascade_delete(self):
        settings = UserSettings.objects.create(user=self.user)
        settings_id = settings.id

        self.user.delete()

        with self.assertRaises(UserSettings.DoesNotExist):
            UserSettings.objects.get(id=settings_id)
