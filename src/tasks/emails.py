print("=== tasks/emails.py LOADED ===")

from celery import shared_task
import asyncio

from database import ActivationTokenModel
from database.session_postgresql import SessionLocal
from notifications.emails import EmailSender
from config.dependencies.core import get_settings
from tasks.celery import broker_url

print("BROKER_URL (emails.py):", broker_url)

def get_sender(settings):
    return EmailSender(
        hostname=settings.EMAIL_HOST,
        port=settings.EMAIL_PORT,
        email=settings.EMAIL_HOST_USER,
        password=settings.EMAIL_HOST_PASSWORD,
        use_tls=settings.EMAIL_USE_TLS,
        template_dir=settings.PATH_TO_EMAIL_TEMPLATES_DIR,
        activation_email_template_name=settings.ACTIVATION_EMAIL_TEMPLATE_NAME,
        activation_complete_email_template_name=settings.ACTIVATION_COMPLETE_EMAIL_TEMPLATE_NAME,
        password_email_template_name=settings.PASSWORD_RESET_TEMPLATE_NAME,
        password_complete_email_template_name=settings.PASSWORD_RESET_COMPLETE_TEMPLATE_NAME,
    )

@shared_task
def send_activation_email_task(email: str, activation_link: str):
    """
    Celery task to send account activation email using EmailSender.
    """
    settings = get_settings()
    sender = get_sender(settings)
    # Run async send_activation_email in sync context
    asyncio.run(sender.send_activation_email(email, activation_link))


@shared_task
def send_activation_complete_email_task(email: str, login_link: str):
    settings = get_settings()
    sender = get_sender(settings)
    asyncio.run(sender.send_activation_complete_email(email, login_link))


@shared_task
def delete_expired_activation_tokens():
    from datetime import datetime, timezone
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        db.query(ActivationTokenModel) \
          .filter(ActivationTokenModel.expires_at < now) \
          .delete(synchronize_session=False)
        db.commit()
    finally:
        db.close()
