# Arquitectura

## Aplicaciones

- `productos`: catálogo, fichas, videos, SEO comercial y recomendaciones.
- `carrito`: lista persistente, variantes personalizadas y checkout por WhatsApp.
- `pedidos`: registro de pedidos y sus líneas finales.
- `cuentas`: registro, acceso, perfil y recuperación de contraseña.
- `asistente`: conversación y memoria opcional de Cora.
- `tienda_regalos`: configuración, seguridad, SEO técnico y telemetría.

## Decisiones principales

### Líneas configurables

`CarritoItem.configuration_key` es un SHA-256 de datos normalizados. No contiene secretos y evita comparar archivos o textos de forma ambigua. La sesión heredada conserva solo cantidades agregadas por producto; la base de datos es la fuente de verdad para variantes.

### Archivos de cliente

Las imágenes usan nombres UUID, límite de 5 MB, verificación de Pillow, formatos permitidos y límite de píxeles. No se versionan en Git.

### Telemetría

`POST /eventos/` acepta una lista cerrada de nombres y propiedades. Descarta parámetros de URL y campos desconocidos, limita frecuencia y registra un identificador irreversible de corta longitud derivado de IP más secreto del servidor.

### Multimedia

El comando `optimize_media_images` crea WebP principal y variantes responsive. El navegador recibe fallback normal si esas variantes todavía no existen. Los videos no críticos hidratan su fuente cuando son visibles.
