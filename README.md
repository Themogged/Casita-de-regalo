# Casita de Regalos

Tienda Django para catálogo, regalos personalizados, lista para cotizar, pedidos por WhatsApp y asistencia con Cora.

## Requisitos

- Python 3.13
- SQLite para desarrollo
- Las dependencias de `requirements.txt`

## Puesta en marcha local

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py runserver
```

Django no carga `.env` automáticamente. Define las variables en la consola, en tu IDE o mediante el gestor de secretos del entorno. No guardes claves reales en Git.

## Validación

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test productos carrito cuentas asistente tienda_regalos
python manage.py collectstatic --noinput
git diff --check
```

## Imágenes y videos

El catálogo sirve WebP cuando existe y admite `srcset` con variantes de 360, 720 y 1080 px. Para generarlas:

```powershell
python manage.py optimize_media_images --path media --quality 78
```

Los videos secundarios se cargan al entrar en pantalla, respetan ahorro de datos y movimiento reducido, mantienen un solo video activo y ofrecen controles propios de pausa y audio.

## Lista configurable

Cada línea se identifica por producto más texto, color, variante, fecha, mensaje, opciones e imagen. Una configuración idéntica aumenta cantidad; una distinta crea una línea independiente. Las líneas pueden editarse, incrementarse o retirarse por separado.

## Cora

La voz usa `SpeechSynthesis` del navegador, viene desactivada y conserva únicamente la preferencia local del dispositivo. Se puede elegir voz en español, pausar, continuar o silenciar. Si el navegador no ofrece síntesis, el chat sigue funcionando normalmente.

## Seguridad y observabilidad

- CSRF, cookies seguras, HSTS y cabeceras defensivas en producción.
- Límites de intentos para acceso administrativo y de clientes.
- Honeypot de registro y validación real de imágenes/videos.
- Eventos operativos con lista blanca y sin texto, correo, dedicatorias ni parámetros de URL.
- Los eventos se escriben como JSON en `storefront.events` y aparecen en el log del servidor.

Consulta [docs/PRODUCTION_CHECKLIST.md](docs/PRODUCTION_CHECKLIST.md) para publicar, [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) para el diseño técnico y [docs/IMPLEMENTATION_REPORT.md](docs/IMPLEMENTATION_REPORT.md) para el alcance validado.
