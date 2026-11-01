#!/usr/bin/env python3
"""Celery Configuration for Enterprise RAG Workspace.

Sets up Celery with Flask application context integration.

Usage in Flask app:
    from celery import Celery
    from celery.config import import_from_celery_config

    def make_celery(app):
        celery = Celery(
            import_name=__name__,
            broker=app.config["CELERY_BROKER_URL"],
            result_backend=app.config["CELERY_RESULT_BACKEND"],
        )
        celery.conf.update(app.config.get("CELERY_CONFIG", {}))
        TaskBase = celery.Task
        class ContextTask(TaskBase):
            abstract = True
            def __call__(self, *args, **kwargs):
                with app.app_context():
                    return TaskBase.__call__(self, *args, **kwargs)
        celery.Task = ContextTask
        return celery