"""Inspección pasiva de una única página HTML; no ejecuta JavaScript."""

import ipaddress, socket, time
from urllib.parse import urlsplit, urljoin
import requests
from bs4 import BeautifulSoup

CRITERIA = {
    "information": "Información al titular: responsable, finalidades, destinatarios y conservación",
    "lawful_basis": "Base jurídica por finalidad y prueba del consentimiento cuando corresponde",
    "rights": "Procedimiento para acceso, rectificación, supresión, oposición y portabilidad",
    "minimization": "Minimización, exactitud y plazos de eliminación",
    "cookies": "Cookies y rastreadores: inventario, finalidad y base jurídica",
    "processors": "Encargados, contratos y transferencias internacionales",
    "security": "Seguridad, control de accesos y gestión de incidentes",
    "special": "Datos sensibles, menores y evaluaciones de impacto cuando corresponda",
    "accountability": "Responsabilidades internas y evidencia de cumplimiento",
}


def validate_url(url):
    try:
        parts = urlsplit(url)
        if (
            parts.scheme not in ("http", "https")
            or not parts.hostname
            or parts.username
            or parts.password
            or parts.port not in (None, 80, 443)
        ):
            raise ValueError(
                "Usa una URL pública HTTP/HTTPS sin credenciales y con puerto estándar."
            )
        addresses = socket.getaddrinfo(
            parts.hostname,
            parts.port or (443 if parts.scheme == "https" else 80),
            type=socket.SOCK_STREAM,
        )
        if not addresses or any(
            not ipaddress.ip_address(a[4][0]).is_global for a in addresses
        ):
            raise ValueError(
                "No se permiten direcciones internas, locales o reservadas."
            )
    except (OSError, ValueError) as exc:
        raise ValueError("Destino inválido o no público.") from exc
    return url


def scan(url):
    start = time.monotonic()
    session = requests.Session()
    try:
        for _ in range(4):
            validate_url(url)
            if time.monotonic() - start > 25:
                raise ValueError("Se excedió el tiempo de auditoría.")
            with session.get(
                url,
                timeout=(4, 6),
                allow_redirects=False,
                stream=True,
                headers={"User-Agent": "Audita/1.0 (revision pasiva de privacidad)"},
            ) as response:
                if response.status_code in (301, 302, 303, 307, 308):
                    location = response.headers.get("Location")
                    if not location:
                        raise ValueError("Redirección sin destino.")
                    url = urljoin(url, location)
                    continue
                response.raise_for_status()
                if "text/html" not in response.headers.get("Content-Type", "").lower():
                    raise ValueError("El destino no entrega HTML.")
                body = bytearray()
                for chunk in response.iter_content(32768):
                    body.extend(chunk)
                    if len(body) > 1_000_000:
                        raise ValueError("Página demasiado grande (máximo 1 MB).")
                    if time.monotonic() - start > 25:
                        raise ValueError("Se excedió el tiempo de auditoría.")
                soup = BeautifulSoup(bytes(body), "html.parser")
                links = [
                    a
                    for a in soup.find_all("a", href=True)
                    if any(
                        w in a.get_text(" ", strip=True).lower()
                        for w in ("privacidad", "privacy", "datos personales")
                    )
                ]
                policies = [urljoin(url, a["href"]) for a in links][:5]
                forms = soup.find_all("form")
                return [
                    {
                        "title": "HTTPS en la página final",
                        "status": (
                            "observed"
                            if urlsplit(url).scheme == "https"
                            else "attention"
                        ),
                        "evidence": url,
                        "limit": "HTTPS no demuestra la seguridad del sistema completo.",
                    },
                    {
                        "title": "Enlace visible a privacidad",
                        "status": "observed" if policies else "review",
                        "evidence": (
                            " | ".join(policies)
                            if policies
                            else "No se identificó un enlace por su texto en el HTML."
                        ),
                        "limit": "No se ha verificado el contenido ni la suficiencia jurídica de la política.",
                    },
                    {
                        "title": "Formularios detectados",
                        "status": "review",
                        "evidence": f"{len(forms)} formulario(s) en el HTML inicial.",
                        "limit": "Revisar campos, finalidades, base jurídica y textos de información.",
                    },
                    {
                        "title": "Scripts externos",
                        "status": "review",
                        "evidence": f"{sum(bool(s.get('src')) and urlsplit(urljoin(url,s['src'])).netloc != urlsplit(url).netloc for s in soup.find_all('script'))} script(s) externos declarados.",
                        "limit": "No identifica todos los rastreadores ni analiza cookies creadas con JavaScript.",
                    },
                    {
                        "title": "Cookies recibidas por HTTP",
                        "status": "review",
                        "evidence": f"{len(response.cookies)} cookie(s) recibidas; sus valores no se guardan.",
                        "limit": "Una cookie no implica infracción; clasificar su finalidad y base jurídica.",
                    },
                ]
        raise ValueError("Demasiadas redirecciones.")
    finally:
        session.close()
