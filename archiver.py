from dotenv import load_dotenv

load_dotenv()

from scraper import fetch_reports, BlockedError
from db import get_connection, fetch_existing, insert_report, update_report, touch_report


def _changed(existing, report):
    estado, unidades, direccion, lat, lon, tipo = existing
    return (
        estado != report["estado"]
        or sorted(unidades) != sorted(report["unidades"])
        or direccion != report["direccion"]
        or lat != report["lat"]
        or lon != report["lon"]
        or tipo != report["tipo"]
    )


def run_once():
    reports = fetch_reports()
    if not reports:
        print("No se obtuvieron reportes.")
        return

    conn = get_connection()
    try:
        cur = conn.cursor()
        inserted = updated = unchanged = 0

        for report in reports:
            existing = fetch_existing(cur, report["nro_parte"])
            if existing is None:
                insert_report(cur, report)
                inserted += 1
            elif _changed(existing, report):
                update_report(cur, report)
                updated += 1
            else:
                touch_report(cur, report["nro_parte"])
                unchanged += 1

        conn.commit()
        print(f"Nuevos: {inserted}, actualizados: {updated}, sin cambios: {unchanged}")
    finally:
        conn.close()


if __name__ == "__main__":
    try:
        run_once()
    except BlockedError as exc:
        print(f"Bloqueado por captcha/anti-bot, se omite esta corrida: {exc}")
