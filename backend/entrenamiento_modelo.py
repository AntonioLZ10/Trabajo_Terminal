import pandas as pd
import pickle
from sqlalchemy import create_engine
from sentence_transformers import SentenceTransformer
from sklearn.neighbors import NearestNeighbors


# ------------------------------------------------------------
# CONFIGURACIÓN DE LA CONEXIÓN (credenciales explícitas)
# ------------------------------------------------------------
DB_USER = "postgres"
DB_PASS = "5525165572"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "Trabajo_Terminal"

# Nombre de la tabla donde guardaste los datos desde Excel
TABLE_NAME = "peliculas"
# ------------------------------------------------------------


def obtener_datos():
    """Obtiene título, género y sinopsis desde PostgreSQL."""
    connection_url = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(connection_url)

    query = f"""
        SELECT anio, titulo, genero, sinopsis
        FROM {TABLE_NAME};
    """

    print("Conectando a PostgreSQL y obteniendo datos...")
    df = pd.read_sql(query, engine)

    if df.empty:
        raise ValueError("La tabla no contiene datos, no es posible entrenar el modelo.")

    print(f"Películas obtenidas: {len(df)}")
    return df


def generar_embeddings(df):
    """Convierte sinopsis y género en vectores mediante BERT."""
    print("Cargando modelo BERT (Sentence Transformers)...")
    model = SentenceTransformer("all-MiniLM-L6-v2")  # modelo ligero y eficiente

    textos = (df["genero"].fillna("") + " " + df["sinopsis"].fillna("")).tolist()

    print("Generando embeddings con BERT...")
    embeddings = model.encode(textos, show_progress_bar=True)

    return embeddings


def entrenar_knn(embeddings, k=5):
    """Entrena un modelo KNN para similitud de películas."""
    print("Entrenando modelo de similitud (KNN)...")
    knn = NearestNeighbors(n_neighbors=k, metric="cosine")
    knn.fit(embeddings)
    return knn


def guardar_archivos(knn, embeddings, df):
    """Guarda modelo, embeddings y metadatos en archivos .pkl."""
    print("Guardando resultados del entrenamiento...")

    with open("backend/modelo_knn.pkl", "wb") as f:
        pickle.dump(knn, f)

    with open("backend/embeddings.pkl", "wb") as f:
        pickle.dump(embeddings, f)

    with open("backend/peliculas_info.pkl", "wb") as f:
        pickle.dump(df.to_dict(), f)

    print("✅ Archivos generados exitosamente:")
    print(" - backend/modelo_knn.pkl")
    print(" - backend/embeddings.pkl")
    print(" - backend/peliculas_info.pkl")


# Ejecución principal del script
if __name__ == "__main__":
    try:
        df = obtener_datos()
        embeddings = generar_embeddings(df)
        knn = entrenar_knn(embeddings)
        guardar_archivos(knn, embeddings, df)

        print("\n🎉 Entrenamiento completado correctamente.\n")
    except Exception as e:
        print("\n⚠ Error durante el entrenamiento:")
        print(str(e))
