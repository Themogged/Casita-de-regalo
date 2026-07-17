from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

from .services import get_cart_for_request


@receiver(user_logged_in)
def merge_cart_after_login(sender, request, user, **kwargs):
    if request is not None:
        # Django's test client (and some custom auth flows) can emit the signal
        # before AuthenticationMiddleware has attached the authenticated user.
        request.user = user
        get_cart_for_request(request)
