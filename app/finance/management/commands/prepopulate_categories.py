from django.core.management.base import BaseCommand
from finance.models.category import Category


class Command(BaseCommand):
    help = 'Prepopulates the database with predefined expense and income categories'

    def handle(self, *args, **options):
        expense_categories = [
            'Groceries',
            'Utilities',
            'Rent/Mortgage',
            'Subscriptions',
            'Health & Wellness',
            'Travel',
            'Transportation',
            'Bills',
            'Dining Out',
            'Entertainment',
            'Clothing',
            'Home Maintenance',
            'Insurance',
            'Education',
            'Personal Care',
            'Gifts & Donations',
            'Miscellaneous'
        ]

        income_categories = [
            'Salary',
            'Freelance/Side Income',
            'Investment Returns',
            'Gifts Received',
            'Tax Refunds',
            'Emergency Fund',
            'Sinking Fund',
            'Other Income'
        ]

        created_count = 0
        skipped_count = 0
        total_processed = 0

        try:
            for category_name in expense_categories:
                category, created = Category.objects.get_or_create(
                    name=category_name,
                    category_type='expense'
                )
                total_processed += 1
                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'Created expense category: {category_name}')
                    )
                else:
                    skipped_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'Expense category already exists: {category_name}')
                    )

            for category_name in income_categories:
                category, created = Category.objects.get_or_create(
                    name=category_name,
                    category_type='income'
                )
                total_processed += 1
                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'Created income category: {category_name}')
                    )
                else:
                    skipped_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'Income category already exists: {category_name}')
                    )

            self.stdout.write(
                self.style.SUCCESS(
                    f'\nSummary: Processed {total_processed} categories - '
                    f'{created_count} created, {skipped_count} skipped'
                )
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating categories: {str(e)}')
            )
            raise
