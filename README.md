Desafío de Análisis de Licitaciones - Kaiken
Este README es un documento vivo y se actualizará progresivamente con cada avance del proyecto.

Versión: 0.1.0
Última actualización: 25 de agosto de 2025

Descripción
Este proyecto tiene como objetivo analizar datos de licitaciones para identificar patrones, tendencias y oportunidades. El análisis se centra en la relación entre productos, órdenes de compra y clientes en el contexto de licitaciones públicas o privadas.

El pipeline de trabajo actual consiste en:

Exploración y Limpieza de Datos con Python (Jupyter Notebooks).

Estructuración de Datos en un esquema de base de datos relacional.

(Futuro) Análisis y Visualización para extraer insights.

Estructura del Proyecto
El repositorio está organizado de la siguiente manera para mantener un flujo de trabajo claro y ordenado.

.
│   README.md                # Documentación principal del proyecto
│
├───scripts/                 # Contiene todos los scripts de análisis y procesamiento
│   │   01.Datos de Muestra.ipynb  # Notebook para exploración y limpieza de datos
│   │
│   └───data/                # Almacena los datasets
│           clientes_sample.csv
│           order_sample.csv
│           product_sample.csv
│           tender_sample.csv
│           order_sample_clean.csv      # Archivos procesados y limpios
│           product_sample_clean.csv
│           tender_sample_clean.csv
│
└───sql/                     # Scripts para la gestión de la base de datos
        01.Crea tablas.sql       # Script DDL para crear la estructura de las tablas
Cómo Empezar
Para replicar el análisis, sigue estos pasos:

Prerrequisitos
Tener instalado Python 3.x.

Tener instalado un gestor de paquetes como pip o conda.

(Opcional) Un motor de base de datos compatible con SQL (ej. PostgreSQL, SQLite).

Instalación
Clona este repositorio:

Bash

git clone <URL-de-tu-repositorio>
cd desafio-licitaciones-kaiken
(Recomendado) Crea un entorno virtual e instala las dependencias:

Bash

python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt # AÚN NO CREADO
Uso
Ejecutar el Notebook: Abre y ejecuta el archivo scripts/01.Datos de Muestra.ipynb utilizando Jupyter Lab o Jupyter Notebook para procesar los datos de la carpeta scripts/data/.

Crear la Base de Datos: Ejecuta el script sql/01.Crea tablas.sql en tu motor de base de datos para generar la estructura necesaria.

Próximos Pasos (TODO)
Esta sección se actualizará con cada commit para reflejar el progreso y las tareas pendientes.

[ ] Crear el archivo requirements.txt con las librerías necesarias (pandas, numpy, etc.).

[ ] Desarrollar un script en Python para cargar los archivos .csv limpios a la base de datos SQL.

[ ] Añadir análisis estadísticos descriptivos en el notebook.

[ ] Generar las primeras visualizaciones para identificar relaciones clave.

[ ] Documentar los hallazgos iniciales del análisis exploratorio.

