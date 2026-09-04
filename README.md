# Team Challenge SQL — TodoComponentes

Team Challenge del bootcamp de **AI Engineering**: diseño, implementación y carga de una
base de datos relacional completa para un e-commerce de electrónica y accesorios
tecnológicos (**TodoComponentes**), normalizada hasta 3NF, implementada en
**Google BigQuery** y poblada con datos sintéticos generados con Python.

> 📚 El enunciado completo de la Parte II está en [`Parte_II_Modelo_BD.ipynb`](./Parte_II_Modelo_BD.ipynb).

## Entidades del modelo

`customers` · `categories` · `products` · `orders` · `order_items` · `payments` · `reviews`

La relación **pedidos ↔ productos** es N:M, resuelta con la tabla intermedia
`order_items`, que además almacena el `unit_price` del momento de la compra.

## Estructura del repositorio

```
tc-sql-tu_equipo/
├── parte_1_sql_murder_mystery/
│   ├── data/
│   │   └── sql-murder-mystery.db
│   └── investigacion.ipynb
├── parte_2_modelo_bigquery/
│   ├── data/                 # vacío — los datos viven en BigQuery
│   ├── docs/
│   │   ├── er_diagram.png    # diagrama Entidad-Relación
│   │   └── normalizacion.md  # justificación 3NF (opcional)
│   └── notebooks/
│       ├── 01_setup_bigquery.ipynb
│       ├── 02_generate_data.ipynb
│       └── 03_queries_verification.ipynb
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

## Setup rápido

### 1) Entorno virtual

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux
pip install -r requirements.txt
```

### 2) Google Cloud

1. Crea un **proyecto** en [Google Cloud Console](https://console.cloud.google.com/).
2. Activa la **API de BigQuery**.
3. Crea una **Service Account** con rol `BigQuery Admin` y descarga la clave JSON
   en `credentials/service-account.json` (carpeta en `.gitignore`).
4. Crea un fichero `.env` a partir de `.env.example`:

   ```
   GCP_PROJECT_ID=tu-proyecto-gcp
   BQ_DATASET_ID=todo_componentes
   GOOGLE_APPLICATION_CREDENTIALS=./credentials/service-account.json
   ```

### 3) Ejecutar los notebooks

Desde `parte_2_modelo_bigquery/notebooks/`:

| Notebook | Qué hace |
|---|---|
| `01_setup_bigquery.ipynb` | Autentica, crea el dataset y las tablas en orden de dependencias FK |
| `02_generate_data.ipynb` | Genera datos sintéticos con Faker y los carga en BigQuery |
| `03_queries_verification.ipynb` | 5+ queries analíticas de verificación del modelo |

## Reglas

- `.env` y `credentials/` **nunca** se versionan.
- El entorno virtual `venv/` nunca se sube.
- Se sube `.env.example` como plantilla sin credenciales.
- Commits descriptivos con **Conventional Commits** (`feat:`, `fix:`, `docs:`, ...).
