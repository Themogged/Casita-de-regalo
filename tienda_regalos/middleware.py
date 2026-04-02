from django.conf import settings
from django.contrib.auth.signals import user_login_failed
from django.core.cache import cache
from django.dispatch import receiver
from django.http import HttpResponse


def _client_ip(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")


def _admin_cache_key(ip_address):
    return f"admin-login-attempts:{ip_address}"


@receiver(user_login_failed, dispatch_uid="tienda_regalos_failed_admin_login")
def register_failed_admin_login(sender, credentials, request, **kwargs):
    if request is None or not request.path.startswith("/admin/login/"):
        return

    ip_address = _client_ip(request)
    cache_key = _admin_cache_key(ip_address)
    attempts = cache.get(cache_key, 0) + 1
    timeout = settings.ADMIN_LOGIN_BLOCK_MINUTES * 60
    cache.set(cache_key, attempts, timeout=timeout)


class AdminRateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        is_admin_login = request.path.startswith("/admin/login/")
        cache_key = _admin_cache_key(_client_ip(request))

        if is_admin_login and request.method == "POST":
            attempts = cache.get(cache_key, 0)
            if attempts >= settings.ADMIN_LOGIN_MAX_ATTEMPTS:
                return HttpResponse(
                    "Demasiados intentos de inicio de sesion. Espera unos minutos e intenta de nuevo.",
                    status=429,
                )

        response = self.get_response(request)

        if is_admin_login and request.method == "POST" and response.status_code in {301, 302}:
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
            "font-src 'self' data:",
            "style-src 'self' 'unsafe-inline'",
            "script-src 'self' 'unsafe-inline'",
            "connect-src 'self'",
            "form-action 'self'",
        ]

        response.setdefault("Content-Security-Policy", "; ".join(csp_parts))
        response.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        response.setdefault("Cross-Origin-Resource-Policy", "same-site")
        response.setdefault("X-Permitted-Cross-Domain-Policies", "none")

        return response
