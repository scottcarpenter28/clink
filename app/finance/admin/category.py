from django.contrib import admin
from finance.models import Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category_type', 'created', 'updated')
    list_filter = ('category_type', 'created', 'updated')
    search_fields = ('name',)
    readonly_fields = ('id', 'created', 'updated')
    ordering = ('category_type', 'name')

    fieldsets = (
        (None, {
            'fields': ('id', 'name', 'category_type')
        }),
        ('Timestamps', {
            'fields': ('created', 'updated'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request)

    # Custom action to quickly create common categories
    actions = ['create_common_expense_categories', 'create_common_income_categories']

    def create_common_expense_categories(self, request, queryset):
        common_expenses = [
            'Food & Dining', 'Transportation', 'Shopping', 'Entertainment',
            'Bills & Utilities', 'Healthcare', 'Education', 'Travel',
            'Business Services', 'Personal Care', 'Gifts & Donations'
        ]
        created_count = 0
        for category_name in common_expenses:
            category, created = Category.objects.get_or_create(
                name=category_name,
                defaults={'category_type': 'expense'}
            )
            if created:
                created_count += 1

        self.message_user(request, f"Created {created_count} new expense categories.")

    create_common_expense_categories.short_description = "Create common expense categories"

    def create_common_income_categories(self, request, queryset):
        common_income = [
            'Salary', 'Freelance', 'Investment', 'Business Income',
            'Rental Income', 'Interest', 'Dividends', 'Other Income'
        ]
        created_count = 0
        for category_name in common_income:
            category, created = Category.objects.get_or_create(
                name=category_name,
                defaults={'category_type': 'income'}
            )
            if created:
                created_count += 1

        self.message_user(request, f"Created {created_count} new income categories.")

    create_common_income_categories.short_description = "Create common income categories"
