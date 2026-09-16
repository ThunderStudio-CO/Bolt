# Tipos de Datos y Representación de los Datos

**Curso/Área:** Ciencia de Datos
**Elaborado por:** Bolt V12 (ThunderStudio) — Modo Investigador
**Fecha:** 13 de agosto de 2026

---

## 1. Introducción

El dato es la unidad mínima de información con significado. En ciencia de datos, comprender los **tipos de datos** y sus **formas de representación** es fundamental, porque determinan qué técnicas de análisis, modelado y visualización pueden aplicarse. Una clasificación errónea de un dato puede invalidar un modelo completo.

---

## 2. Tipos de Datos

### 2.1 Clasificación según su naturaleza estadística

| Tipo | Subtipo | Descripción | Ejemplos |
|------|---------|-------------|----------|
| **Numérico** | Continuo | Puede tomar cualquier valor en un intervalo | Altura (1.75 m), temperatura (36.5 °C) |
| **Numérico** | Discreto | Solo valores enteros o contables | Número de hijos, cantidad de ventas |
| **Categórico** | Nominal | Categorías sin orden intrínseco | Color, sexo, ciudad |
| **Categórico** | Ordinal | Categorías con orden significativo | Nivel educativo (básico, medio, superior) |
| **Binario** | — | Solo dos valores posibles | Sí/No, 0/1, verdadero/falso |

### 2.2 Clasificación según su estructura

1. **Datos estructurados**: organizados en filas y columnas con esquema fijo.
2. **Datos semiestructurados**: tienen estructura flexible (JSON, XML).
3. **Datos no estructurados**: sin esquema definido (texto libre, imágenes, audio).

---

## 3. Representación de los Datos

La representación es la forma en que los datos se codifican, almacenan y visualizan.

### 3.1 Representación interna (computacional)

- **Binaria (0 y 1):** base de todo almacenamiento digital.
- **Enteros y flotantes:** representación numérica en memoria.
- **Caracteres:** codificaciones como ASCII y Unicode/UTF-8.
- **Fechas y horas:** formatos ISO 8601 (ej. 2026-08-13T18:00:00Z).

### 3.2 Representación tabular

- Tablas relacionales (SQL)
- Hojas de cálculo (Excel, CSV)
- DataFrames (pandas en Python)

### 3.3 Representación gráfica y visual

- **Barras y columnas:** comparación de categorías.
- **Líneas:** evolución temporal.
- **Dispersión:** relación entre variables numéricas.
- **Histogramas:** distribución de frecuencia.
- **Mapas de calor:** correlaciones o densidad.

---

## 4. Datos Estructurados

### 4.1 Definición

Los **datos estructurados** son aquellos que poseen un **esquema predefinido**, organizados en registros y campos, generalmente en formato de tabla.

### 4.2 Características

- Alta organización y consistencia.
- Acceso mediante lenguajes de consulta (SQL).
- Fáciles de almacenar, buscar y analizar.
- Ocupan menos espacio si están normalizados.

### 4.3 Fuentes comunes

- Bases de datos relacionales (MySQL, PostgreSQL, SQL Server).
- Archivos CSV, TSV y Excel.
- APIs con respuestas tabulares.

### 4.4 Ejemplo

| ID | Nombre | Edad | Ciudad |
|----|--------|------|--------|
| 1 | Ana | 28 | La Paz |
| 2 | Luis | 35 | Santa Cruz |
| 3 | Marta | 24 | Cochabamba |

---

## 5. Datos No Estructurados

### 5.1 Definición

Los **datos no estructurados** no tienen un formato o esquema predefinido. Representan aproximadamente el **80-90% de los datos generados actualmente** (según estimaciones de la industria).

### 5.2 Formas y representaciones posibles

| Forma | Descripción | Representación típica |
|-------|-------------|----------------------|
| **Texto libre** | Documentos, correos, publicaciones | String, HTML, PDF, DOCX |
| **Imágenes** | Fotos, radiografías, capturas | Matriz de píxeles (RGB), PNG, JPEG |
| **Audio** | Grabaciones, podcasts, llamadas | Series temporales de amplitud (WAV, MP3) |
| **Video** | Secuencias de cuadros con audio | Contenedores MP4, AVI, secuencia de frames |
| **Redes sociales** | Tuits, comentarios, likes | JSON de API, texto + metadatos |

### 5.3 Cómo se procesan

- **NLP (Procesamiento de Lenguaje Natural):** tokenización, embeddings (Word2Vec, BERT).
- **Visión por computadora:** convoluciones, extracción de features.
- **Procesamiento de audio:** espectrogramas, MFCC.
- **Almacenamiento:** bases NoSQL (MongoDB), data lakes, sistemas de archivos distribuidos.

### 5.4 Desafíos

- Dificultad de búsqueda y consulta.
- Requieren preprocesamiento intensivo.
- Consumen grandes volúmenes de almacenamiento.
- Análisis más complejo (IA/ML avanzado).

---

## 6. Comparación General

| Criterio | Estructurado | Semiestructurado | No estructurado |
|----------|--------------|------------------|-----------------|
| Esquema | Fijo | Flexible | Inexistente |
| Ejemplos | SQL, CSV | JSON, XML | Texto, imagen, audio |
| Almacenamiento | BBDD relacionales | BBDD documentales | Data lakes, NoSQL |
| Análisis | Estadística simple | Mixto | IA/ML, NLP, visión |
| Dificultad de análisis | Baja | Media | Alta |

---

## 7. Hipótesis y Consideraciones Metodológicas

- **Hipótesis:** "Un dato bien clasificado según su tipo mejora la precisión del modelo y reduce el sesgo en el preprocesamiento."
- **Metodología sugerida:** para cada dataset, ejecutar análisis exploratorio (EDA), verificar tipos con `dtypes`/`summary()`, y aplicar codificación adecuada (one-hot, label encoding, normalización).

---

## 8. Bibliografía y Fuentes de Referencia

1. Provost, F. & Fawcett, T. (2013). *Data Science for Business*. O'Reilly.
2. Tan, P.N., Steinbach, M. & Kumar, V. (2005). *Introduction to Data Mining*. Pearson.
3. Documentación oficial de pandas: https://pandas.pydata.org/docs/
4. Tutoriales de Khan Academy / estadística básica sobre tipos de variables.
5. Artículos de Toward Data Science sobre datos estructurados vs no estructurados.

---

*Documento generado por Bolt V12 en modo investigador.*


---

## 9. Plataforma Kaggle (Tabla Comparativa)

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

**Nota:** las cuotas exactas de almacenamiento, cómputo y precios de Kaggle cambian con el tiempo; consultar la documentación oficial (https://www.kaggle.com/docs) para valores actualizados.

---

*Documento actualizado por Bolt V12 — incluida tabla comparativa de Kaggle.*
