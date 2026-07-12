print("=== celery.py LOADED ===")
from celery import Celery
from celery.schedules import crontab

from config.dependencies.core import get_settings

settings = get_settings()

redis_host = settings.REDIS_HOST
redis_port = settings.REDIS_PORT
redis_db = settings.REDIS_DB

broker_url = f"redis://{redis_host}:{redis_port}/{redis_db}"
backend_url = f"redis://{redis_host}:{redis_port}/{redis_db}"

print("BROKER_URL (celery.py):", broker_url)

celery_app = Celery("online_cinema_service", broker=broker_url, backend=backend_url)

from tasks import emails

celery_app.autodiscover_tasks(["tasks.emails"])

celery_app.conf.beat_schedule = {
    "cleanup-expired-activation-tokens": {
        "task": "tasks.emails.delete_expired_activation_tokens",
        "schedule": crontab(minute=0),
    },
}
