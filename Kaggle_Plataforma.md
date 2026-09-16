# Plataforma Kaggle — Tabla Comparativa

**Documento elaborado por:** Bolt V12 (ThunderStudio) — Modo Investigador
**Fecha:** 13 de agosto de 2026

---

## ¿Qué es Kaggle?

Kaggle es la comunidad más grande del mundo de ciencia de datos y machine learning, propiedad de **Google (Alphabet Inc.)**. Permite a científicos de datos de todo el mundo competir en desafíos, descargar datasets públicos, aprender con cursos gratuitos y ejecutar notebooks en la nube con GPU/TPU.

**Sitio web oficial:** https://www.kaggle.com

---

## Tabla Comparativa de Kaggle

| Característica | Detalle |
|----------------|---------|
| Propietario | Google (Alphabet Inc.) |
| Tipo de plataforma | Comunidad de ciencia de datos y machine learning |
| Sitio web | https://www.kaggle.com |
| Datasets públicos | Más de 600,000 datasets abiertos (estimado 2025) |
| Formatos de datos soportados | CSV, JSON, SQLite (.db), Parquet, ZIP y archivos múltiples por dataset |
| Tipos de datos que maneja | Estructurados (CSV, SQLite, Parquet), semiestructurados (JSON) y no estructurados (imágenes, texto) |
| Herramientas de análisis | Notebooks en línea (Python y R) con GPU/TPU gratuitas limitadas |
| Competencias | Sí, con premios económicos, datasets de competencia y ranking global |
| Cursos | Cursos gratuitos: Python, SQL, ML, IA generativa, etc. |
| API / CLI | Kaggle API y CLI: `kaggle datasets download`, `kaggle competitions submit` |
| Plan gratuito | Sí. Almacenamiento para datasets públicos con límites variables por archivo/cuota |
| Planes de pago | Kaggle Pro / Teams: almacenamiento privado, mayor cuota de cómputo y soporte |
| Acceso a datos | Descarga web directa, API de Kaggle, notebooks integrados y conexión a BigQuery |
| Integración | Compatible con pandas, scikit-learn, TensorFlow, PyTorch y herramientas de ETL |

---

## Cómo usar Kaggle (comandos básicos)

### 1. Instalar la API de Kaggle
```bash
pip install kaggle
```

### 2. Descargar un dataset
```bash
kaggle datasets download -d <usuario>/<dataset>
```

### 3. Descargar archivos de una competencia
```bash
kaggle competitions download -c <nombre-competencia>
```

### 4. Subir una predicción a una competencia
```bash
kaggle competitions submit -c <nombre-competencia> -f <archivo.csv> -m "mensaje"
```

### 5. Listar datasets del usuario autenticado
```bash
kaggle datasets list --mine
```

---

## Nota importante

Las cuotas exactas de almacenamiento, cómputo y precios de Kaggle cambian con el tiempo; consultar la documentación oficial (https://www.kaggle.com/docs) para valores actualizados.

---

*Documento generado por Bolt V12 en modo investigador — ThunderStudio.*

---

## 📊 Dataset Seleccionado: Netflix Movies and TV Shows

**Elegido por Bolt V12 para Miguel** — ideal para practicar análisis con Power BI y Orange, porque son datos estructurados reales, listos para explorar y visualizar.

| Característica | Detalle |
|----------------|---------|
| Nombre del dataset | Netflix Movies and TV Shows |
| Autor / Usuario | Shivam Bansal (shivamb) |
| URL en Kaggle | https://www.kaggle.com/datasets/shivamb/netflix-shows |
| Formato | CSV (comprimido en ZIP) |
| Tamaño | ~1.4 MB (ZIP) |
| Filas | 8,807 |
| Columnas | 12 |
| Tipo de datos | Estructurados (tabular) |
| Nombres de columnas | show_id, type, title, director, cast, country, date_added, release_year, rating, duration, listed_in, description |
| ¿Por qué es interesante? | Dataset real de Netflix: mezcla películas y series con país, año, duración, rating y género. Perfecto para dashboards en Power BI, visualización en Orange y minería de texto con la columna description. |

---

*Dataset verificado por Bolt V12: descargado desde la API de Kaggle (8,807 filas, 12 columnas) — ThunderStudio.*
