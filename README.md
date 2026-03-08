# Modelado de Impacto Educativo y Segmentación de Escuelas

Pipeline de análisis de datos educativos que integra múltiples fuentes del sistema educativo peruano para apoyar la toma de decisiones sobre implementación de programas como **Qué Maestro**.

## ¿Qué hace este proyecto?

1. Integra múltiples fuentes de datos del sistema educativo peruano
2. Genera features estructurales de las instituciones educativas
3. Agrupa escuelas mediante clustering (KMeans)
4. Entrena un modelo de regresión para analizar factores asociados al desempeño académico

---

## Estructura del proyecto

```
project/
│
├── main.py
├── pyproject.toml
│
├── rsc/
│   ├── model.py
│   └── utils.py
│
├── notebooks/
│   └── Distancia_institucion_highway.csv
│
└── data/
    └── URMECEA.xlsx
```

---

## Requisitos

- Python 3.12+
- pandas
- scikit-learn
- numpy
- matplotlib
- [uv](https://github.com/astral-sh/uv) (gestor de entornos y dependencias)

---

## Instalación

### 1. Clonar el repositorio

```bash
git clone <repo_url>
cd <repo>
```

### 2. Instalar uv

```bash
pip install uv
```

o en Linux/macOS:

```bash
curl -Ls https://astral.sh/uv/install.sh | sh
```

### 3. Sincronizar dependencias

```bash
uv sync
```

Esto instalará todas las dependencias definidas en `pyproject.toml`.

### 4. Activar el entorno virtual

```bash
# Linux / macOS
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

---

## Preparación de datos

Crea la carpeta `data` y coloca el archivo `URMECEA.xlsx` dentro:

```bash
mkdir data
```

```
data/
└── URMECEA.xlsx
```

> Este archivo contiene el histórico de evaluaciones educativas utilizado por el modelo.

---

## Ejecución

```bash
python main.py
```

El script realizará automáticamente:

1. Descarga de datasets públicos del Ministerio de Educación
2. Transformación e integración de datos
3. Generación de variables estructurales
4. Clustering de instituciones educativas
5. Entrenamiento del modelo de regresión

---

## Outputs generados

| Archivo | Descripción |
|---|---|
| `data/dataset_final.csv` | Dataset integrado con todas las variables estructurales y educativas |
| `data/escuelas_clusterizadas.csv` | Asignación de cluster por institución educativa |

---

## Pipeline analítico

```
Datos públicos MINEDU
        │
        ▼
Integración de datasets
        │
        ▼
Feature engineering
        │
        ▼
Clustering de escuelas (KMeans)
        │
        ▼
Perfilamiento de instituciones
        │
        ▼
Modelo de regresión (desempeño académico)
```

---

## Variables principales

| Variable | Descripción |
|---|---|
| `ratio_alumno_docente` | Relación entre número de alumnos y docentes |
| `infra_index` | Índice de infraestructura escolar |
| `n_aulas` | Número de aulas disponibles |
| `max_piso` | Número máximo de pisos del edificio |
| `dist_km_utm_log+1` | Distancia logarítmica a vía principal |

---

## Modelo

**Target:**
```
target = promedio(Evaluación_lectura, Evaluación_matematica)
```

**El pipeline incluye:**
- Imputación de datos faltantes
- Escalamiento de variables numéricas
- Codificación OneHot de variables categóricas
- Regresión lineal

---

## Visualizaciones

El pipeline genera automáticamente:

- **Método Elbow** — selección del número óptimo de clusters
- **PCA** — visualización de la distribución de clusters

---

## Nota

> El modelo debe interpretarse como herramienta de apoyo para la toma de decisiones, no como predicción determinística del desempeño educativo.
