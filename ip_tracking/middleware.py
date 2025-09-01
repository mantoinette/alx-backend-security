import logging
from django.utils.timezone import now
from django.http import HttpResponseForbidden
from django.core.cache import cache
from ipgeolocation import IpGeoLocation

from .models import RequestLog, BlockedIP

logger = logging.getLogger(__name__)


class IPTrackingMiddleware:
    """
    Middleware to log request IP, path, timestamp, and geolocation.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.geo = IpGeoLocation()

    def __call__(self, request):
        ip_address = self.get_client_ip(request)
        path = request.path
        timestamp = now()

        # Try to get geolocation from cache
        geo_cache_key = f"geo:{ip_address}"
        geo_data = cache.get(geo_cache_key)

        if not geo_data:
            try:
                geo_data = self.geo.lookup(ip_address)
                # Save only necessary info
                geo_data = {
                    "country": geo_data.get("country_name"),
                    "city": geo_data.get("city")
                }
                cache.set(geo_cache_key, geo_data, timeout=86400)  # 24 hours
                logger.info(f"Geolocation fetched for {ip_address}: {geo_data}")
            except Exception as e:
                logger.error(f"Failed to fetch geolocation for {ip_address}: {e}")
                geo_data = {"country": None, "city": None}

        try:
            RequestLog.objects.create(
                ip_address=ip_address,
                path=path,
                timestamp=timestamp,
                country=geo_data.get("country"),
                city=geo_data.get("city")
            )
            logger.info(
                f"Logged request from {ip_address} ({geo_data.get('country')}, {geo_data.get('city')}) "
                f"at {timestamp} to {path}"
            )
        except Exception as e:
            logger.error(f"Failed to log request: {e}")

        return self.get_response(request)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR", "")
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
