import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lims.settings')

app = Celery('lims', broker='redis://localhost', backend='redis')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'process-deadlines': {
        'task': 'lims.projects.tasks.process_deadlines',
        'schedule': crontab(minute=0, hour='*/3'),
    }
}
