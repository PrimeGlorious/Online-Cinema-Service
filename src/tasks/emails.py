print("=== tasks/emails.py LOADED ===")

from config.settings import Settings
from celery import shared_task
import asyncio

from database import ActivationTokenModel
from database.session_postgresql import SessionLocal
from config.dependencies.core import get_settings
from tasks.celery import broker_url
from config.dependencies.core import get_accounts_email_notificator

print("BROKER_URL (emails.py):", broker_url)


@shared_task
def send_activation_email_task(email: str, activation_link: str):
    """
    Celery task to send account activation email using EmailSender.
    """
    settings = get_settings()
    sender = get_accounts_email_notificator(settings)
    asyncio.run(sender.send_activation_email(email, activation_link))


@shared_task
def send_activation_complete_email_task(email: str, login_link: str):
    settings = get_settings()
    sender = get_accounts_email_notificator(settings)
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


@shared_task
def send_password_reset_email_task(email: str, reset_link: str):
    settings = get_settings()
    sender = get_accounts_email_notificator(settings)
    asyncio.run(sender.send_password_reset_email(email, reset_link))


@shared_task
def send_password_reset_complete_email_task(email: str, login_link: str):
    settings = get_settings()
    sender = get_accounts_email_notificator(settings)
    asyncio.run(sender.send_password_reset_complete_email(email, login_link))
