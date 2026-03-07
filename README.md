## ENSEÑA PERU> PROGRAMA QUE MAESTRO

Por documentar

Modelo principal archivo main.ipynb




hacer group by de umercea por codlocal
obtener solo variables: codlocal,  PDL DIRECTO	PDL INDIRECTO	PDL	QM DIRECTO	QM INDIRECTO	QM	PDLD	MTESANA	ACADEMIA	PFC	EPE. COLUMNA EVALUACION SE DIVIDE EN MATEMATICA Y LECTURA SE DEBE OBTENER UNA COLUMNA DE LECTURA Y SU CONTENIDO DE BE SER PROMEDIO DE NIVEL DE LOGRO.

NIVEL DE LOGOR:

map_logro = {
    'En Inicio': 1,
    'En proceso': 2,
    'Satisfactorio': 3
}

ejemplo

df_urmecea_2_group = (
    df_urmecea_2
    .groupby([
        'Nombre_IE',
        'Cod_Local',
        'AÑO',
        'Área',
        'Evaluación',
        'PERIODO'
    ])
    .agg(
        promedio_logro=('nivel_logro_num', 'mean')
    )
    .reset_index()
)

TODAS LAS TABLAS DEBE ESTAR A NIVEL COD LOCAL, CASO CONTRARIO AGRUPAR
TODO DEBE SER DE LA REGION ANCASH

PARA ELLO UMERCEA DEBE SER LA TABLA BASE PARA EL MERGE QUE TIENE SOLO ANCAHS