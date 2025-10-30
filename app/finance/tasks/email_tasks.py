from celery import shared_task

from finance.emails.weekly_reminder.queries import get_users_needing_reminders
from finance.emails.weekly_reminder.content import (
    build_reminder_email_subject,
    build_reminder_email_content,
)
from finance.emails.weekly_summary.queries import get_users_needing_weekly_summary
from finance.emails.weekly_summary.calculations import calculate_weekly_totals
from finance.emails.weekly_summary.content import (
    build_weekly_summary_subject,
    build_weekly_summary_content,
)
from finance.utils.email_service import send_email_with_logging
from finance.enums.email_enums import EmailType


@shared_task
def send_weekly_reminders() -> dict[str, int]:
    users = get_users_needing_reminders()
    sent_count = 0
    failed_count = 0

    for user in users:
        subject = build_reminder_email_subject()
        content = build_reminder_email_content(user)

        success = send_email_with_logging(
            user=user,
            email_type=EmailType.WEEKLY_REMINDER,
            subject=subject,
            content=content,
        )

        if success:
            sent_count += 1
        else:
            failed_count += 1

    return {"sent": sent_count, "failed": failed_count}


@shared_task
def send_weekly_summaries() -> dict[str, int]:
    users = get_users_needing_weekly_summary()
    sent_count = 0
    failed_count = 0

    for user in users:
        summary_data = calculate_weekly_totals(user)
        subject = build_weekly_summary_subject()
        content = build_weekly_summary_content(user, summary_data)

        success = send_email_with_logging(
            user=user,
            email_type=EmailType.WEEKLY_SUMMARY,
            subject=subject,
            content=content,
        )

        if success:
            sent_count += 1
        else:
            failed_count += 1

    return {"sent": sent_count, "failed": failed_count}
