from django.contrib.auth.models import User


def build_reminder_email_subject() -> str:
    return "Reminder: Log Your Expenses This Week"


def build_reminder_email_content(user: User) -> str:
    return f"""Hello {user.first_name or user.username},

We noticed you haven't logged any expenses in the past 7 days.

Keeping track of your spending helps you stay on top of your financial goals. Take a moment to add any recent expenses you may have forgotten.

If you've already logged everything, great job staying organized!

Best regards,
Clink Finance Team

---

To manage your email preferences, log in to your account and visit your settings page.
"""
