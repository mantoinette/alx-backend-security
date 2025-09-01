import logging
from django.utils.timezone import now
from django.http import HttpResponseForbidden
from .models import RequestLog, BlockedIP

logger = logging.getLogger(__name__)


class IPTrackingMiddleware:
    """
    Middleware to log request IP, path, and timestamp.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip_address = self.get_client_ip(request)
        path = request.path
        timestamp = now()

        try:
            RequestLog.objects.create(
                ip_address=ip_address,
                path=path,
                timestamp=timestamp
            )
            logger.info(f"Logged request from {ip_address} at {timestamp} to {path}")
        except Exception as e:
            logger.error(f"Failed to log request: {e}")

        return self.get_response(request)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip


class BlockIPMiddleware:
    """
    Middleware to block requests from blocked IP addresses.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip = self.get_client_ip(request)
        if BlockedIP.objects.filter(ip_address=ip).exists():
            return HttpResponseForbidden("Your IP is blocked.")
        return self.get_response(request)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR", "")
        return ip
