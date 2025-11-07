import pickle
import pandas as pd
import numpy as np
from fastapi import FastAPI
from pydantic import BaseModel
from contextlib import asynccontextmanager
from sentence_transformers import SentenceTransformer
from typing import List
from fastapi.middleware.cors import CORSMiddleware  # <-- Import de CORS
import uvicorn

# --- MODELOS DE DATOS PYDANTIC ---
class DescripcionRequest(BaseModel):
    """El 'contrato' de lo que esperamos recibir en el request."""
    descripcion: str

class PeliculaResponse(BaseModel):
    """El 'contrato' de lo que vamos a devolver por cada película."""
    titulo: str
    genero: str
    sinopsis: str
    anio: int
# ------------------------------------

# --- Rutas a los artefactOS del modelo ---
KNN_MODEL_PATH = "model_artifacts/modelo_knn.pkl"
DATA_PATH = "model_artifacts/peliculas_info.pkl"
SENTENCE_MODEL_NAME = "all-MiniLM-L6-v2"

# --- Caché del Modelo ---
model_cache = {}

# --- Context Manager 'lifespan' (Carga de modelos al inicio) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- CÓDIGO DE INICIO (startup) ---
    print("Iniciando la aplicación...")
    
    print(f"Cargando modelo SentenceTransformer: '{SENTENCE_MODEL_NAME}'...")
    model_cache["sentence_transformer"] = SentenceTransformer(SENTENCE_MODEL_NAME)
    
    print(f"Cargando modelo KNN desde: '{KNN_MODEL_PATH}'...")
    with open(KNN_MODEL_PATH, "rb") as f:
        model_cache["knn_model"] = pickle.load(f)
        
    print(f"Cargando datos de películas desde: '{DATA_PATH}'...")
    with open(DATA_PATH, "rb") as f:
        data_dict = pickle.load(f)
        model_cache["peliculas_df"] = pd.DataFrame.from_dict(data_dict)
    
    print("¡Modelos cargados y listos!")
    
    yield
    
    # --- CÓDIGO DE APAGADO (shutdown) ---
    print("Apagando la aplicación...")
    model_cache.clear()
    print("Caché de modelos limpiado.")

# --- Creación de la App FastAPI ---
app = FastAPI(
    title="API de Recomendación de Cine Mexicano (Mexcine)",
    description="Proyecto de Trabajo Terminal (basado en el doc)",
    version="0.1.0",
    lifespan=lifespan  # Conectamos el 'lifespan'
)

# --- [ LA SOLUCIÓN DE CORS ] ---
# ¡¡Este bloque DEBE IR DESPUÉS de crear 'app = FastAPI(...)'!!
origins = [
    "http://localhost:5173", # La dirección de tu frontend de React
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       # Permite estos orígenes
    allow_credentials=True,
    allow_methods=["*"],         # Permite todos los métodos (GET, POST, etc.)
    allow_headers=["*"],         # Permite todos los headers
)
# --- [ FIN DEL BLOQUE CORS ] ---


# --- Endpoint de prueba ---
@app.get("/")
def read_root():
    """Endpoint raíz para verificar que la API está funcionando."""
    return {"mensaje": "¡Bienvenido a la API de Mexcine!"}

# --- ENDPOINT DE RECOMENDACIÓN ---
@app.post("/recomendar", response_model=List[PeliculaResponse])
async def post_recomendar(request: DescripcionRequest):
    """
    Recibe la descripción de un usuario, la vectoriza y devuelve
    las películas más similares que cumplan con el umbral.
    """
    
    # 1. Vectorizar la descripción del usuario
    model_st = model_cache["sentence_transformer"]
    descripcion_texto = request.descripcion
    vector_usuario = model_st.encode(descripcion_texto).reshape(1, -1)

    # 2. Consultar el modelo KNN
    knn = model_cache["knn_model"]
    distancias, indices = knn.kneighbors(vector_usuario)
    
    # 3. Aplicar reglas de negocio y formatear la respuesta
    df_peliculas = model_cache["peliculas_df"]
    
    # (Dejamos tu umbral de prueba, ¡a ver que pedo!)
    UMBRAL_MINIMO = 0.50 
    
    MAX_RESULTADOS = 3
    recomendaciones = []
    
    # Iteramos sobre los resultados
    for i in range(len(indices[0])):
        idx = indices[0][i]       # El índice (posición) de la película
        dist = distancias[0][i]   # La distancia de la película
        
        similitud = 1 - dist
        
        # Filtramos por el umbral mínimo
        if similitud >= UMBRAL_MINIMO:
            
            pelicula_data = df_peliculas.iloc[idx]
            
            recomendaciones.append(PeliculaResponse(
                titulo=pelicula_data['titulo'],
                genero=pelicula_data['genero'],
                sinopsis=pelicula_data['sinopsis'],
                anio=pelicula_data['anio']
            ))
        
        # Filtramos por el máximo de resultados
        if len(recomendaciones) >= MAX_RESULTADOS:
            break

    # 4. Devolver la lista de recomendaciones
    return recomendaciones

# --- Ejecutar la API (para pruebas locales) ---
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)