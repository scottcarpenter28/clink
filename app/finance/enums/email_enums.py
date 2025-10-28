from enum import Enum


class EmailType(Enum):
    WEEKLY_REMINDER = "Weekly Reminder"
    WEEKLY_SUMMARY = "Weekly Summary"
    MONTHLY_SUMMARY = "Monthly Summary"
    YEARLY_SUMMARY = "Yearly Summary"
