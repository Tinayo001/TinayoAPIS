from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.signals import task_failure

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Mtambo.settings')

# Create Celery app
app = Celery('Mtambo')

# Configure retry on startup
app.conf.broker_connection_retry_on_startup = True

# Additional configurations for reliability
app.conf.update(
    task_track_started=True,
    task_time_limit=30 * 60,
    worker_prefetch_multiplier=1,
    task_always_eager=False,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
)

# Configure Celery using Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Explicitly set timezone for Celery to match Django's timezone setting
app.conf.update(
    timezone='UTC',  # Or use 'django.utils.timezone.get_current_timezone()' for dynamic timezone
    enable_utc=True  # Ensure that UTC is enabled for all times
)

# Auto-discover tasks from all registered Django apps
app.autodiscover_tasks()

# Task failure handler
@task_failure.connect
def handle_task_failure(task_id, exception, traceback, sender, *args, **kwargs):
    print(f'Task {task_id} failed: {exception}\n{traceback}')

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

