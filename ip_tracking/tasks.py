from datetime import timedelta
from django.utils.timezone import now
from celery import shared_task
from .models import RequestLog, SuspiciousIP

SENSITIVE_PATHS = ["/admin", "/login"]


@shared_task
def flag_suspicious_ips():
    """
    Runs hourly:
    - Flags IPs exceeding 100 requests in the past hour
    - Flags IPs accessing sensitive paths (/admin, /login)
    """
    one_hour_ago = now() - timedelta(hours=1)

    # Check for IPs exceeding 100 requests/hour
    request_counts = (
        RequestLog.objects.filter(timestamp__gte=one_hour_ago)
        .values("ip_address")
        .annotate(count=models.Count("id"))
        .filter(count__gt=100)
    )

    for entry in request_counts:
        ip = entry["ip_address"]
        SuspiciousIP.objects.get_or_create(
            ip_address=ip, reason="Exceeded 100 requests/hour"
        )

    # Check for access to sensitive paths
    sensitive_logs = RequestLog.objects.filter(
        timestamp__gte=one_hour_ago, path__in=SENSITIVE_PATHS
    ).values("ip_address", "path")

    for log in sensitive_logs:
        SuspiciousIP.objects.get_or_create(
            ip_address=log["ip_address"],
            reason=f"Accessed sensitive path: {log['path']}",
        )
