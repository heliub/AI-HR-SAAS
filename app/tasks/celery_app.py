"""
Celery application configuration
"""
from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

# 创建Celery应用
celery_app = Celery(
    "hr_saas",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.resume_tasks",
        "app.tasks.email_tasks",
        "app.tasks.matching_tasks",
        "app.tasks.rpa_tasks",
    ]
)

# Celery配置
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1小时超时
    task_soft_time_limit=3000,  # 50分钟软超时
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# 定时任务配置
celery_app.conf.beat_schedule = {
    'sync-emails-every-5-minutes': {
        'task': 'app.tasks.email_tasks.sync_all_emails',
        'schedule': crontab(minute='*/5'),
    },
    'check-failed-tasks-every-10-minutes': {
        'task': 'app.tasks.task_monitor.check_failed_tasks',
        'schedule': crontab(minute='*/10'),
    },
}

