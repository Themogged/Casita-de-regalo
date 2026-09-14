import json
from pathlib import Path
from unittest import mock

from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from .models import Producto
from .templatetags.media_optimization import optimized_image_url, responsive_image_srcset
from .views import _build_product_schema


class StructuredDataSafetyTests(SimpleTestCase):
    def test_product_json_cannot_close_its_script_element(self):
        name = '</script><script>alert("test")</script> & regalo'
        product = Producto(id=1, nombre=name, descripcion=name, precio='125000', stock=1)
        serialized = _build_product_schema(RequestFactory().get('/'), product)

        self.assertNotIn('<', serialized)
        self.assertNotIn('>', serialized)
        self.assertEqual(json.loads(serialized)['name'], name)


class ImageUrlTests(SimpleTestCase):
    def test_encoded_names_use_existing_optimized_images(self):
        existing = {'caja corazón.webp', 'caja corazón-360w.webp'}
        with override_settings(MEDIA_ROOT='C:/media'), mock.patch.object(
            Path, 'exists', autospec=True, side_effect=lambda path: path.name in existing
        ):
            url = '/media/caja%20coraz%C3%B3n.jpeg'
            self.assertEqual(optimized_image_url(url), '/media/caja%20coraz%C3%B3n.webp')
            self.assertEqual(responsive_image_srcset(url), '/media/caja%20coraz%C3%B3n-360w.webp 360w')

    def test_outside_media_and_missing_variants_keep_original(self):
        for url in ('https://example.com/image.jpg', '/media/%2e%2e/private.jpg', '/media/missing.jpg'):
            with self.subTest(url=url):
                self.assertEqual(optimized_image_url(url), url)
                self.assertEqual(responsive_image_srcset(url), '')


class PublicPageRegressionTests(TestCase):
    def test_catalog_handles_oversized_and_unicode_filters(self):
        for params in ({'categoria': '9' * 80}, {'categoria': '\u00b2'}, {'q': 'menos ' + '9' * 400}, {'q': 'menos \u00b2'}):
            with self.subTest(params=params):
                self.assertEqual(self.client.get(reverse('catalogo'), params).status_code, 200)

    def test_product_page_starts_in_standards_mode(self):
        product = Producto.objects.create(nombre='Regalo de prueba', precio=1000, stock=1)
        response = self.client.get(reverse('detalle_producto', args=[product.pk]))
        self.assertTrue(response.content.lstrip().lower().startswith(b'<!doctype html>'))

    def test_private_pages_are_not_indexed(self):
        response = self.client.get(reverse('login'))
        self.assertContains(response, 'content="noindex, follow"')

    def test_public_pages_have_share_image_metadata(self):
        response = self.client.get(reverse('inicio'))
        self.assertContains(response, 'property="og:image"')
        self.assertContains(response, 'brand-casita-icon-512.png')

    def test_paginated_catalog_has_its_own_canonical(self):
        response = self.client.get(reverse('catalogo'), {'page': '2'})
        self.assertContains(response, 'rel="canonical" href="http://testserver/catalogo/?page=2"')

    def test_customer_image_preview_is_allowed_by_csp(self):
        response = self.client.get(reverse('inicio'))
        image_policy = next(part for part in response['Content-Security-Policy'].split(';') if 'img-src' in part)
        self.assertIn('blob:', image_policy)
