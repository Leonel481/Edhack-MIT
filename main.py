import pandas as pd
import numpy as np
from rsc.model import escalar, elbow_plot, aplicar_kmeans, pca_plot, entrenar_regresion, construir_preprocessor
from rsc.utils import *


def main():

    # URLs de datasets públicos
    URL_AULAS = "https://escale.minedu.gob.pe/documents/10156/f5035329-93b9-4fd9-bb4c-1e83dcfa91da"
    URL_EDIFICIOS = "https://escale.minedu.gob.pe/documents/10156/e36efe68-64b2-4302-b715-0c4b6037d67b"
    URL_PADRON = "https://escale.minedu.gob.pe/documents/10156/aec96875-bdd2-4d3b-a43a-fb7b89d7738c"

    # Archivo local URMECEA
    PATH_URMECEA = "data/URMECEA.xlsx"
    PATH_DISTANCIAS = "notebooks/Distancia_institucion_highway.csv"

    print("Descargando datasets...")

    df_aulas = cargar_url_en_df(URL_AULAS, "AULAS")
    df_edif = cargar_url_en_df(URL_EDIFICIOS, "EDIFICIOS")
    df_padron = cargar_url_en_df(URL_PADRON, "PADRON")

    print("Transformando datasets...")

    df_final = transformar_urmecea(
        df_edif=df_edif,
        df_aula=df_aulas,
        df_padron=df_padron,
        path_urmecea=PATH_URMECEA,
        path_distancia=PATH_DISTANCIAS
    )

    print("Dataset final generado:")
    print(df_final.shape)
    print(df_final.head())

    # Guardar dataset final
    df_final.to_csv("data/dataset_final.csv", index=False)

    # =========================
    #  Preparación de datos
    # =========================
    df_modelo = df_final.copy()

    # columnas que no se usan
    cols_drop = ['COD_MOD', 'D_FORMA', 'D_DPTO']
    df_modelo = df_modelo.drop(columns=cols_drop, errors="ignore")

    # =========================
    #  Clustering
    # =========================
    df_cluster = df_modelo.copy()
    df_cluster['ratio_alumno_docente'] = df_cluster['TALUM'] / df_cluster['TDOC']

    # Crear índice de infraestructura (ejemplo)
    infra_cols = ['P53_13_1', 'P53_13_2', 'P53_13_3','P531011','P531012','P53_3', 'P53_4','P53_9']

    df_cluster['infra_index'] = df_cluster[infra_cols].sum(axis=1)

    # Variables finales para clustering
    cluster_vars = [
        'ratio_alumno_docente',
        'TALUM',
        'infra_index',
        'dist_km_utm_log+1',
        'n_aulas',
        'max_piso'
    ]

    X_scaled, df_clean = escalar(df_cluster, cluster_vars)
    elbow_plot(X_scaled, k_max=10)
    k = 4   # ejemplo (elige según elbow)
    df_clustered, modelo_kmeans = aplicar_kmeans(X_scaled, df_clean, k)
    pca_plot(X_scaled, df_clustered["cluster"])

    df_clustered.to_csv("data/escuelas_clusterizadas.csv", index=False)

    print("Clusters generados")
    print(df_clustered["cluster"].value_counts())

    df_modelo = df_modelo.merge(
                    df_clustered[["cluster"]],
                    left_index=True,
                    right_index=True,
                    how="left"
                )
    # =========================
    #  Modelo
    # =========================

    df_modelo["cluster"] = df_modelo["cluster"].astype("category")
    df_modelo["target"] = df_modelo[
                                    ["Evaluación_lectura", "Evaluación_matematica"]
                                ].mean(axis=1)
    df_modelo = df_modelo.dropna(subset=["target"])
    cols_drop = [
    "Evaluación_lectura",
    "Evaluación_matematica"
    ]
    df_modelo = df_modelo.drop(columns=cols_drop, errors="ignore")
    print("Filas antes:", len(df_modelo))
    df_modelo = df_modelo.dropna(subset=["target"])
    print("Filas después:", len(df_modelo))
    # ejemplo target
    target = "target"

    X = df_modelo.drop(columns=[target])
    y = df_modelo[target]

    num_cols = X.select_dtypes(include=["int64", "float64"]).columns.tolist()
    cat_cols = X.select_dtypes(include=["object", "category", "string"]).columns.tolist()
    
    # entrenar modelo
    modelo, metricas = entrenar_regresion(
        df_modelo,
        target,
        num_cols,
        cat_cols
    )


    print("Modelo entrenado")
    print(metricas)

if __name__ == "__main__":
    main()