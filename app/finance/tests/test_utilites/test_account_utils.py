from django.utils import timezone
import datetime
from django.contrib.auth.models import User
from django.test import TestCase

from finance.models import Account, AccountTracker
from finance.utilities.account_utils import (
    get_user_accounts,
    get_latest_account_balance,
    get_latest_user_account_balances,
    CurrentAccountBalance
)


class TestAccountUtils(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='testuser1',
            email='test1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )

        self.account1 = Account.objects.create(
            name='Checking Account',
            starting_balance=1000.00,
            owner=self.user1
        )
        self.account2 = Account.objects.create(
            name='Savings Account',
            starting_balance=5000.00,
            owner=self.user1
        )

        self.account3 = Account.objects.create(
            name='Credit Card',
            starting_balance=-500.00,
            owner=self.user2
        )

    def test_get_user_accounts_returns_correct_accounts(self):
        user1_accounts = get_user_accounts(self.user1)
        user2_accounts = get_user_accounts(self.user2)

        self.assertEqual(user1_accounts.count(), 2)
        self.assertIn(self.account1, user1_accounts)
        self.assertIn(self.account2, user1_accounts)

        self.assertEqual(user2_accounts.count(), 1)
        self.assertIn(self.account3, user2_accounts)

    def test_get_user_accounts_empty_for_user_with_no_accounts(self):
        user_no_accounts = User.objects.create_user(
            username='noaccounts',
            email='no@example.com',
            password='testpass123'
        )

        accounts = get_user_accounts(user_no_accounts)
        self.assertEqual(accounts.count(), 0)

    def test_get_latest_account_balance_with_tracker_records(self):
        AccountTracker.objects.create(
            account=self.account1,
            balance=1200.00
        )
        AccountTracker.objects.create(
            account=self.account1,
            balance=1500.00
        )

        result = get_latest_account_balance(self.account1)

        self.assertIsInstance(result, CurrentAccountBalance)
        self.assertEqual(result.account, 'Checking Account')
        self.assertEqual(result.balance, 1500.00)

    def test_get_latest_account_balance_without_tracker_records(self):
        result = get_latest_account_balance(self.account2)

        self.assertIsInstance(result, CurrentAccountBalance)
        self.assertEqual(result.account, 'Savings Account')
        self.assertEqual(result.balance, 5000.00)

    def test_get_latest_account_balance_with_negative_balance(self):
        AccountTracker.objects.create(
            account=self.account3,
            balance=-750.00
        )

        result = get_latest_account_balance(self.account3)

        self.assertIsInstance(result, CurrentAccountBalance)
        self.assertEqual(result.account, 'Credit Card')
        self.assertEqual(result.balance, -750.00)

    def test_get_latest_account_balance_with_zero_balance(self):
        zero_account = Account.objects.create(
            name='Empty Account',
            starting_balance=0.00,
            owner=self.user1
        )

        result = get_latest_account_balance(zero_account)

        self.assertIsInstance(result, CurrentAccountBalance)
        self.assertEqual(result.account, 'Empty Account')
        self.assertEqual(result.balance, 0.00)

    def test_get_latest_user_account_balances_ordering(self):
        tracker1 = AccountTracker.objects.create(
            account=self.account1,
            balance=1000.00
        )
        tracker2 = AccountTracker.objects.create(
            account=self.account1,
            balance=2000.00
        )

        tracker1.created = timezone.now() - datetime.timedelta(days=1)
        tracker1.save()
        tracker2.created = timezone.now()
        tracker2.save()

        result = get_latest_user_account_balances(self.user1)
        checking_result = next(r for r in result if r.account == 'Checking Account')

        self.assertEqual(checking_result.balance, 2000.00)

    def test_current_account_balance_model(self):
        balance = CurrentAccountBalance(account="Test Account", balance=123.45)

        self.assertEqual(balance.account, "Test Account")
        self.assertEqual(balance.balance, 123.45)

        balance_dict = balance.model_dump()
        expected = {"account": "Test Account", "balance": 123.45}
        self.assertEqual(balance_dict, expected)

    def test_get_latest_account_balance_uses_most_recent_tracker(self):
        older_tracker = AccountTracker.objects.create(
            account=self.account1,
            balance=100.00
        )
        older_tracker.created = timezone.now() - datetime.timedelta(hours=2)
        older_tracker.save()

        newer_tracker = AccountTracker.objects.create(
            account=self.account1,
            balance=200.00
        )
        newer_tracker.created = timezone.now() - datetime.timedelta(hours=1)
        newer_tracker.save()

        AccountTracker.objects.create(
            account=self.account1,
            balance=300.00
        )

        result = get_latest_account_balance(self.account1)

        self.assertEqual(result.balance, 300.00)

    def test_get_user_accounts_with_multiple_users_isolation(self):
        user3 = User.objects.create_user(
            username='user3',
            email='user3@example.com',
            password='testpass123'
        )
        account_user3 = Account.objects.create(
            name='User3 Account',
            starting_balance=999.99,
            owner=user3
        )

        user1_accounts = get_user_accounts(self.user1)
        user2_accounts = get_user_accounts(self.user2)
        user3_accounts = get_user_accounts(user3)

        self.assertEqual(user1_accounts.count(), 2)
        self.assertEqual(user2_accounts.count(), 1)
        self.assertEqual(user3_accounts.count(), 1)

        self.assertNotIn(self.account3, user1_accounts)
        self.assertNotIn(account_user3, user1_accounts)
        self.assertNotIn(self.account1, user2_accounts)
        self.assertNotIn(account_user3, user2_accounts)
        self.assertNotIn(self.account1, user3_accounts)
        self.assertNotIn(self.account2, user3_accounts)
        self.assertNotIn(self.account3, user3_accounts)

        AccountTracker.objects.create(
            account=self.account1,
            balance=123.456789
        )

        result = get_latest_account_balance(self.account1)

        self.assertIsInstance(result, CurrentAccountBalance)
        self.assertEqual(result.account, 'Checking Account')
        self.assertAlmostEqual(result.balance, 123.456789, places=6)

    def test_get_latest_user_account_balances_performance_with_many_trackers(self):
        for i in range(10):
            AccountTracker.objects.create(
                account=self.account1,
                balance=float(i * 100)
            )

        result = get_latest_user_account_balances(self.user1)

        self.assertEqual(len(result), 2)

        checking_result = next(r for r in result if r.account == 'Checking Account')

        self.assertEqual(checking_result.balance, 900.0)

    def test_get_latest_account_balance_with_deleted_trackers(self):
        tracker1 = AccountTracker.objects.create(
            account=self.account1,
            balance=100.00
        )
        AccountTracker.objects.create(
            account=self.account1,
            balance=200.00
        )

        tracker1.delete()

        result = get_latest_account_balance(self.account1)

        self.assertEqual(result.balance, 200.00)

    def test_get_user_accounts_queryset_properties(self):
        accounts = get_user_accounts(self.user1)

        from django.db.models.query import QuerySet
        self.assertIsInstance(accounts, QuerySet)

        self.assertEqual(accounts.count(), 2)
        self.assertTrue(accounts.exists())

        named_accounts = accounts.filter(name__icontains='account')
        self.assertEqual(named_accounts.count(), 2)
