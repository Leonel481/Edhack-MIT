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


def preparar_padron(df_padron: pd.DataFrame) -> pd.DataFrame:
    """
    Selecciona columnas relevantes del padrón y elimina duplicados por CODLOCAL.
    """
    cols_padron = ['COD_MOD', 'CODLOCAL', 'D_FORMA', 'DAREACENSO', 'TALUM', 'TDOC', 'D_DPTO']

    df = (
        df_padron[cols_padron]
        .drop_duplicates(subset=['CODLOCAL'], keep='first')
        .copy()
    )

    return df


def transformar_aulas(df_aula: pd.DataFrame) -> pd.DataFrame:
    """
    Genera métricas agregadas a nivel de CODLOCAL para aulas:
    - número de aulas
    - piso máximo
    - aulas usadas
    - tipo de aula
    """

    cols_aula = ['CODLOCAL', 'P61_2', 'P61_3', 'P61_4']
    df = df_aula[cols_aula].copy()

    # Número de aulas por local
    n_aulas = (
        df.groupby('CODLOCAL')
        .size()
        .rename('n_aulas')
        .reset_index()
    )

    # Piso máximo por local
    max_piso = (
        df.groupby('CODLOCAL')['P61_2']
        .max()
        .rename('max_piso')
        .reset_index()
    )

    # Conversión binaria (1 si es '1')
    df['P61_3'] = (df['P61_3'] == '1').astype(int)

    aulas_usadas = (
        df.groupby('CODLOCAL')['P61_3']
        .sum()
        .reset_index()
    )

    # Pivot de tipo de aula
    tipo_aula = (
        df.groupby(['CODLOCAL', 'P61_4'])
        .size()
        .unstack(fill_value=0)
        .add_prefix('P61_4')
        .reset_index()
    )

    # Selección segura de columnas
    cols = ['CODLOCAL', 'P61_401', 'P61_402']
    tipo_aula = tipo_aula.reindex(columns=cols, fill_value=0)

    # Merge final
    df_result = (
        n_aulas
        .merge(max_piso, on='CODLOCAL', how='left')
        .merge(aulas_usadas, on='CODLOCAL', how='left')
        .merge(tipo_aula, on='CODLOCAL', how='left')
    )

    return df_result


def transformar_edificios(df_edif: pd.DataFrame) -> pd.DataFrame:
    """
    Genera métricas agregadas a nivel de CODLOCAL para edificios.
    """

    cols_edif = [
        'CODLOCAL', 'P53_3', 'P53_4', 'P53_9',
        'P53_10', 'P53_13_1', 'P53_13_2', 'P53_13_3'
    ]

    binary_cols = ['P53_3', 'P53_4', 'P53_9', 'P53_13_1', 'P53_13_2', 'P53_13_3']

    df = df_edif[cols_edif].copy()

    # Número de edificios por local
    n_edificios = (
        df.groupby('CODLOCAL')
        .size()
        .rename('n_edificios')
        .reset_index()
    )

    # Conversión binaria
    df[binary_cols] = (df[binary_cols] == '1').astype(int)

    binarios = (
        df.groupby('CODLOCAL')[binary_cols]
        .sum()
        .reset_index()
    )

    # Pivot de estado de edificio
    estado = (
        df.groupby(['CODLOCAL', 'P53_10'])
        .size()
        .unstack(fill_value=0)
        .add_prefix('P5310')
        .reset_index()
    )

    df_result = (
        n_edificios
        .merge(binarios, on='CODLOCAL', how='left')
        .merge(estado, on='CODLOCAL', how='left')
    )

    return df_result


def procesar_urmecea(path_excel: str) -> pd.DataFrame:
    """
    Procesa el archivo histórico URMECEA:
    - normaliza codigos
    - convierte nivel de logro a numérico
    - genera variables binarias
    - calcula promedio de evaluación
    """

    df = pd.read_excel(path_excel)

    cols = [
        'Cod_Local', 'PDL', 'QM DIRECTO', 'QM INDIRECTO',
        'QM', 'PDLD', 'MTESANA', 'ACADEMIA',
        'Evaluación', 'Nivel de logro'
    ]

    df = df[cols].copy()

    # Normalizar código local
    df['Cod_Local'] = (
        df['Cod_Local']
        .astype('Int64')
        .astype(str)
        .str.zfill(6)
    )

    # Mapear nivel de logro
    map_logro = {
        'en inicio': 1,
        'en proceso': 2,
        'satisfactorio': 3
    }

    df['nivel_logro_num'] = (
        df['Nivel de logro']
        .str.lower()
        .map(map_logro)
        .astype('Int64')
    )

    df['Evaluación'] = df['Evaluación'].str.lower()

    # Promedio por evaluación
    evaluacion = (
        df.groupby(['Cod_Local', 'Evaluación'])
        .agg({'nivel_logro_num': 'mean'})
        .unstack(fill_value=0)
        .add_prefix('Evaluación')
        .reset_index()
    )

    evaluacion.columns = [
        'Cod_Local',
        'Evaluación_lectura',
        'Evaluación_matematica'
    ]

    # Variables binarias
    cols_binarias = [
        'PDL', 'QM DIRECTO', 'QM INDIRECTO',
        'QM', 'PDLD', 'MTESANA', 'ACADEMIA'
    ]

    df[cols_binarias] = df[cols_binarias].notna().astype(int)

    df_bin = (
        df[['Cod_Local'] + cols_binarias]
        .rename(columns={
            'MTESANA': 'MTESANA_INDIRECTO',
            'ACADEMIA': 'ACADEMIA_DIRECTO'
        })
        .drop_duplicates(subset=['Cod_Local'])
    )

    df_result = (
        df_bin
        .merge(evaluacion, on='Cod_Local', how='left')
        .rename(columns={'Cod_Local': 'CODLOCAL'})
    )

    return df_result

def procesar_distancias(path_excel: str) -> pd.DataFrame:
    """
    Procesa el archivo histórico URMECEA:
    - normaliza codigos
    - convierte nivel de logro a numérico
    - genera variables binarias
    - calcula promedio de evaluación
    """

    df = pd.read_csv(path_excel)

    # Normalizar código local
    df['CODLOCAL'] = (
        df['CODLOCAL']
        .astype('Int64')
        .astype(str)
        .str.zfill(6)
    )

    return df

def transformar_urmecea(
    df_edif: pd.DataFrame,
    df_aula: pd.DataFrame,
    df_padron: pd.DataFrame,
    path_distancia: str,
    path_urmecea: str
) -> pd.DataFrame:
    """
    Función principal que integra todas las transformaciones.
    """

    df_padron_clean = preparar_padron(df_padron)
    df_aulas = transformar_aulas(df_aula)
    df_edificios = transformar_edificios(df_edif)
    
    
    # Integración de datasets
    df_infraestructura = (
        df_edificios
        .merge(df_aulas, on='CODLOCAL', how='left')
    )

    df_base = (
        df_padron_clean
        .merge(df_infraestructura, on='CODLOCAL', how='left')
    )

    # Procesar URMECEA y DISTANCIAS
    df_urmecea = procesar_urmecea(path_urmecea)
    df_distancias = procesar_distancias(path_distancia)

    # Merge final
    df_final = (
        df_urmecea
        .merge(df_base, on='CODLOCAL', how='left')
    )

    df_modelo = (
        df_final
        .merge(df_distancias, on='CODLOCAL', how='left')
    )

    return df_modelo