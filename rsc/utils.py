import requests
import io
import zipfile
import tempfile
import os
import pandas as pd
from dbfread import DBF

def cargar_url_en_df(url: str, nombre: str) -> pd.DataFrame:
    """
    Descarga un archivo desde una URL directamente en memoria
    y lo retorna como DataFrame.
    Soporta: zip + (dbf, xlsx, xls, csv)
    """
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers, allow_redirects=True, timeout=60)
    response.raise_for_status()
    print(f"[{nombre}] Descargado: {len(response.content)/1024/1024:.2f} MB | Content-Type: {response.headers.get('Content-Type','?')}")

    content = response.content
    buf = io.BytesIO(content)

    # --- ZIP (puede contener DBF, xlsx u otros) ---
    if zipfile.is_zipfile(io.BytesIO(content)):
        with zipfile.ZipFile(buf) as z:
            nombres = z.namelist()
            print(f"[{nombre}] Archivos en ZIP: {nombres}")

            # Buscar DBF dentro del ZIP
            dbf_files = [n for n in nombres if n.lower().endswith(".dbf")]
            xlsx_files = [n for n in nombres if n.lower().endswith(".xlsx")]
            xls_files  = [n for n in nombres if n.lower().endswith(".xls")]
            csv_files  = [n for n in nombres if n.lower().endswith(".csv")]

            if dbf_files:
                dbf_bytes = z.read(dbf_files[0])
                with tempfile.NamedTemporaryFile(suffix=".dbf", delete=False) as tmp:
                    tmp.write(dbf_bytes)
                    tmp_path = tmp.name
                try:
                    tabla = DBF(tmp_path, encoding="latin-1", ignore_missing_memofile=True)
                    df = pd.DataFrame(iter(tabla))
                finally:
                    os.unlink(tmp_path)

            elif xlsx_files:
                df = pd.read_excel(io.BytesIO(z.read(xlsx_files[0])), engine="openpyxl")
            elif xls_files:
                df = pd.read_excel(io.BytesIO(z.read(xls_files[0])), engine="xlrd")
            elif csv_files:
                raw = z.read(csv_files[0])
                try:
                    df = pd.read_csv(io.BytesIO(raw), encoding="utf-8")
                except UnicodeDecodeError:
                    df = pd.read_csv(io.BytesIO(raw), encoding="latin-1")
            else:
                raise ValueError(f"[{nombre}] ZIP no contiene DBF, xlsx, xls ni csv. Archivos: {nombres}")

    # --- Excel directo ---
    elif content[0:8] == b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1":
        df = pd.read_excel(buf, engine="xlrd")

    # --- CSV directo ---
    else:
        try:
            df = pd.read_csv(buf, encoding="utf-8", sep=None, engine="python")
        except UnicodeDecodeError:
            df = pd.read_csv(io.BytesIO(content), encoding="latin-1", sep=None, engine="python")

    print(f"[{nombre}] shape: {df.shape}")
    return df