from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.impute import SimpleImputer
from sklearn.metrics import r2_score, mean_absolute_error
import pandas as pd


def escalar(df: pd.DataFrame, vars_cluster: list) -> tuple[np.ndarray, pd.DataFrame]:
    """Escala las variables y elimina NaN. Retorna (X_scaled, df_limpio)."""
    X = df[vars_cluster].dropna()
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    return X_scaled, X


def elbow_plot(X_scaled: np.ndarray, k_max: int = 10) -> None:
    """Gráfica del método Elbow para elegir k."""
    inertias = []
    K_range = range(2, k_max + 1)
    for k in K_range:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        km.fit(X_scaled)
        inertias.append(km.inertia_)

    plt.figure()
    plt.plot(K_range, inertias, marker="o")
    plt.xlabel("Número de clusters")
    plt.ylabel("Inercia")
    plt.title("Método Elbow")
    plt.tight_layout()
    plt.show()


def aplicar_kmeans(X_scaled: np.ndarray, df_base: pd.DataFrame, k: int) -> pd.DataFrame:
    """Aplica KMeans y añade columna 'cluster' al df_base (sin NaN)."""
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    df_result = df_base.copy()
    df_result["cluster"] = km.fit_predict(X_scaled)
    return df_result, km


def pca_plot(X_scaled: np.ndarray, clusters: pd.Series) -> None:
    """Visualiza los clusters con PCA 2D."""
    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X_scaled)
    var_exp = pca.explained_variance_ratio_ * 100

    plt.figure()
    sc = plt.scatter(X_pca[:, 0], X_pca[:, 1], c=clusters, cmap="tab10", alpha=0.6, s=10)
    plt.colorbar(sc, label="Cluster")
    plt.xlabel(f"PCA 1 ({var_exp[0]:.1f}%)")
    plt.ylabel(f"PCA 2 ({var_exp[1]:.1f}%)")
    plt.title("Clusters de Escuelas")
    plt.tight_layout()
    plt.show()

def construir_preprocessor(num_cols: list, cat_cols: list) -> ColumnTransformer:
    num_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler())
    ])
    cat_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False))
    ])
    return ColumnTransformer([
        ("num", num_pipe, num_cols),
        ("cat", cat_pipe, cat_cols)
    ])

def entrenar_regresion(df: pd.DataFrame, target: str, num_cols: list,
                       cat_cols: list, modelo=None, test_size=0.2):
    X = df[num_cols + cat_cols]
    y = df[target]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42
    )
    if modelo is None:
        modelo = LinearRegression()

    pipe = Pipeline([
        ("preprocess", construir_preprocessor(num_cols, cat_cols)),
        ("regressor", modelo)
    ])
    pipe.fit(X_train, y_train)
    y_pred = pipe.predict(X_test)

    metricas = {"R2": r2_score(y_test, y_pred), "MAE": mean_absolute_error(y_test, y_pred)}
    print(metricas)
    return pipe, metricas