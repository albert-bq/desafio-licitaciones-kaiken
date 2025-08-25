# Mini Sistema de Gestión de Licitaciones

Este proyecto es una aplicación web creada como solución al desafío técnico de Kaiken. El sistema funciona como una herramienta interna para que un equipo comercial pueda registrar y analizar licitaciones públicas adjudicadas.

[](https://www.google.com/search?q=https://URL-DE-TU-APP-DESPLEGADA.streamlit.app/)

## ✨ Características Principales

  * **Dashboard Interactivo:** Métricas clave y gráficos avanzados (rentabilidad, Pareto, tendencias) para la toma de decisiones estratégicas, con filtros dinámicos.
  * **Gestión de Licitaciones (CRUD):** Permite crear nuevas licitaciones, buscar, visualizar un análisis completo y editar registros existentes.
  * **Gestión de Clientes (CRUD):** Permite agregar y editar clientes, con validación de RUT chileno a nivel de aplicación y base de datos.
  * **Gestión de Productos (CRUD):** Interfaz para agregar y editar los productos de la empresa.
  * **Integridad de Datos:** Reglas de negocio implementadas tanto en la aplicación como en la base de datos (PostgreSQL) para garantizar la consistencia y seguridad de la información.

## 🛠️ Stack Tecnológico

  * **Frontend:** Streamlit
  * **Backend & Base de Datos:** Supabase (PostgreSQL)
  * **Lenguaje:** Python
  * **Librerías Clave:** Pandas (manipulación de datos), Plotly (visualizaciones), Psycopg2 (conexión a DB).
  * **Despliegue:** Streamlit Community Cloud

-----

## 🚀 Implementación y Puesta en Marcha

Para ejecutar este proyecto en un entorno local, sigue estos pasos:

### **1. Prerrequisitos**

  * Tener instalado Python 3.9+ y Git.
  * Una cuenta gratuita en [Supabase](https://supabase.com/) para crear la base de datos PostgreSQL.

### **2. Clonar el Repositorio**

```bash
git clone https://github.com/albert-bq/desafio-licitaciones-kaiken.git
cd desafio-licitaciones-kaiken
```

### **3. Configurar el Entorno Virtual**

Es una buena práctica aislar las dependencias del proyecto.

```bash
# Crear el entorno
python -m venv venv

# Activar el entorno
# En Windows:
venv\Scripts\activate
# En macOS/Linux:
source venv/bin/activate
```

### **4. Instalar Dependencias**

El archivo `requirements.txt` contiene todas las librerías necesarias.

```bash
pip install -r requirements.txt
```

### **5. Configurar la Base de Datos**

  * Crea un nuevo proyecto en **Supabase**.
  * Ve a **Project Settings \> Database** y copia tus credenciales de conexión.
  * Ve al **SQL Editor** de tu proyecto Supabase.
  * Copia y ejecuta el contenido de los archivos en la carpeta `sql/` en el siguiente orden:
    1.  `01.Crea tablas.sql`
    2.  `02.Reglas del Negocio.sql`
    3.  `03.RUT Chileno.sql`

### **6. Configurar los Secretos**

La aplicación se conecta a la base de datos de forma segura a través de un archivo de secretos.

  * En la raíz del proyecto, crea una carpeta llamada `.streamlit`.
  * Dentro de esa carpeta, crea un archivo llamado `secrets.toml`.
  * Copia y pega el siguiente contenido, reemplazando los valores con tus credenciales de Supabase (se recomienda usar la conexión **Session Pooler**):

<!-- end list -->

```toml
[database]
host = "tu-host-de-supabase"
port = "6543"
dbname = "postgres"
user = "tu-usuario-de-supabase"
password = "tu-contraseña-de-supabase"
```

### **7. Ejecutar la Aplicación**

Una vez configurado todo, inicia la aplicación con el siguiente comando:

```bash
streamlit run app.py
```

Se abrirá una pestaña en tu navegador con la aplicación funcionando localmente.

-----

## 📁 Estructura del Proyecto

```
.
├─── .streamlit/
│    └── secrets.toml      # Archivo de credenciales (ignorado por Git)
├─── scripts/              # Notebooks y scripts auxiliares
├─── sql/                  # Scripts para la creación y configuración de la DB
├─── app.py                # Código principal de la aplicación Streamlit
├─── README.md             # Documentación del proyecto
└─── requirements.txt      # Dependencias de Python
```