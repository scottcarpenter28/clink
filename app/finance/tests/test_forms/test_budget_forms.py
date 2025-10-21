from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from finance.forms import (
    BudgetItemForm,
    MultiBudgetForm,
    BudgetItemFormSet,
    InternalTransferForm,
)
from finance.models import Budget
from finance.enums import TransactionType


class BudgetItemFormTests(TestCase):
    def test_valid_budget_item_form(self):
        data = {
            "type": TransactionType.INCOME.name,
            "category": "Salary",
            "amount": "1956.40",
        }
        form = BudgetItemForm(data=data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["type"], TransactionType.INCOME.name)
        self.assertEqual(form.cleaned_data["category"], "Salary")
        self.assertEqual(float(form.cleaned_data["amount"]), 1956.40)

    def test_negative_amount_fails(self):
        data = {
            "type": TransactionType.NEED.name,
            "category": "Housing",
            "amount": "-100.00",
        }
        form = BudgetItemForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("amount", form.errors)

    def test_zero_amount_fails(self):
        data = {
            "type": TransactionType.NEED.name,
            "category": "Housing",
            "amount": "0.00",
        }
        form = BudgetItemForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("amount", form.errors)

    def test_invalid_amount_format(self):
        data = {
            "type": TransactionType.NEED.name,
            "category": "Housing",
            "amount": "invalid",
        }
        form = BudgetItemForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("amount", form.errors)

    def test_invalid_type(self):
        data = {"type": "INVALID_TYPE", "category": "Housing", "amount": "100.00"}
        form = BudgetItemForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("type", form.errors)

    def test_missing_required_fields(self):
        data = {}
        form = BudgetItemForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("type", form.errors)
        self.assertIn("category", form.errors)
        self.assertIn("amount", form.errors)

    def test_category_max_length(self):
        data = {
            "type": TransactionType.NEED.name,
            "category": "A" * 101,
            "amount": "100.00",
        }
        form = BudgetItemForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("category", form.errors)


class MultiBudgetFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

    def test_valid_multi_budget_form_with_multiple_items(self):
        data = {
            "year": 2025,
            "month": 10,
            "budgets": [
                {
                    "type": TransactionType.INCOME.name,
                    "category": "Salary",
                    "amount": 1956.40,
                },
                {
                    "type": TransactionType.NEED.name,
                    "category": "Housing",
                    "amount": 800.00,
                },
            ],
        }
        form = MultiBudgetForm(data=data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["year"], 2025)
        self.assertEqual(form.cleaned_data["month"], 10)

    def test_invalid_year_too_low(self):
        data = {
            "year": 1899,
            "month": 10,
            "budgets": [
                {
                    "type": TransactionType.INCOME.name,
                    "category": "Salary",
                    "amount": 1000.00,
                }
            ],
        }
        form = MultiBudgetForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("year", form.errors)

    def test_invalid_month_zero(self):
        data = {
            "year": 2025,
            "month": 0,
            "budgets": [
                {
                    "type": TransactionType.INCOME.name,
                    "category": "Salary",
                    "amount": 1000.00,
                }
            ],
        }
        form = MultiBudgetForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("month", form.errors)

    def test_invalid_month_thirteen(self):
        data = {
            "year": 2025,
            "month": 13,
            "budgets": [
                {
                    "type": TransactionType.INCOME.name,
                    "category": "Salary",
                    "amount": 1000.00,
                }
            ],
        }
        form = MultiBudgetForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("month", form.errors)

    def test_invalid_month_negative(self):
        data = {
            "year": 2025,
            "month": -1,
            "budgets": [
                {
                    "type": TransactionType.INCOME.name,
                    "category": "Salary",
                    "amount": 1000.00,
                }
            ],
        }
        form = MultiBudgetForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("month", form.errors)

    def test_empty_budget_items_fails(self):
        data = {"year": 2025, "month": 10, "budgets": []}
        form = MultiBudgetForm(data=data)
        self.assertFalse(form.is_valid())

    def test_duplicate_category_type_combination_fails(self):
        data = {
            "year": 2025,
            "month": 10,
            "budgets": [
                {
                    "type": TransactionType.NEED.name,
                    "category": "Housing",
                    "amount": 800.00,
                },
                {
                    "type": TransactionType.NEED.name,
                    "category": "Housing",
                    "amount": 900.00,
                },
            ],
        }
        form = MultiBudgetForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("Duplicate entry found", str(form.errors))

    def test_same_category_different_type_is_valid(self):
        data = {
            "year": 2025,
            "month": 10,
            "budgets": [
                {
                    "type": TransactionType.NEED.name,
                    "category": "Transportation",
                    "amount": 200.00,
                },
                {
                    "type": TransactionType.WANT.name,
                    "category": "Transportation",
                    "amount": 100.00,
                },
            ],
        }
        form = MultiBudgetForm(data=data)
        self.assertTrue(form.is_valid())


class MultiBudgetFormSaveTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

    def test_save_creates_new_budgets(self):
        data = {
            "year": 2025,
            "month": 10,
            "budgets": [
                {
                    "type": TransactionType.INCOME.name,
                    "category": "Salary",
                    "amount": 1956.40,
                },
                {
                    "type": TransactionType.NEED.name,
                    "category": "Housing",
                    "amount": 800.00,
                },
            ],
        }
        form = MultiBudgetForm(data=data)
        self.assertTrue(form.is_valid())

        budgets = form.save(self.user)

        self.assertEqual(len(budgets), 2)
        self.assertEqual(Budget.objects.filter(user=self.user).count(), 2)

        salary_budget = Budget.objects.get(user=self.user, category="Salary")
        self.assertEqual(salary_budget.amount_in_cents, 195640)
        self.assertEqual(salary_budget.type, TransactionType.INCOME.name)
        self.assertEqual(salary_budget.budget_year, 2025)
        self.assertEqual(salary_budget.budget_month, 10)

        housing_budget = Budget.objects.get(user=self.user, category="Housing")
        self.assertEqual(housing_budget.amount_in_cents, 80000)

    def test_save_updates_existing_budgets(self):
        Budget.from_dollars(
            dollar_amount=1000.00,
            user=self.user,
            type=TransactionType.INCOME.name,
            category="Salary",
            budget_year=2025,
            budget_month=10,
        ).save()

        self.assertEqual(Budget.objects.count(), 1)

        data = {
            "year": 2025,
            "month": 10,
            "budgets": [
                {
                    "type": TransactionType.INCOME.name,
                    "category": "Salary",
                    "amount": 1956.40,
                },
            ],
        }
        form = MultiBudgetForm(data=data)
        self.assertTrue(form.is_valid())

        budgets = form.save(self.user)

        self.assertEqual(len(budgets), 1)
        self.assertEqual(Budget.objects.filter(user=self.user).count(), 1)

        salary_budget = Budget.objects.get(user=self.user, category="Salary")
        self.assertEqual(salary_budget.amount_in_cents, 195640)

    def test_save_handles_multiple_items(self):
        data = {
            "year": 2025,
            "month": 10,
            "budgets": [
                {
                    "type": TransactionType.INCOME.name,
                    "category": "Salary",
                    "amount": 1956.40,
                },
                {
                    "type": TransactionType.NEED.name,
                    "category": "Housing",
                    "amount": 800.00,
                },
                {
                    "type": TransactionType.WANT.name,
                    "category": "Entertainment",
                    "amount": 150.00,
                },
            ],
        }
        form = MultiBudgetForm(data=data)
        self.assertTrue(form.is_valid())

        budgets = form.save(self.user)

        self.assertEqual(len(budgets), 3)
        self.assertEqual(Budget.objects.filter(user=self.user).count(), 3)

    def test_save_associates_with_correct_user(self):
        user2 = User.objects.create_user(
            username="testuser2", email="test2@example.com", password="testpass123"
        )

        data = {
            "year": 2025,
            "month": 10,
            "budgets": [
                {
                    "type": TransactionType.INCOME.name,
                    "category": "Salary",
                    "amount": 1000.00,
                },
            ],
        }
        form = MultiBudgetForm(data=data)
        self.assertTrue(form.is_valid())

        budgets = form.save(self.user)

        self.assertEqual(Budget.objects.filter(user=self.user).count(), 1)
        self.assertEqual(Budget.objects.filter(user=user2).count(), 0)
        self.assertEqual(budgets[0].user, self.user)

    def test_save_converts_dollars_to_cents_correctly(self):
        data = {
            "year": 2025,
            "month": 10,
            "budgets": [
                {
                    "type": TransactionType.INCOME.name,
                    "category": "Salary",
                    "amount": 1234.56,
                },
            ],
        }
        form = MultiBudgetForm(data=data)
        self.assertTrue(form.is_valid())

        budgets = form.save(self.user)

        self.assertEqual(budgets[0].amount_in_cents, 123456)
        self.assertEqual(budgets[0].amount_dollars, 1234.56)

    def test_save_returns_budget_instances(self):
        data = {
            "year": 2025,
            "month": 10,
            "budgets": [
                {
                    "type": TransactionType.INCOME.name,
                    "category": "Salary",
                    "amount": 1000.00,
                },
            ],
        }
        form = MultiBudgetForm(data=data)
        self.assertTrue(form.is_valid())

        budgets = form.save(self.user)

        self.assertIsInstance(budgets, list)
        self.assertIsInstance(budgets[0], Budget)

    def test_save_invalid_form_raises_error(self):
        data = {"year": 2025, "month": 13, "budgets": []}
        form = MultiBudgetForm(data=data)
        self.assertFalse(form.is_valid())

        with self.assertRaises(ValueError):
            form.save(self.user)


