# Audita · Auditorías preliminares de privacidad

Proyecto Django con usuarios, administrador, inspección pasiva de sitios y PDF. Marco de referencia: Ley chilena N° 21.719, publicada el 13 de diciembre de 2024 y vigente desde el 1 de diciembre de 2026. No constituye certificación jurídica ni garantiza por sí solo el cumplimiento del sitio auditado o de esta plataforma.

## Tecnología

Python 3.11 o 3.12 y Django 5.2 LTS. Se reemplazó Django 3.2 porque está fuera de soporte y no admite oficialmente Python 3.11. Usa una versión de mantenimiento actual de Python 3.11 en lugar de 3.11.0. SQLite incluido; MySQL opcional. SQLyog es un cliente para administrar MySQL, no una base de datos.

## Instalación local (Windows PowerShell)

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:DEBUG="1"
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Abre http://127.0.0.1:8000. El administrador entra a /admin/ y crea las cuentas de usuario desde Usuarios. Las cuentas normales deben estar activas y tener contraseña, sin marcar «staff» ni «superusuario». Las cuentas staff acceden a todas las auditorías; los permisos de modelos del panel administrativo se asignan por separado.

En Linux/macOS:

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
export DEBUG=1
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

No hay cuentas ni contraseñas de demostración incluidas.

## Uso

1. Inicia sesión y elige Nueva auditoría.
2. Introduce una URL pública sin datos personales y confirma que tienes autorización para revisarla.
3. Revisa observaciones y límites del análisis automático.
4. Completa nueve criterios manuales, documentando evidencia y aplicabilidad. Guarda antes de descargar.
5. Descarga PDF o confirma un destinatario y solicita envío por correo.
6. Puedes eliminar la auditoría con sus revisiones. Permanece un evento mínimo de eliminación sin URL ni evidencia.

El administrador gestiona cuentas y puede consultar auditorías, revisiones y eventos. No se permite autorregistro. No se envió ningún mensaje real durante la construcción.

## Correo SMTP

Por defecto los mensajes se escriben en consola: **no se envían a Internet**. Configura variables de entorno del servidor:

```
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.tu-proveedor.cl
EMAIL_PORT=587
EMAIL_USE_TLS=1
EMAIL_HOST_USER=usuario
EMAIL_HOST_PASSWORD=secreto
DEFAULT_FROM_EMAIL=informes@tu-dominio.cl
```

No guardes secretos en Git. Se exige confirmación explícita por envío y se limita a una solicitud por minuto y usuario en el proceso. El PDF puede contener información confidencial: define procedimientos reales para autorizar destinatarios. La aplicación registra el evento sin conservar el correo del destinatario.

## MySQL / SQLyog

Instala MySQL 8, crea una base utf8mb4 y un usuario con permisos limitados. Instala `mysqlclient>=2.2.1`. Define `DB_ENGINE=mysql`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST` y opcionalmente `DB_PORT`. Ejecuta `python manage.py migrate`. SQLyog puede conectarse a esa instancia para su administración. Esta variante no fue probada en este entorno.

## Verificación

```sh
DEBUG=1 python manage.py check
DEBUG=1 python manage.py test
```

Pruebas de aislamiento de usuarios, acceso administrativo, CSRF, bloqueo de destinos internos, flujo de auditoría, revisión manual, PDF y adjunto de correo. El análisis remoto se simula en pruebas; no se ha auditado un sitio real ni probado SMTP real. Verificado en Python 3.12; compatible por dependencias con 3.11, pero requiere validación en el servidor definitivo. No se realizó una prueba visual de navegador.

## Alcance de la auditoría

Se inspecciona solamente el HTML inicial de una URL, enlaces por su texto, formularios, scripts externos y cookies recibidas por HTTP. Máximo 1 MB, tres redirecciones y tiempo acotado. Sin JavaScript, rastreo completo, acceso autenticado o pruebas de intrusión. No se guarda el HTML, valores de cookies ni contenido de formularios.

Las observaciones son señales técnicas, no fallos legales automáticos. Una cookie, un script externo o la falta de un enlace detectado no prueban infracción. Los criterios manuales son una guía general y deben ajustarse a cada organización y caso con asesoría jurídica. No hay porcentaje de cumplimiento ni un sello «cumple».

Fuentes para revisión jurídica: texto oficial en la Biblioteca del Congreso Nacional (https://www.bcn.cl/leychile/; buscar Ley 21719), Diario Oficial y normativa e instrucciones aplicables de la autoridad. Deben revisarse actualizaciones, reglamentos, tratamientos especiales y obligaciones específicas antes de usar la herramienta profesionalmente.

## Antes de producción

Esta es una primera versión funcional; no está desplegada ni preparada para abrirse al público sin la configuración siguiente:

- Completar la página de privacidad con responsable, contacto, bases jurídicas, finalidades, destinatarios, transferencias, conservación y canal de derechos. Implementar el procedimiento operativo para atender solicitudes y sus plazos. La página incluida identifica claramente los datos que faltan.
- Establecer políticas y procedimientos efectivos: contratos con encargados, gestión de incidentes, borrado en backups, evaluaciones de impacto cuando correspondan y revisión jurídica. El software no acredita estas medidas.
- Definir `DEBUG=0`, una `SECRET_KEY` aleatoria y `ALLOWED_HOSTS`. Configurar HTTPS, servidor WSGI, archivos estáticos, copias cifradas, recuperación y control de acceso. Ejecutar `manage.py check --deploy` con la configuración definitiva. `runserver` es solo para desarrollo.
- **Aislar el analizador con una política de salida de red que bloquee redes privadas, loopback, link-local, direcciones reservadas y endpoints de metadatos en IPv4/IPv6**, también tras resolver DNS. La validación de aplicación comprueba destinos y redirecciones, pero no evita por sí sola DNS rebinding ni cambios de resolución entre comprobación y conexión. No exponer el escáner a usuarios no confiables antes de implementar este aislamiento. En producción se deshabilita por defecto: define `SCANNER_ENABLED=1` únicamente después de configurar ese aislamiento.
- El escaneo es síncrono para uso de bajo volumen. Para producción, moverlo a una cola con trabajadores aislados, límites por organización y cortes de tiempo a nivel de infraestructura. Usar caché compartida (por ejemplo Redis) para límites entre procesos; la caché local actual no es un control global.
- Incorporar limitación de intentos de login en el proxy o un componente probado, y MFA para administradores. No hay recuperación pública de contraseña configurada; el administrador restablece las cuentas.
- Desactivar caché de páginas privadas en proxy y configurar manejo de logs sin datos sensibles. Revisar permisos del administrador, política de sesión y retención de eventos. La administración Django permite editar registros: no es una bitácora inmutable.

## Estructura

`config/`: configuración; `audits/`: modelos, permisos, escáner, PDF, correo y pruebas; `templates/`: interfaz responsive; `audits/migrations/`: esquema versionado. No se incluyen base de datos, secretos, correos ni datos reales.
