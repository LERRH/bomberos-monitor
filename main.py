import time

from dotenv import load_dotenv
import os

load_dotenv()

from scraper import fetch_reports, BlockedError
from notifier import send_telegram_message, format_report_message
from state import load_last_seen, save_last_seen

POLL_INTERVAL_SECONDS = int(os.environ.get("POLL_INTERVAL_SECONDS", "90"))
BLOCKED_BACKOFF_SECONDS = int(os.environ.get("BLOCKED_BACKOFF_SECONDS", str(max(POLL_INTERVAL_SECONDS * 10, 300))))


def check_once():
    reports = fetch_reports()
    if not reports:
        print("No se pudieron leer reportes en esta pasada.")
        return

    current_max = max(r["nro_parte"] for r in reports)
    last_seen = load_last_seen()

    if last_seen is None:
        save_last_seen(current_max)
        print(f"Primera ejecucion: se establece el ultimo Nro Parte visto en {current_max}, sin enviar alertas.")
        return

    nuevos = sorted(
        (r for r in reports if r["nro_parte"] > last_seen),
        key=lambda r: r["nro_parte"],
    )

    for report in nuevos:
        send_telegram_message(format_report_message(report))
        print(f"Alerta enviada: Parte {report['nro_parte']} - {report['tipo']}")

    if current_max > last_seen:
        save_last_seen(current_max)

    if not nuevos:
        print("Sin reportes nuevos.")


def main():
    print(f"Iniciando monitoreo cada {POLL_INTERVAL_SECONDS} segundos. Ctrl+C para detener.")
    is_blocked = False
    while True:
        try:
            check_once()
            if is_blocked:
                send_telegram_message("✅ Monitoreo restablecido, el sitio volvio a responder normal.")
                is_blocked = False
            time.sleep(POLL_INTERVAL_SECONDS)
        except BlockedError:
            if not is_blocked:
                print("Bloqueado por captcha/anti-bot. Pausando y avisando.")
                send_telegram_message(
                    f"⚠️ El sitio de bomberos esta pidiendo captcha (posible bloqueo anti-bot). "
                    f"Pausando revisiones por {BLOCKED_BACKOFF_SECONDS // 60} min antes de reintentar."
                )
                is_blocked = True
            else:
                print("Sigue bloqueado, reintentando mas tarde.")
            time.sleep(BLOCKED_BACKOFF_SECONDS)
        except Exception as exc:
            print(f"Error durante la revision: {exc}")
            time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
