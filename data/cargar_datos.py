import pandas as pd
from sqlalchemy import create_engine
import sys
import logging

# --- CONFIGURACIÓN DE LA BASE DE DATOS ---
DB_USER = "postgres"
DB_PASS = "5525165572"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "Trabajo_Terminal"
# -----------------------------------------

EXCEL_FILE = "../dataset.xlsx"  # Ajustado para que funcione desde /data/
TABLE_NAME = "peliculas"

# --- CONFIGURACIÓN DEL LOG ---
logging.basicConfig(
    filename="registros_descartados.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
# -----------------------------------------


def log_descartado(df_descartado, motivo):
    """
    Registra en el archivo .log el motivo del descarte y las filas afectadas.
    """
    for _, row in df_descartado.iterrows():
        logging.info(f"Registro descartado ({motivo}): {row.to_dict()}")


def cargar_datos_a_postgres():
    try:
        # Conexión a la base de datos
        connection_url = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        print(f"Conectando a la base de datos '{DB_NAME}' en {DB_HOST}...")
        engine = create_engine(connection_url)

        # Lectura del archivo Excel
        print(f"Leyendo el archivo '{EXCEL_FILE}'...")
        df = pd.read_excel(EXCEL_FILE, engine='openpyxl')

        if df.empty:
            print(f"Error: El archivo '{EXCEL_FILE}' está vacío.")
            return

        print(f"Se encontraron {len(df)} registros en el archivo original.")
        print("Columnas detectadas en el Excel:", df.columns.tolist())

        # --- NORMALIZACIÓN DE NOMBRES DE COLUMNAS ---
        df.columns = (
            df.columns
              .str.strip()
              .str.lower()
              .str.normalize("NFKD")
              .str.encode("ascii", errors="ignore")
              .str.decode("utf-8")
        )

        # Mapeo para que coincida con la estructura SQL
        column_mapping = {
            'ano': 'anio',
            'titulo': 'titulo',
            'genero': 'genero',
            'sinopsis': 'sinopsis',
            'fuente': 'fuente'
        }
        df = df.rename(columns=column_mapping)

        columnas_sql = ['anio', 'titulo', 'genero', 'sinopsis', 'fuente']
        df = df[columnas_sql]

        # --- PREPROCESAMIENTO DE LIMPIEZA ---
        print("Realizando limpieza de datos...")

        # Filas completamente vacías
        vacias = df[df.isna().all(axis=1)]
        if not vacias.empty:
            log_descartado(vacias, "Fila completamente vacía")
        df = df.dropna(how='all')

        # Faltan datos en columnas obligatorias
        obligatorias = ['anio', 'titulo', 'genero']
        faltantes = df[df[obligatorias].isna().any(axis=1)]
        if not faltantes.empty:
            log_descartado(faltantes, "Faltan valores obligatorios")
        df = df.dropna(subset=obligatorias)

        # Conversión del año a entero
        df['anio'] = pd.to_numeric(df['anio'], errors='coerce')
        invalidos_anio = df[df['anio'].isna()]
        if not invalidos_anio.empty:
            log_descartado(invalidos_anio, "Valor no numérico en columna año")
        df = df.dropna(subset=['anio'])
        df['anio'] = df['anio'].astype(int)

        # Limpieza de textos
        cols_texto = ['titulo', 'genero', 'sinopsis', 'fuente']
        for col in cols_texto:
            df[col] = df[col].astype(str).str.strip()

        print(f"Registros restantes después de limpieza: {len(df)}")

        # --- INSERCIÓN EN LA BASE DE DATOS ---
        print(f"Insertando datos en la tabla '{TABLE_NAME}'...")
        df.to_sql(TABLE_NAME, engine, if_exists='append', index=False)

        print("\n✅ Proceso completado con éxito.")
        print("➡ Datos cargados en PostgreSQL.")
        print("➡ Registros descartados almacenados en registros_descartados.log")

    except FileNotFoundError:
        print(f"Error: No se pudo encontrar '{EXCEL_FILE}'.", file=sys.stderr)
        print("Asegúrate de estar ejecutando el script desde la carpeta correcta.", file=sys.stderr)

    except Exception as e:
        print("\nHa ocurrido un error inesperado:", file=sys.stderr)
        print(e, file=sys.stderr)
        print("\nConsejo: Verifica las columnas del Excel o que PostgreSQL esté corriendo.", file=sys.stderr)


if __name__ == "__main__":
    cargar_datos_a_postgres()
