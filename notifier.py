import os

import requests

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"


def build_map_links(report: dict):
    lat, lon = report.get("lat"), report.get("lon")
    if lat is None or lon is None:
        return None, None

    maps_url = f"https://www.google.com/maps?q={lat},{lon}"
    waze_url = f"https://waze.com/ul?ll={lat},{lon}&navigate=yes"
    return maps_url, waze_url


def send_telegram_message(text: str):
    token = os.environ["TELEGRAM_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]

    response = requests.post(
        TELEGRAM_API.format(token=token),
        data={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
        timeout=15,
    )
    response.raise_for_status()


def format_report_message(report: dict) -> str:
    unidades = ", ".join(report["unidades"]) if report["unidades"] else "Sin unidades asignadas"
    maps_url, waze_url = build_map_links(report)
    if maps_url and waze_url:
        ubicacion_linea = f'📍 <a href="{maps_url}">Abrir en Maps</a> | <a href="{waze_url}">Abrir en Waze</a>'
    else:
        ubicacion_linea = "📍 Solicitar direccion a central (sin coordenadas registradas)"

    return (
        f"🚨 <b>Nueva emergencia</b> (Parte {report['nro_parte']})\n"
        f"<b>Tipo:</b> {report['tipo']}\n"
        f"<b>Direccion:</b> {report['direccion']}\n"
        f"<b>Hora:</b> {report['fecha_hora']}\n"
        f"<b>Estado:</b> {report['estado']}\n"
        f"<b>Unidades:</b> {unidades}\n"
        f"{ubicacion_linea}"
    )
