import os
from sentence_transformers import SentenceTransformer

# --- CONFIGURACIÓN ---
# Este nombre debe coincidir con el que usas en tu main.py
# Si decidiste usar el 'bert-base-multilingual-cased', cambia este nombre aquí.
MODEL_NAME = "all-MiniLM-L6-v2"

# Carpeta local donde guardaremos los archivos físicos
MODEL_PATH = "./model_files"

def descargar_modelo():
    print(f"⬇️  Iniciando descarga del modelo: '{MODEL_NAME}'...")
    
    # Descargamos y guardamos el modelo en la carpeta local
    model = SentenceTransformer(MODEL_NAME)
    model.save(MODEL_PATH)
    
    print(f"✅ Modelo guardado exitosamente en la carpeta: {MODEL_PATH}")
    print("   Ahora el contenedor usará estos archivos en lugar de internet.")

if __name__ == "__main__":
    descargar_modelo()