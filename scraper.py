import datetime
import re

import requests
from bs4 import BeautifulSoup

URL = "https://sgonorte.bomberosperu.gob.pe/24horas"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-PE,es;q=0.9,en;q=0.8",
}
COORD_RE = re.compile(r"\(\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\)")
FECHA_RE = re.compile(r"(\d{2})/(\d{2})/(\d{4})\s+(\d{2}):(\d{2}):(\d{2})\s*([ap])\.?\s*m\.?", re.IGNORECASE)

_session = requests.Session()
_session.headers.update(HEADERS)


class BlockedError(Exception):
    pass


def _parse_direccion(direccion_raw):
    match = COORD_RE.search(direccion_raw)
    lat = lon = None
    if match:
        lat_val, lon_val = float(match.group(1)), float(match.group(2))
        if lat_val != 0 or lon_val != 0:
            lat, lon = lat_val, lon_val
        direccion_raw = COORD_RE.sub("", direccion_raw)

    direccion = re.sub(r"\s{2,}", " ", direccion_raw).strip()
    return direccion, lat, lon


def _parse_fecha_hora(fecha_hora_raw):
    match = FECHA_RE.search(fecha_hora_raw)
    if not match:
        return None

    day, month, year, hour, minute, second, period = match.groups()
    hour = int(hour)
    if period.lower() == "p" and hour != 12:
        hour += 12
    elif period.lower() == "a" and hour == 12:
        hour = 0

    return datetime.datetime(int(year), int(month), int(day), hour, int(minute), int(second))


def fetch_reports():
    response = _session.get(URL, timeout=20)
    response.raise_for_status()

    if "Home/Forbidden" in response.url or "no eres humano" in response.text:
        raise BlockedError("El sitio esta solicitando captcha (posible bloqueo anti-bot).")

    soup = BeautifulSoup(response.text, "html.parser")

    rows = soup.select("table tbody tr")
    reports = []
    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 6:
            continue

        nro_parte = cells[0].get_text(strip=True)
        fecha_hora = cells[1].get_text(strip=True)
        fecha_hora_dt = _parse_fecha_hora(fecha_hora)
        direccion, lat, lon = _parse_direccion(cells[2].get_text(strip=True))
        tipo = cells[3].get_text(strip=True)
        estado = cells[4].get_text(strip=True)
        unidades = [li.get_text(strip=True) for li in cells[5].select("li")]

        if not nro_parte.isdigit():
            continue

        reports.append({
            "nro_parte": int(nro_parte),
            "fecha_hora": fecha_hora,
            "fecha_hora_dt": fecha_hora_dt,
            "direccion": direccion,
            "lat": lat,
            "lon": lon,
            "tipo": tipo,
            "estado": estado,
            "unidades": unidades,
        })

    return reports
