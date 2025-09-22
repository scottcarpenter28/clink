from django.contrib import admin
from finance.models import BudgetAllocation


@admin.register(BudgetAllocation)
class BudgetAllocationAdmin(admin.ModelAdmin):
    list_display = ('category', 'budget_display', 'allocated_amount', 'rollover_from_previous', 'spent_amount', 'remaining_amount')
    list_filter = ('category', 'budget__month', 'budget__user')
    search_fields = ('category__name', 'budget__user__username')
    readonly_fields = ('uid', 'created', 'updated', 'spent_amount', 'remaining_amount', 'percent_spent')
    ordering = ('budget__month', 'category__name')

    fieldsets = (
        (None, {
            'fields': ('uid', 'budget', 'category')
        }),
        ('Budget Amounts', {
            'fields': ('allocated_amount', 'rollover_from_previous')
        }),
        ('Calculated Fields', {
            'fields': ('spent_amount', 'remaining_amount', 'percent_spent')
        }),
        ('Timestamps', {
            'fields': ('created', 'updated'),
            'classes': ('collapse',)
        }),
    )

    def budget_display(self, obj):
        return obj.budget.month.strftime('%B %Y')
    budget_display.short_description = 'Budget Month'
    budget_display.admin_order_field = 'budget__month'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('budget', 'category')