class BudgetItemFormCarryOverTests(TestCase):
    def test_budget_item_form_includes_allow_carry_over_field(self):
        form = BudgetItemForm()
        self.assertIn("allow_carry_over", form.fields)

    def test_allow_carry_over_is_optional(self):
        data = {
            "type": TransactionType.SAVINGS.name,
            "category": "Emergency Fund",
            "amount": "1000.00",
        }
        form = BudgetItemForm(data=data)
        self.assertTrue(form.is_valid())

    def test_allow_carry_over_defaults_to_false(self):
        data = {
            "type": TransactionType.SAVINGS.name,
            "category": "Emergency Fund",
            "amount": "1000.00",
        }
        form = BudgetItemForm(data=data)
        self.assertTrue(form.is_valid())
        self.assertFalse(form.cleaned_data.get("allow_carry_over", False))

    def test_allow_carry_over_can_be_set_to_true(self):
        data = {
            "type": TransactionType.SAVINGS.name,
            "category": "Emergency Fund",
            "amount": "1000.00",
            "allow_carry_over": True,
        }
        form = BudgetItemForm(data=data)
        self.assertTrue(form.is_valid())
        self.assertTrue(form.cleaned_data["allow_carry_over"])


class InternalTransferFormTests(TestCase):
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

    def test_valid_internal_transfer_form(self):
        data = {
            "source_budget_id": self.source_budget.id,
            "destination_budget_id": self.dest_budget.id,
            "amount": "200.00",
            "transfer_date": "2025-10-15",
            "description": "Moving funds",
        }
        form = InternalTransferForm(data=data)
        self.assertTrue(form.is_valid())

    def test_transfer_to_use_funds_with_empty_destination(self):
        data = {
            "source_budget_id": self.source_budget.id,
            "destination_budget_id": "",
            "amount": "150.00",
            "transfer_date": "2025-10-15",
        }
        form = InternalTransferForm(data=data)
        self.assertTrue(form.is_valid())
        self.assertIsNone(form.cleaned_data["destination_budget_id"])

    def test_negative_amount_fails(self):
        data = {
            "source_budget_id": self.source_budget.id,
            "destination_budget_id": self.dest_budget.id,
            "amount": "-50.00",
            "transfer_date": "2025-10-15",
        }
        form = InternalTransferForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("amount", form.errors)

    def test_zero_amount_fails(self):
        data = {
            "source_budget_id": self.source_budget.id,
            "destination_budget_id": self.dest_budget.id,
            "amount": "0.00",
            "transfer_date": "2025-10-15",
        }
        form = InternalTransferForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("amount", form.errors)

    def test_invalid_source_budget_id_fails(self):
        data = {
            "source_budget_id": 99999,
            "destination_budget_id": self.dest_budget.id,
            "amount": "100.00",
            "transfer_date": "2025-10-15",
        }
        form = InternalTransferForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("source_budget_id", form.errors)

    def test_same_source_and_destination_fails(self):
        data = {
            "source_budget_id": self.source_budget.id,
            "destination_budget_id": self.source_budget.id,
            "amount": "100.00",
            "transfer_date": "2025-10-15",
        }
        form = InternalTransferForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn(
            "Source and destination budgets cannot be the same", str(form.errors)
        )

    def test_transfer_from_income_budget_fails(self):
        income_budget = Budget.objects.create(
            user=self.user,
            type=TransactionType.INCOME.name,
            category="Salary",
            amount_in_cents=500000,
            budget_year=2025,
            budget_month=10,
        )

        data = {
            "source_budget_id": income_budget.id,
            "destination_budget_id": self.dest_budget.id,
            "amount": "100.00",
            "transfer_date": "2025-10-15",
        }
        form = InternalTransferForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("source_budget_id", form.errors)

    def test_missing_required_fields(self):
        data = {}
        form = InternalTransferForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("source_budget_id", form.errors)
        self.assertIn("amount", form.errors)
        self.assertIn("transfer_date", form.errors)

    def test_description_is_optional(self):
        data = {
            "source_budget_id": self.source_budget.id,
            "destination_budget_id": self.dest_budget.id,
            "amount": "100.00",
            "transfer_date": "2025-10-15",
        }
        form = InternalTransferForm(data=data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data.get("description", ""), "")
