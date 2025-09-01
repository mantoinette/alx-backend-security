from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    "flag-suspicious-ips-hourly": {
        "task": "ip_tracking.tasks.flag_suspicious_ips",
        "schedule": crontab(minute=0, hour="*"),  # every hour
    },
}
