import pandas as pd
from sqlalchemy import create_engine
import sys
import logging

"""
-----------------------------------------------------------------------------
MÓDULO DE INGESTA Y LIMPIEZA DE DATOS (ETL)
TRABAJO TERMINAL
-----------------------------------------------------------------------------
Descripción:
    Este script automatiza el proceso de Extracción, Transformación y Carga (ETL).
    Lee la fuente de datos cruda (Excel), aplica reglas de normalización y limpieza
    para asegurar la integridad referencial, y finalmente inserta los registros
    validados en la base de datos PostgreSQL.
    
    Incluye un sistema de logging para auditar los registros rechazados.

Autores: [Nombre de tu equipo / Integrantes]
Fecha: Noviembre 2025
-----------------------------------------------------------------------------
"""

# ------------------------------------------------------------
# CONFIGURACIÓN DEL ENTORNO DE DESARROLLO
# ------------------------------------------------------------
# Credenciales de acceso a la capa de persistencia.
DB_USER = "postgres"
DB_PASS = "ns+E{XJ_ohhj9EQ)"
DB_HOST = "34.123.117.28"
DB_PORT = "5432"
DB_NAME = "mexcine_db"
# ------------------------------------------------------------

# Definición de fuentes de datos y destino
EXCEL_FILE = "dataset2.xlsx"  
TABLE_NAME = "peliculas"

# ------------------------------------------------------------
# SISTEMA DE AUDITORÍA (LOGGING)
# ------------------------------------------------------------
# Configuramos un log persistente para mantener la trazabilidad de los datos.
# Esto nos permite saber exactamente qué registros se descartaron y por qué,
# sin detener la ejecución del pipeline principal.
logging.basicConfig(
    filename="registros_descartados.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def log_descartado(df_descartado, motivo):
    """
    Auxiliar para registrar incidentes de calidad de datos.
    Escribe en el archivo .log las filas que no cumplieron las reglas de negocio.
    """
    for _, row in df_descartado.iterrows():
        # Convertimos la fila a dict para un registro legible en el log
        logging.info(f"Registro descartado ({motivo}): {row.to_dict()}")


def cargar_datos_a_postgres():
    """
    Función principal del pipeline ETL.
    """
    try:
        # --- FASE 1: EXTRACCIÓN (Extract) ---
        connection_url = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        print(f"--- [ETL] Iniciando proceso de ingesta ---")
        print(f"Estableciendo conexión con: {DB_NAME} en {DB_HOST}...")
        engine = create_engine(connection_url)

        print(f"Leyendo fuente de datos cruda: '{EXCEL_FILE}'...")
        df = pd.read_excel(EXCEL_FILE, engine='openpyxl')

        # Validación inicial de existencia de datos
        if df.empty:
            print(f"Error crítico: El archivo fuente '{EXCEL_FILE}' no contiene registros.")
            return

        print(f"Dataset cargado en memoria. Total registros crudos: {len(df)}")
        
        # --- FASE 2: TRANSFORMACIÓN Y LIMPIEZA (Transform) ---
        
        # 2.1 Normalización de Metadatos (Cabeceras)
        # Estandarizamos los nombres de columnas para evitar errores de mapeo SQL
        # (eliminamos espacios, acentos y convertimos a minúsculas).
        df.columns = (
            df.columns
              .str.strip()
              .str.lower()
              .str.normalize("NFKD")
              .str.encode("ascii", errors="ignore")
              .str.decode("utf-8")
        )

        # 2.2 Mapeo de Esquema
        # Alineamos las columnas del Excel con el esquema definido en PostgreSQL
        column_mapping = {
            'ano': 'anio',       # Corrección ortográfica para base de datos
            'titulo': 'titulo',
            'genero': 'genero',
            'sinopsis': 'sinopsis',
            'fuente': 'fuente'
        }
        df = df.rename(columns=column_mapping)

        # Filtramos solo las columnas que existen en nuestro modelo de datos
        columnas_sql = ['anio', 'titulo', 'genero', 'sinopsis', 'fuente']
        # Nota: Si el excel trae columnas extra, las ignoramos aquí.
        try:
            df = df[columnas_sql]
        except KeyError as e:
            print(f"Error de esquema: Falta una columna requerida en el Excel: {e}")
            return

        print("Aplicando reglas de Calidad de Datos (Data Quality Gates)...")

        # 2.3 Regla: Integridad Completa
        # Descartamos filas que no tengan información útil (todo vacío)
        vacias = df[df.isna().all(axis=1)]
        if not vacias.empty:
            log_descartado(vacias, "Fila completamente vacía")
        df = df.dropna(how='all')

        # 2.4 Regla: Campos Obligatorios
        # Un registro no sirve para el modelo si no tiene Título o Género
        obligatorias = ['anio', 'titulo', 'genero']
        faltantes = df[df[obligatorias].isna().any(axis=1)]
        if not faltantes.empty:
            log_descartado(faltantes, "Violación de restricción NOT NULL (Faltan valores)")
        df = df.dropna(subset=obligatorias)

        # 2.5 Regla: Tipado de Datos (Año)
        # Forzamos conversión a numérico y descartamos basura (ej: "año 2000 aprox")
        df['anio'] = pd.to_numeric(df['anio'], errors='coerce')
        invalidos_anio = df[df['anio'].isna()]
        if not invalidos_anio.empty:
            log_descartado(invalidos_anio, "Error de tipo de dato: Año no numérico")
        df = df.dropna(subset=['anio'])
        df['anio'] = df['anio'].astype(int)

        # 2.6 Sanitización de Texto
        # Eliminamos espacios en blanco al inicio/final que ensucian la base de datos
        cols_texto = ['titulo', 'genero', 'sinopsis', 'fuente']
        for col in cols_texto:
            df[col] = df[col].astype(str).str.strip()

        print(f"Registros válidos tras limpieza: {len(df)}")

        # --- FASE 3: CARGA (Load) ---
        print(f"Insertando lote de datos en tabla '{TABLE_NAME}'...")
        
        # Usamos 'append' para agregar datos históricos sin borrar lo existente
        df.to_sql(TABLE_NAME, engine, if_exists='append', index=False)

        print("\n✅ Pipeline ETL ejecutado exitosamente.")
        print("➡ Datos persistidos en PostgreSQL.")
        print("➡ Reporte de anomalías generado en: registros_descartados.log")

    except FileNotFoundError:
        print(f"Error de I/O: No se encuentra el archivo fuente '{EXCEL_FILE}'.", file=sys.stderr)
        print("Verifique la ruta relativa del script.", file=sys.stderr)

    except Exception as e:
        print("\n⚠ Excepción no controlada durante el proceso:", file=sys.stderr)
        print(e, file=sys.stderr)
        print("Sugerencia: Verifique que el servicio de PostgreSQL esté activo.", file=sys.stderr)


if __name__ == "__main__":
    cargar_datos_a_postgres()