from django.conf import settings
from django.contrib.auth.signals import user_login_failed
from django.core.cache import cache
from django.dispatch import receiver
from django.http import HttpResponse


def client_ip(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if settings.TRUST_X_FORWARDED_FOR and forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")


def _admin_cache_key(ip_address):
    return f"admin-login-attempts:{ip_address}"


def _customer_cache_key(ip_address):
    return f"customer-login-attempts:{ip_address}"


@receiver(user_login_failed, dispatch_uid="tienda_regalos_failed_login")
def register_failed_login(sender, credentials, request, **kwargs):
    if request is None:
        return
    if request.path.startswith("/admin/login/"):
        cache_key = _admin_cache_key(client_ip(request))
        timeout = settings.ADMIN_LOGIN_BLOCK_MINUTES * 60
    elif request.path.startswith("/cuenta/ingresar/"):
        cache_key = _customer_cache_key(client_ip(request))
        timeout = settings.CUSTOMER_LOGIN_BLOCK_MINUTES * 60
    else:
        return
    cache.set(cache_key, cache.get(cache_key, 0) + 1, timeout=timeout)


class AdminRateLimitMiddleware:
    """Limits both staff and customer login attempts without storing credentials."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        is_admin_login = request.path.startswith("/admin/login/")
        is_customer_login = request.path.startswith("/cuenta/ingresar/")
        if is_admin_login:
            cache_key = _admin_cache_key(client_ip(request))
            limit = settings.ADMIN_LOGIN_MAX_ATTEMPTS
            retry_after = settings.ADMIN_LOGIN_BLOCK_MINUTES * 60
        elif is_customer_login:
            cache_key = _customer_cache_key(client_ip(request))
            limit = settings.CUSTOMER_LOGIN_MAX_ATTEMPTS
            retry_after = settings.CUSTOMER_LOGIN_BLOCK_MINUTES * 60
        else:
            cache_key = None
            limit = 0
            retry_after = 0

        if cache_key and request.method == "POST" and cache.get(cache_key, 0) >= limit:
            response = HttpResponse(
                "Demasiados intentos de inicio de sesión. Espera unos minutos e intenta de nuevo.",
                status=429,
            )
            response["Retry-After"] = str(retry_after)
            return response

        response = self.get_response(request)
        if cache_key and request.method == "POST" and response.status_code in {301, 302}:
            cache.delete(cache_key)
        return response


class SecurityHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        csp_parts = [
            "default-src 'self'",
            "base-uri 'self'",
            "object-src 'none'",
            "frame-ancestors 'none'",
            "img-src 'self' data:",
            "media-src 'self'",
            "font-src 'self' data: https://fonts.gstatic.com",
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
            "script-src 'self' 'unsafe-inline'",
            "connect-src 'self'",
            "form-action 'self'",
        ]
        response.setdefault("Content-Security-Policy", "; ".join(csp_parts))
        response.setdefault("Referrer-Policy", settings.SECURE_REFERRER_POLICY)
        response.setdefault("X-Content-Type-Options", "nosniff")
        response.setdefault("X-Frame-Options", "DENY")
        response.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        response.setdefault("Cross-Origin-Resource-Policy", "same-site")
        response.setdefault("X-Permitted-Cross-Domain-Policies", "none")
        response.setdefault("Origin-Agent-Cluster", "?1")

        if request.path.startswith(("/admin/", "/cuenta/", "/carrito/")):
            response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response["Pragma"] = "no-cache"
            response["Expires"] = "0"
        return response
