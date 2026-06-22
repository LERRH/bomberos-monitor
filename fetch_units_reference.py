import time

from dotenv import load_dotenv

load_dotenv()

import requests
from bs4 import BeautifulSoup
from psycopg2.extras import execute_values

from db import get_connection

URL = "https://www.bomberosperu.gob.pe/sgo/ceem/SGO_CEEM_CDVehiculos.asp"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
}

COMANDANCIAS = {
    "201000": "I Comandancia Departamental - Piura",
    "202000": "II Comandancia Departamental Lambayeque",
    "203000": "III Comandancia Departamental La Libertad",
    "204000": "IV Comandancia Departamental Lima",
    "205000": "V Comandancia Departamental Callao",
    "206000": "VI Comandancia Departamental Ica",
    "207000": "VII Comandancia Departamental Arequipa",
    "208000": "VIII Comandancia Departamental Tacna",
    "209000": "IX Comandancia Departamental Cusco",
    "210000": "X Comandancia Departamental Junin Centro",
    "211000": "XI Comandancia Departamental Loreto",
    "212000": "XII Comandancia Departamental Ucayali",
    "213000": "XIII Comandancia Departamental Ancash",
    "214000": "XIV Comandancia Departamental Huanuco",
    "215000": "XV Comandancia Departamental Junin Oriente",
    "216000": "XVI Comandancia Departamental Madre de Dios",
    "217000": "XVII Comandancia Departamental San Martin",
    "218000": "XVIII Comandancia Departamental Tumbes",
    "219000": "XIX Comandancia Departamental Apurimac",
    "220000": "XX Comandancia Departamental Puno",
    "221000": "XXI Comandancia Departamental Moquegua",
    "222000": "XXII Comandancia Departamental Amazonas",
    "223000": "XXIII Comandancia Departamental Cajamarca",
    "224000": "XXIV Comandancia Departamental Lima Sur",
    "225000": "XXV Comandancia Departamental Lima Norte",
    "226000": "XXVI Comandancia Departamental Ayacucho",
    "227000": "XXVII Comandancia Departamental Huancavelica",
    "228000": "XXVIII Comandancia Departamental Lima Este",
}


def fetch_comandancia(session, codigo):
    response = session.post(URL, data={"cboCD": codigo}, timeout=20)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    rows = []
    for tr in soup.select("tr.fuente1"):
        tds = tr.find_all("td")
        if not tds:
            continue
        cia = tds[0].get_text(strip=True)
        unidades = [td.get_text(strip=True) for td in tds if td.has_attr("bgcolor") and td.get_text(strip=True)]
        if cia and unidades:
            rows.append((cia, unidades))
    return rows


def main():
    session = requests.Session()
    session.headers.update(HEADERS)

    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("delete from unit_reference")
    conn.close()

    total = 0
    for codigo, nombre in COMANDANCIAS.items():
        rows = fetch_comandancia(session, codigo)

        values = [
            (codigo, nombre, cia, unidad)
            for cia, unidades in rows
            for unidad in unidades
        ]

        if values:
            conn = get_connection()
            conn.autocommit = True
            cur = conn.cursor()
            execute_values(
                cur,
                "insert into unit_reference (comandancia_code, comandancia_name, cia_code, unit_code) values %s",
                values,
            )
            conn.close()
            total += len(values)

        print(f"{codigo} {nombre}: {len(rows)} companias, {len(values)} unidades", flush=True)
        time.sleep(0.5)

    print(f"Total unidades cargadas: {total}", flush=True)


if __name__ == "__main__":
    main()
