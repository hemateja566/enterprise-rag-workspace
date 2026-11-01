"""Celery Application Configuration.

Connects Celery to Redis broker and Flask app context.
Used to background PDF ingestion so Flask workers never block.
"""

from celery import Celery

# Broker and backend URLs - configure for production Redis instance
CELERY_BROKER_URL = "redis://localhost:6379/0"
CELERY_RESULT_BACKEND = "redis://localhost:6379/0"

# Optional: Configure task serialization
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]

# Optional: Task time limits (in seconds)
CELERY_TASK_TIME_LIMIT = 300      # 5 minutes hard limit
CELERY_TASK_SOFT_TIME_LIMIT = 240  # 4 minutes soft limit

# Optional: Enable UTC
CELERY_TIMEZONE = "UTC"

# Create Celery app instance
celery_app = Celery(
    "enterprise_rag",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
)

# Apply configuration
celery_app.conf.update(
    task_serializer=CELERY_TASK_SERIALIZER,
    result_serializer=CELERY_RESULT_SERIALIZER,
    accept_content=CELERY_ACCEPT_CONTENT,
    task_time_limit=CELERY_TASK_TIME_LIMIT,
    task_soft_time_limit=CELERY_TASK_SOFT_TIME_LIMIT,
    timezone=CELERY_TIMEZONE,
)


def init_celery_with_flask_app(app):
    """Initialize Celery with a Flask application context.

    Ensures every Celery task runs within the Flask app context,
    allowing access to db, current_app, etc.

    Usage in app factory:
        from celery.config import init_celery_with_flask_app
        celery = init_celery_with_flask_app(app)
    """
    class ContextTask(celery_app.Task):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return super().__call__(*args, **kwargs)

    celery_app.Task = ContextTask
    return celery_app