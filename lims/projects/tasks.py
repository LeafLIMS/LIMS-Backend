from celery import shared_task

from .models import Project


@shared_task
def process_deadlines():
    with_deadlines = Project.objects.filter(deadline__isnull=False)
    for p in with_deadlines:
        if p.past_deadline() and p.deadline_status != 'Past':
            p.deadline_status = 'Past'
            p.save()
        elif p.warn_deadline() and p.deadline_status != 'Warn':
            p.deadline_status = 'Warn'
            p.save()
