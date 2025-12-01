import pickle
import pandas as pd
import numpy as np
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from contextlib import asynccontextmanager
from sentence_transformers import SentenceTransformer
from typing import List
from fastapi.middleware.cors import CORSMiddleware

"""
-----------------------------------------------------------------------------
MÓDULO DE INTERFAZ DE PROGRAMACIÓN DE APLICACIONES (API)
TRABAJO TERMINAL - SISTEMA "MEXCINE"
-----------------------------------------------------------------------------
Descripción:
    Este script define el servidor backend utilizando el framework FastAPI.
    Su responsabilidad es exponer el modelo de Machine Learning como un 
    microservicio RESTful, gestionando la carga eficiente de modelos en 
    memoria y validando las peticiones del cliente (Frontend).

Autores: [Nombre de tu equipo / Integrantes]
Versión: 1.0.0
-----------------------------------------------------------------------------
"""

# ------------------------------------------------------------
# DEFINICIÓN DE ESQUEMAS DE DATOS (DTOs)
# ------------------------------------------------------------
# Implementamos modelos Pydantic para asegurar la validación estricta de tipos
# en la entrada y salida de la API, cumpliendo con el contrato de interfaz.

class DescripcionRequest(BaseModel):
    """
    Modelo de entrada (Request Body).
    Valida que el cliente envíe estrictamente una cadena de texto.
    """
    descripcion: str

class PeliculaResponse(BaseModel):
    """
    Modelo de salida (Response Model).
    Estandariza la estructura JSON que recibirá el frontend, ocultando 
    datos internos del DataFrame que no son relevantes para el usuario.
    """
    titulo: str
    genero: str
    sinopsis: str
    anio: int

# ------------------------------------------------------------
# CONFIGURACIÓN DE ARTEFACTOS Y RUTAS
# ------------------------------------------------------------
KNN_MODEL_PATH = "model_artifacts/modelo_knn.pkl"
DATA_PATH = "model_artifacts/peliculas_info.pkl"
SENTENCE_MODEL_NAME = "all-MiniLM-L6-v2"

# Estructura global para mantener los modelos en memoria RAM
model_cache = {}

# ------------------------------------------------------------
# GESTIÓN DEL CICLO DE VIDA (LIFESPAN)
# ------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestor de contexto para la inicialización y cierre de la aplicación.
    
    Decisión de diseño:
    Utilizamos el evento 'startup' para cargar los modelos ML (BERT y KNN) 
    una única vez al iniciar el servidor. Esto evita la latencia de carga 
    (overhead) en cada petición del usuario y optimiza el uso de recursos.
    """
    # --- FASE DE ARRANQUE (STARTUP) ---
    print("--- [SISTEMA] Iniciando servidor y cargando recursos ---")
    
    print(f"-> Cargando modelo de lenguaje (NLP): '{SENTENCE_MODEL_NAME}'...")
    # Cargamos el modelo transformer en CPU/GPU según disponibilidad
    model_cache["sentence_transformer"] = SentenceTransformer(SENTENCE_MODEL_NAME)
    
    print(f"-> Deserializando modelo predictivo desde: '{KNN_MODEL_PATH}'...")
    with open(KNN_MODEL_PATH, "rb") as f:
        model_cache["knn_model"] = pickle.load(f)
        
    print(f"-> Cargando catálogo de metadatos desde: '{DATA_PATH}'...")
    with open(DATA_PATH, "rb") as f:
        data_dict = pickle.load(f)
        # Reconstruimos el DataFrame para búsquedas rápidas por índice
        model_cache["peliculas_df"] = pd.DataFrame.from_dict(data_dict)
    
    print("✅ Todos los modelos han sido cargados en memoria RAM.")
    
    yield  # La aplicación corre aquí
    
    # --- FASE DE CIERRE (SHUTDOWN) ---
    print("--- [SISTEMA] Deteniendo servidor ---")
    model_cache.clear()
    print("Memoria liberada correctamente.")


# ------------------------------------------------------------
# INICIALIZACIÓN DE FASTAPI
# ------------------------------------------------------------
app = FastAPI(
    title="API de Recomendación de Cine Mexicano (Mexcine)",
    description="Backend para inferencia de similitud semántica en tiempo real.",
    version="0.1.0",
    lifespan=lifespan 
)

# ------------------------------------------------------------
# CONFIGURACIÓN DE POLÍTICAS CORS (Seguridad)
# ------------------------------------------------------------
# Permitimos peticiones cruzadas únicamente desde nuestro cliente React
# para prevenir uso no autorizado de la API desde otros dominios.
origins = [
    "http://localhost:5173", 
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],        # Permitimos todos los verbos HTTP (GET, POST)
    allow_headers=["*"],
)


# ------------------------------------------------------------
# ENDPOINTS (Puntos de acceso)
# ------------------------------------------------------------

@app.get("/")
def read_root():
    """Health check: Verifica que el servicio esté operativo."""
    return {"status": "online", "servicio": "Mexcine API v1.0"}


@app.post("/recomendar", response_model=List[PeliculaResponse])
async def post_recomendar(request: DescripcionRequest):
    """
    Endpoint principal de inferencia.
    
    Flujo de ejecución:
    1. Preprocesamiento: Recibe texto del usuario.
    2. Vectorización: Convierte texto a embeddings (BERT).
    3. Inferencia: Busca los k-vecinos más cercanos (KNN).
    4. Filtrado: Aplica reglas de negocio (umbral de similitud).
    """
    
    # 1. Recuperamos modelos de la caché (operación O(1))
    model_st = model_cache["sentence_transformer"]
    knn = model_cache["knn_model"]
    df_peliculas = model_cache["peliculas_df"]
    
    # 2. Vectorización del input del usuario
    # Transformamos la descripción a un vector de 384 dimensiones
    vector_usuario = model_st.encode(request.descripcion).reshape(1, -1)

    # 3. Búsqueda de vecinos (Inferencia)
    # Solicitamos 15 vecinos para tener margen de filtrado posterior
    distancias, indices = knn.kneighbors(vector_usuario, n_neighbors=15)
    
    # 4. Reglas de Negocio
    UMBRAL_MINIMO = 0.80  # Definimos que una similitud < 80% no es relevante
    MAX_RESULTADOS = 15   # Límite de respuesta al cliente
    recomendaciones = []
    
    # Procesamos los vecinos encontrados
    for i in range(len(indices[0])):
        idx = indices[0][i]      # Índice en el DataFrame original
        dist = distancias[0][i]  # Distancia coseno
        
        # Conversión matemática: Similitud = 1 - Distancia Coseno
        # (Donde 0 es opuesto y 1 es idéntico)
        similitud = 1 - dist
        
        # Filtro de calidad (Thresholding)
        if similitud >= UMBRAL_MINIMO:
            pelicula_data = df_peliculas.iloc[idx]
            
            # Mapeo al modelo de respuesta (DTO)
            recomendaciones.append(PeliculaResponse(
                titulo=pelicula_data['titulo'],
                genero=pelicula_data['genero'],
                sinopsis=pelicula_data['sinopsis'],
                anio=pelicula_data['anio']
            ))
        
        # Early exit si alcanzamos el máximo deseado
        if len(recomendaciones) >= MAX_RESULTADOS:
            break

    return recomendaciones

# Bloque de ejecución para desarrollo local
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)