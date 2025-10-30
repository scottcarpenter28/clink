from django.contrib.auth.models import User
from django.db.models import QuerySet
from django.utils import timezone
from datetime import timedelta


def get_users_needing_weekly_summary() -> QuerySet[User]:
    seven_days_ago = timezone.now() - timedelta(days=7)

    users_with_recent_transactions = User.objects.filter(
        transaction__date_of_expense__gte=seven_days_ago.date()
    ).values_list("id", flat=True)

    return (
        User.objects.filter(
            email_settings__weekly_summary_enabled=True,
            email__isnull=False,
            id__in=users_with_recent_transactions,
        )
        .exclude(email="")
        .distinct()
    )
