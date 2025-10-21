from datetime import date

from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from finance.models import Budget, InternalTransfer
from finance.enums.transaction_enums import TransactionType


class InternalTransferModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

        self.source_budget = Budget.objects.create(
            user=self.user,
            type=TransactionType.SAVINGS.name,
            category="Emergency Fund",
            amount_in_cents=100000,
            budget_year=2025,
            budget_month=10,
        )

        self.dest_budget = Budget.objects.create(
            user=self.user,
            type=TransactionType.SAVINGS.name,
            category="Vacation",
            amount_in_cents=50000,
            budget_year=2025,
            budget_month=10,
        )

    def test_create_transfer_with_all_fields(self):
        transfer = InternalTransfer.objects.create(
            user=self.user,
            source_budget=self.source_budget,
            destination_budget=self.dest_budget,
            amount_in_cents=25000,
            transfer_date=date(2025, 10, 15),
            description="Moving funds for vacation",
        )

        self.assertEqual(transfer.user, self.user)
        self.assertEqual(transfer.source_budget, self.source_budget)
        self.assertEqual(transfer.destination_budget, self.dest_budget)
        self.assertEqual(transfer.amount_in_cents, 25000)
        self.assertEqual(transfer.transfer_date, date(2025, 10, 15))
        self.assertEqual(transfer.description, "Moving funds for vacation")

    def test_create_transfer_to_use_funds(self):
        transfer = InternalTransfer.objects.create(
            user=self.user,
            source_budget=self.source_budget,
            destination_budget=None,
            amount_in_cents=30000,
            transfer_date=date(2025, 10, 20),
        )

        self.assertIsNone(transfer.destination_budget)
        self.assertEqual(transfer.amount_in_cents, 30000)

    def test_amount_dollars_property(self):
        transfer = InternalTransfer.objects.create(
            user=self.user,
            source_budget=self.source_budget,
            destination_budget=self.dest_budget,
            amount_in_cents=25050,
            transfer_date=date(2025, 10, 15),
        )

        self.assertEqual(transfer.amount_dollars, 250.50)

    def test_clean_prevents_zero_amount(self):
        transfer = InternalTransfer(
            user=self.user,
            source_budget=self.source_budget,
            destination_budget=self.dest_budget,
            amount_in_cents=0,
            transfer_date=date(2025, 10, 15),
        )

        with self.assertRaises(ValidationError) as context:
            transfer.clean()

        self.assertIn("amount_in_cents", context.exception.message_dict)

    def test_clean_prevents_negative_amount(self):
        transfer = InternalTransfer(
            user=self.user,
            source_budget=self.source_budget,
            destination_budget=self.dest_budget,
            amount_in_cents=-5000,
            transfer_date=date(2025, 10, 15),
        )

        with self.assertRaises(ValidationError) as context:
            transfer.clean()

        self.assertIn("amount_in_cents", context.exception.message_dict)

    def test_clean_prevents_income_source_budget(self):
        income_budget = Budget.objects.create(
            user=self.user,
            type=TransactionType.INCOME.name,
            category="Salary",
            amount_in_cents=500000,
            budget_year=2025,
            budget_month=10,
        )

        transfer = InternalTransfer(
            user=self.user,
            source_budget=income_budget,
            destination_budget=self.dest_budget,
            amount_in_cents=10000,
            transfer_date=date(2025, 10, 15),
        )

        with self.assertRaises(ValidationError) as context:
            transfer.clean()

        self.assertIn("source_budget", context.exception.message_dict)

    def test_clean_prevents_same_source_and_destination(self):
        transfer = InternalTransfer(
            user=self.user,
            source_budget=self.source_budget,
            destination_budget=self.source_budget,
            amount_in_cents=10000,
            transfer_date=date(2025, 10, 15),
        )

        with self.assertRaises(ValidationError) as context:
            transfer.clean()

        self.assertIn(
            "Source and destination budgets cannot be the same", str(context.exception)
        )

    def test_str_representation_with_destination(self):
        transfer = InternalTransfer.objects.create(
            user=self.user,
            source_budget=self.source_budget,
            destination_budget=self.dest_budget,
            amount_in_cents=25000,
            transfer_date=date(2025, 10, 15),
        )

        expected = "Transfer: Emergency Fund → Vacation - $250.00 on 2025-10-15"
        self.assertEqual(str(transfer), expected)

    def test_str_representation_with_use_funds(self):
        transfer = InternalTransfer.objects.create(
            user=self.user,
            source_budget=self.source_budget,
            destination_budget=None,
            amount_in_cents=30000,
            transfer_date=date(2025, 10, 20),
        )

        expected = "Transfer: Emergency Fund → Used Funds - $300.00 on 2025-10-20"
        self.assertEqual(str(transfer), expected)

    def test_ordering_by_transfer_date_descending(self):
        transfer1 = InternalTransfer.objects.create(
            user=self.user,
            source_budget=self.source_budget,
            destination_budget=self.dest_budget,
            amount_in_cents=10000,
            transfer_date=date(2025, 10, 10),
        )

        transfer2 = InternalTransfer.objects.create(
            user=self.user,
            source_budget=self.source_budget,
            destination_budget=self.dest_budget,
            amount_in_cents=20000,
            transfer_date=date(2025, 10, 20),
        )

        transfer3 = InternalTransfer.objects.create(
            user=self.user,
            source_budget=self.source_budget,
            destination_budget=self.dest_budget,
            amount_in_cents=15000,
            transfer_date=date(2025, 10, 15),
        )

        transfers = list(InternalTransfer.objects.all())

        self.assertEqual(transfers[0], transfer2)
        self.assertEqual(transfers[1], transfer3)
        self.assertEqual(transfers[2], transfer1)

    def test_related_name_outgoing_transfers(self):
        InternalTransfer.objects.create(
            user=self.user,
            source_budget=self.source_budget,
            destination_budget=self.dest_budget,
            amount_in_cents=10000,
            transfer_date=date(2025, 10, 10),
        )

        InternalTransfer.objects.create(
            user=self.user,
            source_budget=self.source_budget,
            destination_budget=None,
            amount_in_cents=5000,
            transfer_date=date(2025, 10, 15),
        )

        outgoing = self.source_budget.outgoing_transfers.all()
        self.assertEqual(outgoing.count(), 2)

    def test_related_name_incoming_transfers(self):
        InternalTransfer.objects.create(
            user=self.user,
            source_budget=self.source_budget,
            destination_budget=self.dest_budget,
            amount_in_cents=10000,
            transfer_date=date(2025, 10, 10),
        )

        other_budget = Budget.objects.create(
            user=self.user,
            type=TransactionType.SAVINGS.name,
            category="Car Fund",
            amount_in_cents=75000,
            budget_year=2025,
            budget_month=10,
        )

        InternalTransfer.objects.create(
            user=self.user,
            source_budget=other_budget,
            destination_budget=self.dest_budget,
            amount_in_cents=15000,
            transfer_date=date(2025, 10, 15),
        )

        incoming = self.dest_budget.incoming_transfers.all()
        self.assertEqual(incoming.count(), 2)

    def test_cascade_delete_when_source_budget_deleted(self):
        transfer = InternalTransfer.objects.create(
            user=self.user,
            source_budget=self.source_budget,
            destination_budget=self.dest_budget,
            amount_in_cents=10000,
            transfer_date=date(2025, 10, 10),
        )

        self.source_budget.delete()

        self.assertFalse(InternalTransfer.objects.filter(id=transfer.id).exists())

    def test_cascade_delete_when_destination_budget_deleted(self):
        transfer = InternalTransfer.objects.create(
            user=self.user,
            source_budget=self.source_budget,
            destination_budget=self.dest_budget,
            amount_in_cents=10000,
            transfer_date=date(2025, 10, 10),
        )

        self.dest_budget.delete()

        self.assertFalse(InternalTransfer.objects.filter(id=transfer.id).exists())
