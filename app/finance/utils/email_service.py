from django.core.mail import send_mail
from django.contrib.auth.models import User
from django.conf import settings
from finance.models.email_log import EmailLog
from finance.enums.email_enums import EmailType


def send_email_with_logging(
    user: User, email_type: EmailType, subject: str, content: str
) -> bool:
    email_data = {"subject": subject, "content": content, "recipient": user.email}

    try:
        send_mail(
            subject=subject,
            message=content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

        EmailLog.objects.create(
            user=user,
            email_type=email_type.name,
            success=True,
            email_data=email_data,
        )

        return True

    except Exception as e:
        EmailLog.objects.create(
            user=user,
            email_type=email_type.name,
            success=False,
            error_message=str(e),
            email_data=email_data,
        )

        return False
