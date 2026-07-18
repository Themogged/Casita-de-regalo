# Informe de implementación

Fecha de cierre técnico: 17 de julio de 2026.

## Fase 1: identidad y cuentas

- Sistema de marca SVG con isotipo, versión circular, horizontal y favicon.
- Identidad aplicada en acceso, registro, perfil y seguridad de la cuenta.
- Cambio de contraseña dentro de la sesión, con validación de la clave actual y sin servicios de correo externos.
- Campo señuelo en registro y límites de intentos para accesos administrativos y de clientes.

## Fase 2: Cora

- Voz opcional mediante `SpeechSynthesis`, desactivada de forma predeterminada.
- Selección preferente de voces en español y persistencia de la preferencia.
- Controles para activar, pausar, reanudar y silenciar.
- Cancelación de voz al cerrar el panel o abandonar la página.
- Degradación silenciosa cuando el navegador no ofrece síntesis de voz.

## Fase 3: medios, rendimiento y accesibilidad

- Imágenes responsivas WebP con `srcset`, `sizes`, carga diferida y prioridad para el contenido principal.
- Comando de generación de derivados: `python manage.py optimize_media_images --path media --quality 78`.
- Videos automáticos silenciados, sin controles nativos, con controles accesibles propios.
- Pausa fuera de pantalla, una sola reproducción activa y respeto por ahorro de datos y movimiento reducido.
- Enlace para saltar al contenido, foco visible, etiquetas accesibles y página 404 propia.

## Fase 4: lista para cotizar

- Cada línea se identifica por producto y configuración normalizada.
- Configuraciones idénticas incrementan cantidad; configuraciones diferentes crean líneas independientes.
- Edición, incremento, reducción y eliminación funcionan por línea.
- Las personalizaciones se preservan como líneas separadas al generar el pedido.
- Las imágenes aportadas por clientes se validan por formato real, tamaño y cantidad de píxeles.

## Fase 5: observabilidad, seguridad y SEO

- Telemetría propia sin texto libre ni datos personales, con respeto por `Do Not Track` y límite de frecuencia.
- Registro de vistas, lista, cotización, asistente y fallos técnicos con contexto limitado.
- Encabezados de seguridad, límites de acceso y secreto obligatorio en producción.
- Canonical sin parámetros, `robots.txt`, `sitemap.xml`, datos estructurados existentes y 404 indexable correctamente.
- Compatibilidad del panel de Productos y Videos con Django 6 verificada en listado, alta y edición.

## Validación ejecutada

- Django: `manage.py check`, migraciones y pruebas de `productos`, `carrito`, `cuentas`, `asistente` y `tienda_regalos`.
- Navegador móvil: 320, 375, 390 y 430 px sin desbordamiento horizontal.
- Navegador escritorio: 1440 px sin solapes ni desbordamiento.
- Header móvil medido entre 85 y 95 px, incluyendo búsqueda de 38 a 40 px.
- Confirmación compacta al agregar, actualización de cantidad y apertura explícita del bottom sheet verificadas.
- Cora verificada con voz apagada de inicio, selector disponible y activación manual.
- Cambio de contraseña y activos SVG verificados en móvil.

## Operación

- Variables requeridas y opcionales: `.env.example`.
- Arquitectura: `docs/ARCHITECTURE.md`.
- Checklist y comandos de PythonAnywhere: `docs/PRODUCTION_CHECKLIST.md`.
- CI: `.github/workflows/ci.yml`.

La prueba final en Safari/iOS físico y Firefox debe mantenerse como control manual previo a cada campaña, ya que el entorno automatizado local valida Chromium.
