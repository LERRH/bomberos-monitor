import os

import psycopg2


def get_connection():
    return psycopg2.connect(os.environ["DATABASE_URL"])


def fetch_existing(cur, nro_parte):
    cur.execute(
        "select estado, unidades, direccion, lat, lon, tipo from reports where nro_parte = %s",
        (nro_parte,),
    )
    return cur.fetchone()


def insert_report(cur, report):
    cur.execute(
        """
        insert into reports (nro_parte, fecha_hora, direccion, lat, lon, tipo, estado, unidades)
        values (%(nro_parte)s, %(fecha_hora_dt)s, %(direccion)s, %(lat)s, %(lon)s, %(tipo)s, %(estado)s, %(unidades)s)
        """,
        report,
    )
    _insert_history(cur, report)


def update_report(cur, report):
    cur.execute(
        """
        update reports
        set direccion = %(direccion)s,
            lat = %(lat)s,
            lon = %(lon)s,
            tipo = %(tipo)s,
            estado = %(estado)s,
            unidades = %(unidades)s,
            last_seen_at = now(),
            last_changed_at = now()
        where nro_parte = %(nro_parte)s
        """,
        report,
    )
    _insert_history(cur, report)


def touch_report(cur, nro_parte):
    cur.execute("update reports set last_seen_at = now() where nro_parte = %s", (nro_parte,))


def _insert_history(cur, report):
    cur.execute(
        """
        insert into report_history (nro_parte, estado, unidades, direccion, lat, lon, tipo)
        values (%(nro_parte)s, %(estado)s, %(unidades)s, %(direccion)s, %(lat)s, %(lon)s, %(tipo)s)
        """,
        report,
    )
