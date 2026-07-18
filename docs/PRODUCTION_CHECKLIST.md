# Checklist de producción

## Antes de publicar

1. Configurar `DJANGO_SECRET_KEY`, hosts, orígenes CSRF y correo fuera del repositorio.
2. Ejecutar pruebas, `check` y revisión de migraciones.
3. Ejecutar `collectstatic` y optimización de medios.
4. Confirmar que no se versionan `.env`, bases SQLite, logs ni `media/personalizaciones/`.

## PythonAnywhere

Aplicación: `daxian7.pythonanywhere.com`

- Código: `/home/daxian7/Casita-de-regalo`
- Directorio de trabajo: `/home/daxian7/Casita-de-regalo`
- Virtualenv: `/home/daxian7/.virtualenvs/casita-regalos-venv`
- WSGI: `/var/www/daxian7_pythonanywhere_com_wsgi.py`
- Settings: `tienda_regalos.settings_pythonanywhere`

Actualización desde una consola Bash de PythonAnywhere:

```bash
cd /home/daxian7/Casita-de-regalo
git pull origin main
source /home/daxian7/.virtualenvs/casita-regalos-venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py optimize_media_images --path media --quality 78
python manage.py collectstatic --noinput
python manage.py check --deploy
```

Mapeos estáticos:

- `/static/` -> `/home/daxian7/Casita-de-regalo/staticfiles`
- `/media/` -> `/home/daxian7/Casita-de-regalo/media`

Después, pulsa **Reload** en la pestaña Web. Si algo falla, revisa primero:

- `/var/log/daxian7.pythonanywhere.com.error.log`
- `/var/log/daxian7.pythonanywhere.com.server.log`
- `/var/log/daxian7.pythonanywhere.com.access.log`

## WSGI

El WSGI debe agregar el proyecto al `sys.path`, definir `DJANGO_SETTINGS_MODULE=tienda_regalos.settings_pythonanywhere` y cargar el secreto desde una variable privada de PythonAnywhere. Nunca subas el secreto al repositorio.

Para que los enlaces de recuperación lleguen por correo, agrega también estas variables al WSGI antes de crear la aplicación Django:

```python
os.environ["DJANGO_EMAIL_BACKEND"] = "django.core.mail.backends.smtp.EmailBackend"
os.environ["DJANGO_EMAIL_HOST"] = "smtp.gmail.com"
os.environ["DJANGO_EMAIL_PORT"] = "587"
os.environ["DJANGO_EMAIL_HOST_USER"] = "correo-remitente@gmail.com"
os.environ["DJANGO_EMAIL_HOST_PASSWORD"] = "contrasena-de-aplicacion"
os.environ["DJANGO_EMAIL_USE_TLS"] = "True"
os.environ["DJANGO_DEFAULT_FROM_EMAIL"] = "Casita de Regalos <correo-remitente@gmail.com>"
```

En Gmail, `DJANGO_EMAIL_HOST_PASSWORD` debe ser una contraseña de aplicación, no la contraseña normal. Con otro proveedor, reemplaza host, puerto y TLS por sus datos SMTP. Tras recargar la web, solicita una recuperación con una cuenta de prueba y confirma recepción y apertura del enlace.

## Prueba posterior

1. Inicio y catálogo en 320, 375, 390, 430 y escritorio.
2. Agregar dos configuraciones distintas del mismo producto.
3. Editar y quitar solo una línea.
4. Abrir el drawer y finalizar por WhatsApp.
5. Registro, acceso y recuperación de contraseña.
6. Abrir Cora, activar voz, pausar y cerrar.
7. Confirmar que imágenes y videos no producen 404.
