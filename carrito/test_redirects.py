from django.test import RequestFactory, SimpleTestCase
from django.urls import reverse

from .views import _redirect_after_add


class CartRedirectTests(SimpleTestCase):
    def test_external_or_unsafe_referer_stays_in_catalog(self):
        for referer in ('https://example.com/offer/', '//example.com/offer/', 'javascript:alert(1)', 'http://testserver/producto/1/'):
            with self.subTest(referer=referer):
                request = RequestFactory().post('/carrito/agregar/1/', secure=True, HTTP_REFERER=referer)
                self.assertEqual(_redirect_after_add(request).url, reverse('catalogo') + '#catalogo')

    def test_same_site_product_referer_is_preserved(self):
        referer = 'https://testserver/producto/1/'
        request = RequestFactory().post('/carrito/agregar/1/', secure=True, HTTP_REFERER=referer)
        self.assertEqual(_redirect_after_add(request).url, referer)
