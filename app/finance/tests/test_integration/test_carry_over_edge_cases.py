from datetime import date

from django.test import TestCase
from django.contrib.auth.models import User

from finance.models import Budget, Transaction, InternalTransfer
from finance.enums.transaction_enums import TransactionType
from finance.utils.budget_calculator import process_month_end_carry_over


class DeletingBudgetWithCarryOverTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

    def test_deleting_budget_with_carried_over_amount(self):
        jan_budget = Budget.objects.create(
            user=self.user,
            type=TransactionType.SAVINGS.name,
            category="Emergency Fund",
            amount_in_cents=100000,
            budget_year=2025,
            budget_month=1,
            allow_carry_over=True,
        )

        process_month_end_carry_over(self.user, 2025, 1)

        feb_budget = Budget.objects.get(
            user=self.user,
            category="Emergency Fund",
            budget_year=2025,
            budget_month=2,
        )
        self.assertEqual(feb_budget.carried_over_amount_in_cents, 100000)

        jan_budget.delete()

        self.assertTrue(Budget.objects.filter(id=feb_budget.id).exists())
        feb_budget.refresh_from_db()
        self.assertEqual(feb_budget.carried_over_amount_in_cents, 100000)

    def test_deleting_budget_that_received_transfer(self):
        source = Budget.objects.create(
            user=self.user,
            type=TransactionType.SAVINGS.name,
            category="Emergency Fund",
            amount_in_cents=100000,
            budget_year=2025,
            budget_month=1,
        )

        dest = Budget.objects.create(
            user=self.user,
            type=TransactionType.SAVINGS.name,
            category="Vacation",
            amount_in_cents=50000,
            budget_year=2025,
            budget_month=1,
        )

        transfer = InternalTransfer.objects.create(
            user=self.user,
            source_budget=source,
            destination_budget=dest,
            amount_in_cents=20000,
            transfer_date=date(2025, 1, 10),
        )

        dest_id = dest.id
        transfer_id = transfer.id
        dest.delete()

        self.assertFalse(Budget.objects.filter(id=dest_id).exists())
        self.assertFalse(InternalTransfer.objects.filter(id=transfer_id).exists())


class MultipleTransfersInSingleMonthTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

    def test_multiple_transfers_affect_carry_over_correctly(self):
        emergency = Budget.objects.create(
            user=self.user,
            type=TransactionType.SAVINGS.name,
            category="Emergency Fund",
            amount_in_cents=100000,
            budget_year=2025,
            budget_month=1,
            allow_carry_over=True,
        )

        vacation = Budget.objects.create(
            user=self.user,
            type=TransactionType.SAVINGS.name,
            category="Vacation",
            amount_in_cents=50000,
            budget_year=2025,
            budget_month=1,
            allow_carry_over=True,
        )

        InternalTransfer.objects.create(
            user=self.user,
            source_budget=emergency,
            destination_budget=vacation,
            amount_in_cents=10000,
            transfer_date=date(2025, 1, 5),
        )

        InternalTransfer.objects.create(
            user=self.user,
            source_budget=emergency,
            destination_budget=vacation,
            amount_in_cents=15000,
            transfer_date=date(2025, 1, 15),
        )

        InternalTransfer.objects.create(
            user=self.user,
            source_budget=vacation,
            destination_budget=emergency,
            amount_in_cents=5000,
            transfer_date=date(2025, 1, 20),
        )

        process_month_end_carry_over(self.user, 2025, 1)

        feb_emergency = Budget.objects.get(
            user=self.user, category="Emergency Fund", budget_year=2025, budget_month=2
        )
        feb_vacation = Budget.objects.get(
            user=self.user, category="Vacation", budget_year=2025, budget_month=2
        )

        expected_emergency = 100000 - 10000 - 15000 + 5000
        expected_vacation = 50000 + 10000 + 15000 - 5000

        self.assertEqual(feb_emergency.carried_over_amount_in_cents, expected_emergency)
        self.assertEqual(feb_vacation.carried_over_amount_in_cents, expected_vacation)

    def test_bidirectional_transfers_in_same_month(self):
        budget_a = Budget.objects.create(
            user=self.user,
            type=TransactionType.SAVINGS.name,
            category="Fund A",
            amount_in_cents=100000,
            budget_year=2025,
            budget_month=1,
            allow_carry_over=True,
        )

        budget_b = Budget.objects.create(
            user=self.user,
            type=TransactionType.SAVINGS.name,
            category="Fund B",
            amount_in_cents=100000,
            budget_year=2025,
            budget_month=1,
            allow_carry_over=True,
        )

        InternalTransfer.objects.create(
            user=self.user,
            source_budget=budget_a,
            destination_budget=budget_b,
            amount_in_cents=30000,
            transfer_date=date(2025, 1, 10),
        )

        InternalTransfer.objects.create(
            user=self.user,
            source_budget=budget_b,
            destination_budget=budget_a,
            amount_in_cents=50000,
            transfer_date=date(2025, 1, 20),
        )

        process_month_end_carry_over(self.user, 2025, 1)

        feb_a = Budget.objects.get(
            user=self.user, category="Fund A", budget_year=2025, budget_month=2
        )
        feb_b = Budget.objects.get(
            user=self.user, category="Fund B", budget_year=2025, budget_month=2
        )

        self.assertEqual(feb_a.carried_over_amount_in_cents, 120000)
        self.assertEqual(feb_b.carried_over_amount_in_cents, 80000)


class TransferringFromBudgetWithCarryOverTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

    def test_transfer_from_budget_with_existing_carry_over(self):
        jan_budget = Budget.objects.create(
            user=self.user,
            type=TransactionType.SAVINGS.name,
            category="Emergency Fund",
            amount_in_cents=100000,
            budget_year=2025,
            budget_month=1,
            allow_carry_over=True,
        )

        process_month_end_carry_over(self.user, 2025, 1)

        feb_emergency = Budget.objects.get(
            user=self.user,
            category="Emergency Fund",
            budget_year=2025,
            budget_month=2,
        )
        self.assertEqual(feb_emergency.carried_over_amount_in_cents, 100000)

        feb_vacation = Budget.objects.create(
            user=self.user,
            type=TransactionType.SAVINGS.name,
            category="Vacation",
            amount_in_cents=50000,
            budget_year=2025,
            budget_month=2,
            allow_carry_over=True,
        )

        InternalTransfer.objects.create(
            user=self.user,
            source_budget=feb_emergency,
            destination_budget=feb_vacation,
            amount_in_cents=30000,
            transfer_date=date(2025, 2, 15),
        )

        process_month_end_carry_over(self.user, 2025, 2)

        mar_emergency = Budget.objects.get(
            user=self.user,
            category="Emergency Fund",
            budget_year=2025,
            budget_month=3,
        )
        mar_vacation = Budget.objects.get(
            user=self.user,
            category="Vacation",
            budget_year=2025,
            budget_month=3,
        )

        expected_emergency = 100000 + 100000 - 30000
        expected_vacation = 50000 + 30000

        self.assertEqual(mar_emergency.carried_over_amount_in_cents, expected_emergency)
        self.assertEqual(mar_vacation.carried_over_amount_in_cents, expected_vacation)


class ChainOfTransfersTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

    def test_chain_of_transfers_affecting_multiple_budgets(self):
        budget_a = Budget.objects.create(
            user=self.user,
            type=TransactionType.SAVINGS.name,
            category="Fund A",
            amount_in_cents=100000,
            budget_year=2025,
            budget_month=1,
            allow_carry_over=True,
        )

        budget_b = Budget.objects.create(
            user=self.user,
            type=TransactionType.SAVINGS.name,
            category="Fund B",
            amount_in_cents=50000,
            budget_year=2025,
            budget_month=1,
            allow_carry_over=True,
        )

        budget_c = Budget.objects.create(
            user=self.user,
            type=TransactionType.SAVINGS.name,
            category="Fund C",
            amount_in_cents=25000,
            budget_year=2025,
            budget_month=1,
            allow_carry_over=True,
        )

        InternalTransfer.objects.create(
            user=self.user,
            source_budget=budget_a,
            destination_budget=budget_b,
            amount_in_cents=20000,
            transfer_date=date(2025, 1, 5),
        )

        InternalTransfer.objects.create(
            user=self.user,
            source_budget=budget_b,
            destination_budget=budget_c,
            amount_in_cents=15000,
            transfer_date=date(2025, 1, 10),
        )

        InternalTransfer.objects.create(
            user=self.user,
            source_budget=budget_c,
            destination_budget=None,
            amount_in_cents=10000,
            transfer_date=date(2025, 1, 15),
        )

        process_month_end_carry_over(self.user, 2025, 1)

        feb_a = Budget.objects.get(
            user=self.user, category="Fund A", budget_year=2025, budget_month=2
        )
        feb_b = Budget.objects.get(
            user=self.user, category="Fund B", budget_year=2025, budget_month=2
        )
        feb_c = Budget.objects.get(
            user=self.user, category="Fund C", budget_year=2025, budget_month=2
        )

        self.assertEqual(feb_a.carried_over_amount_in_cents, 80000)
        self.assertEqual(feb_b.carried_over_amount_in_cents, 55000)
        self.assertEqual(feb_c.carried_over_amount_in_cents, 30000)


class ConcurrentUserAccessTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username="user1", password="testpass123")
        self.user2 = User.objects.create_user(username="user2", password="testpass123")

    def test_concurrent_users_dont_interfere_with_carry_overs(self):
        Budget.objects.create(
            user=self.user1,
            type=TransactionType.SAVINGS.name,
            category="Emergency Fund",
            amount_in_cents=100000,
            budget_year=2025,
            budget_month=1,
            allow_carry_over=True,
        )

        Budget.objects.create(
            user=self.user2,
            type=TransactionType.SAVINGS.name,
            category="Emergency Fund",
            amount_in_cents=200000,
            budget_year=2025,
            budget_month=1,
            allow_carry_over=True,
        )

        process_month_end_carry_over(self.user1, 2025, 1)
        process_month_end_carry_over(self.user2, 2025, 1)

        user1_feb = Budget.objects.get(
            user=self.user1,
            category="Emergency Fund",
            budget_year=2025,
            budget_month=2,
        )

        user2_feb = Budget.objects.get(
            user=self.user2,
            category="Emergency Fund",
            budget_year=2025,
            budget_month=2,
        )

        self.assertEqual(user1_feb.carried_over_amount_in_cents, 100000)
        self.assertEqual(user2_feb.carried_over_amount_in_cents, 200000)

    def test_users_transfers_dont_affect_other_users(self):
        user1_emergency = Budget.objects.create(
            user=self.user1,
            type=TransactionType.SAVINGS.name,
            category="Emergency Fund",
            amount_in_cents=100000,
            budget_year=2025,
            budget_month=1,
            allow_carry_over=True,
        )

        user1_vacation = Budget.objects.create(
            user=self.user1,
            type=TransactionType.SAVINGS.name,
            category="Vacation",
            amount_in_cents=50000,
            budget_year=2025,
            budget_month=1,
            allow_carry_over=True,
        )

        user2_emergency = Budget.objects.create(
            user=self.user2,
            type=TransactionType.SAVINGS.name,
            category="Emergency Fund",
            amount_in_cents=200000,
            budget_year=2025,
            budget_month=1,
            allow_carry_over=True,
        )

        InternalTransfer.objects.create(
            user=self.user1,
            source_budget=user1_emergency,
            destination_budget=user1_vacation,
            amount_in_cents=25000,
            transfer_date=date(2025, 1, 10),
        )

        process_month_end_carry_over(self.user1, 2025, 1)
        process_month_end_carry_over(self.user2, 2025, 1)

        user1_feb_emergency = Budget.objects.get(
            user=self.user1,
            category="Emergency Fund",
            budget_year=2025,
            budget_month=2,
        )

        user2_feb_emergency = Budget.objects.get(
            user=self.user2,
            category="Emergency Fund",
            budget_year=2025,
            budget_month=2,
        )

        self.assertEqual(user1_feb_emergency.carried_over_amount_in_cents, 75000)
        self.assertEqual(user2_feb_emergency.carried_over_amount_in_cents, 200000)
