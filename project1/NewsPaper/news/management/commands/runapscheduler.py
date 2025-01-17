import logging
import datetime
from datetime import timedelta

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from django.conf import settings
from django.core.mail import mail_managers, EmailMultiAlternatives
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django_apscheduler import util
from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.models import DjangoJobExecution
from django.utils import timezone

from news.models import Posts, Category, Subscription

logger = logging.getLogger(__name__)


def my_job():
    today= timezone.now()
    last_week= today - datetime.timedelta(days=7)
    posts = Posts.objects.filter(date_post__gte = last_week)
    categories = set(posts.values_list('postCategory', flat=True))
    subscribers = set(Subscription.objects.filter(Category__in=categories).values_list('user__email', flat=True))
    
    html_content= render_to_string(
        'daily_post.html',
        {
        'link': settings.SITE_URL,
        'posts': posts,
        }
    )
    msg= EmailMultiAlternatives(
        subject= 'Новости этой недели',
        body = " ",
        from_email= settings.DEFAULT_FROM_EMAIL,
        to = subscribers,
    )

    msg.attach_alternative(html_content, 'text/html')
    msg.send()


@util.close_old_connections
def delete_old_job_executions(max_age=604_800):
    DjangoJobExecution.objects.delete_old_job_executions(max_age)


class Command(BaseCommand):
    help = "Runs APScheduler."

    def handle(self, *args, **options):
        scheduler = BlockingScheduler(timezone=settings.TIME_ZONE)
        scheduler.add_jobstore(DjangoJobStore(), "default")

        scheduler.add_job(
            my_job,
            trigger=CronTrigger(minute="00", hour="18"),
            id="my_job",  # The `id` assigned to each job MUST be unique
            max_instances=1,
            replace_existing=True,
        )
        logger.info("Added job 'my_job'.")

        scheduler.add_job(
            delete_old_job_executions,
            trigger=CronTrigger(
                day_of_week="fri", hour="18", minute="00"
            ),
            id="delete_old_job_executions",
            max_instances=1,
            replace_existing=True,
        )
        logger.info("Added weekly job: 'delete_old_job_executions'.")

        try:
            logger.info("Starting scheduler...")
            scheduler.start()
        except KeyboardInterrupt:
            logger.info("Stopping scheduler...")
            scheduler.shutdown()
            logger.info("Scheduler shut down successfully!")