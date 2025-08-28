from django.contrib import admin
from finance.models import AccountTracker


@admin.register(AccountTracker)
class AccountTrackerAdmin(admin.ModelAdmin):
    list_display = ('account', 'balance', 'created', 'updated')
    list_filter = ('created', 'updated', 'account__owner')
    search_fields = ('account__name', 'account__owner__username')
    readonly_fields = ('id', 'created', 'updated')
    ordering = ('-created',)

    fieldsets = (
        (None, {
            'fields': ('id', 'account', 'balance')
        }),
        ('Timestamps', {
            'fields': ('created', 'updated'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('account', 'account__owner')

    def has_change_permission(self, request, obj=None):
        # Only allow changing balance, not the account
        return True

    def has_delete_permission(self, request, obj=None):
        # Allow deletion for data cleanup
        return True
