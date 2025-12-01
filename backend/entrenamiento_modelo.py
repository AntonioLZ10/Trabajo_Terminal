import pandas as pd
import pickle
from sqlalchemy import create_engine
from sentence_transformers import SentenceTransformer
from sklearn.neighbors import NearestNeighbors

"""
-----------------------------------------------------------------------------
MÓDULO DE ENTRENAMIENTO DEL MODELO DE RECOMENDACIÓN
TRABAJO TERMINAL
-----------------------------------------------------------------------------
Descripción:
    Este script orquesta el proceso ETL (Extracción, Transformación y Carga)
    para el motor de recomendación. Se encarga de conectar a la base de datos
    PostgreSQL, vectorizar el contenido textual mediante modelos BERT y
    entrenar el algoritmo de vecinos más cercanos (KNN).

Autores: [Cuellar Reyes Ethan Moisés, González Rojo Scarlett Michelle y Luna Zamora Juan Antonio]
-----------------------------------------------------------------------------
"""

# ------------------------------------------------------------
# CONFIGURACIÓN DE LA INFRAESTRUCTURA DE DATOS
# ------------------------------------------------------------
# Definimos las credenciales de acceso a nuestra base de datos local.
# Nota: Para el despliegue final, estas credenciales se migrarán a 
# variables de entorno por seguridad.
DB_USER = "postgres"
DB_PASS = "ns+E{XJ_ohhj9EQ)" 
DB_HOST = "34.123.117.28"
DB_PORT = "5432"
DB_NAME = "mexcine_db"

# Especificamos la tabla fuente normalizada que contiene el catálogo
TABLE_NAME = "peliculas"
# ------------------------------------------------------------


def obtener_datos():
    """
    Establece la conexión con la capa de persistencia (PostgreSQL) y recupera
    el dataset necesario para el entrenamiento.
    
    Returns:
        pd.DataFrame: DataFrame con las columnas 'anio', 'titulo', 'genero' y 'sinopsis'.
    
    Raises:
        ValueError: Si la consulta no retorna registros, detenemos el flujo para evitar errores en el modelo.
    """
    # Construimos la cadena de conexión utilizando el formato estándar de SQLAlchemy
    connection_url = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(connection_url)

    # Seleccionamos únicamente las características (features) relevantes para la similitud semántica
    query = f"""
        SELECT anio, titulo, genero, sinopsis
        FROM {TABLE_NAME};
    """

    print("--- [FASE 1] Iniciando extracción de datos ---")
    print(f"Conectando a base de datos: {DB_NAME} en {DB_HOST}...")
    
    df = pd.read_sql(query, engine)

    # Validación de integridad de los datos
    if df.empty:
        raise ValueError("Error crítico: La tabla está vacía. No es posible entrenar el modelo.")

    print(f"Éxito: Se han cargado {len(df)} registros en memoria.")
    return df


def generar_embeddings(df):
    """
    Transforma el lenguaje natural (sinopsis y género) en representaciones vectoriales densas.
    Utilizamos Sentence-BERT para capturar el contexto semántico de cada película.
    
    Args:
        df (pd.DataFrame): Dataset crudo.
        
    Returns:
        numpy.ndarray: Matriz de embeddings listos para el cálculo de distancias.
    """
    print("\n--- [FASE 2] Vectorización de texto (NLP) ---")
    
    # Seleccionamos 'all-MiniLM-L6-v2' por ser el compromiso óptimo entre 
    # velocidad de inferencia y precisión semántica para nuestra infraestructura.
    print("Cargando modelo pre-entrenado: all-MiniLM-L6-v2...")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    # Ingeniería de características: Concatenamos género y sinopsis para enriquecer 
    # el contexto del vector resultante. Manejamos valores nulos para evitar fallos.
    textos = (df["genero"].fillna("") + " " + df["sinopsis"].fillna("")).tolist()

    print(f"Generando embeddings para {len(textos)} elementos...")
    embeddings = model.encode(textos, show_progress_bar=True)

    return embeddings


def entrenar_knn(embeddings, k=5):
    """
    Entrena el modelo de vecinos más cercanos (NearestNeighbors).
    
    Optamos por KNN debido a su eficiencia en sistemas de recomendación basados en contenido,
    donde la proximidad en el espacio vectorial indica similitud temática.
    
    Args:
        embeddings (numpy.ndarray): Matriz de vectores.
        k (int): Número de vecinos a considerar (default: 5).
        
    Returns:
        sklearn.neighbors.NearestNeighbors: Modelo ajustado.
    """
    print("\n--- [FASE 3] Entrenamiento del modelo (KNN) ---")
    
    # Utilizamos la métrica 'cosine' ya que es independiente de la magnitud del vector,
    # midiendo puramente la orientación (similitud semántica) en espacios de alta dimensión.
    print(f"Configurando KNN con métrica 'cosine' y k={k}...")
    knn = NearestNeighbors(n_neighbors=k, metric="cosine")
    
    knn.fit(embeddings)
    print("Modelo ajustado correctamente.")
    return knn


def guardar_archivos(knn, embeddings, df):
    """
    Serializa los objetos críticos del sistema para su uso en el backend (API).
    Almacenamos el modelo, los vectores y los metadatos para evitar re-entrenamientos 
    en cada petición del usuario.
    """
    print("\n--- [FASE 4] Persistencia de artefactos ---")

    # Guardamos el modelo KNN
    with open("backend/modelo_knn.pkl", "wb") as f:
        pickle.dump(knn, f)

    # Guardamos la matriz de embeddings (necesaria para futuras inferencias)
    with open("backend/embeddings.pkl", "wb") as f:
        pickle.dump(embeddings, f)

    # Guardamos el catálogo como diccionario para una búsqueda rápida (O(1)) por índice
    with open("backend/peliculas_info.pkl", "wb") as f:
        pickle.dump(df.to_dict(), f)

    print("✅ Serialización completada. Archivos generados en /backend:")
    print("   -> modelo_knn.pkl (Lógica de recomendación)")
    print("   -> embeddings.pkl (Espacio vectorial)")
    print("   -> peliculas_info.pkl (Metadatos)")


# Punto de entrada principal
if __name__ == "__main__":
    try:
        # Orquestación secuencial del pipeline
        df_peliculas = obtener_datos()
        matriz_embeddings = generar_embeddings(df_peliculas)
        modelo_entrenado = entrenar_knn(matriz_embeddings)
        guardar_archivos(modelo_entrenado, matriz_embeddings, df_peliculas)

        print("\n🎉 Proceso finalizado: El sistema de recomendación está listo para despliegue.\n")
        
    except Exception as e:
        print("\n⚠ Excepción crítica durante la ejecución del pipeline:")
        print(f"Detalle del error: {str(e)}")