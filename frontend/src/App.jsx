import React, { useState } from 'react';
import axios from 'axios';

// --- El Componente Principal de nuestra Aplicación ---
function App() {
  
  // --- Estados de React ---
  const [descripcion, setDescripcion] = useState("");
  const [recomendaciones, setRecomendaciones] = useState([]);
  const [estadoApp, setEstadoApp] = useState("buscando"); // 'buscando', 'resultados', 'sin_resultados'
  const [error, setError] = useState(null);

  const API_URL = "http://127.0.0.1:8000/recomendar";

  /**
   * Se ejecuta cuando el usuario hace clic en "Buscar"
   */
  const handleBuscar = async () => {
    if (descripcion.trim() === "") return;
    setError(null);
    
    // Mostramos un "cargando" temporal (opcional)
    setEstadoApp("cargando"); 

    try {
      const respuesta = await axios.post(API_URL, {
        descripcion: descripcion 
      });

      if (respuesta.data && respuesta.data.length > 0) {
        setRecomendaciones(respuesta.data);
        setEstadoApp("resultados"); // <-- Cambiamos a 'resultados'
      } else {
        setRecomendaciones([]);
        setEstadoApp("sin_resultados"); // <-- Cambiamos a 'sin_resultados'
      }

    } catch (err) {
      console.error("Error al conectar con la API:", err);
      setError("No se pudo conectar con el servidor. ¿Está el backend corriendo?");
      setEstadoApp("error"); // <-- Estado de error
    }
  };

  /**
   * Resetea el estado para volver a la pantalla de búsqueda
   * (Requerimiento RF07)
   */
  const volverABuscar = () => {
    setEstadoApp("buscando");
    setRecomendaciones([]);
    setDescripcion(""); // Limpiamos la barra de búsqueda
    setError(null);
  };

  // --- RENDERIZADO CONDICIONAL ---

  // 1. Lo que se ve al buscar (Figura 14)
  const renderBuscando = () => (
    <>
      <p style={styles.subtitle}>
        Danos una descripción y nosotros te recomendaremos una película
      </p>
      <div style={styles.searchContainer}>
        <input 
          type="text" 
          placeholder="Escribe aquí..." 
          style={styles.searchInput}
          value={descripcion}
          onChange={(e) => setDescripcion(e.target.value)}
        />
        <button 
          style={styles.searchButton}
          onClick={handleBuscar}
        >
          {estadoApp === 'cargando' ? 'Buscando...' : 'Buscar'}
        </button>
      </div>
    </>
  );

  // 2. Lo que se ve con resultados (Figura 15)
  const renderResultados = () => (
    <>
      <div style={styles.gridResultados}>
        {recomendaciones.map((peli, index) => (
          <div key={index} style={styles.card}>
            <h3 style={styles.cardTitle}>{peli.titulo} ({peli.anio})</h3>
            <p style={styles.cardGenero}>{peli.genero}</p>
            <p style={styles.cardSinopsis}>{peli.sinopsis}</p>
          </div>
        ))}
      </div>
      <button style={styles.volverButton} onClick={volverABuscar}>
        Volver a intentar
      </button>
    </>
  );

  // 3. Lo que se ve sin resultados (Figura 17)
  const renderSinResultados = () => (
    <>
      <h2 style={styles.mensajeResultado}>
        Parece que no encontramos ninguna película que coincida, intenta con otra búsqueda :)
      </h2>
      <button style={styles.volverButton} onClick={volverABuscar}>
        Volver a intentar
      </button>
    </>
  );

  // 4. Lo que se ve si la API falla
  const renderError = () => (
     <>
      <h2 style={styles.mensajeResultado}>
        {error}
      </h2>
      <button style={styles.volverButton} onClick={volverABuscar}>
        Volver
      </button>
    </>
  );

  // --- Renderizado Principal de la App ---
  return (
    <div style={styles.appContainer}>
      <h1 style={styles.title}>MexCine</h1>
      
      {/* --- Contenido Dinámico --- */}
      <div style={styles.contentContainer}>
        {estadoApp === 'buscando' && renderBuscando()}
        {estadoApp === 'cargando' && renderBuscando()} 
        {estadoApp === 'resultados' && renderResultados()}
        {estadoApp === 'sin_resultados' && renderSinResultados()}
        {estadoApp === 'error' && renderError()}
      </div>
      
      <p style={styles.footerText}>
        "El cine mexicano al alcance de tu mano"
      </p>
    </div>
  );
}

// --- Estilos CSS en línea ---
// (He añadido estilos nuevos al final)
const styles = {
  // Contenedor principal
  appContainer: {
    width: '100%',
    maxWidth: '1200px', // Hacemos la app más ancha para los resultados
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    textAlign: 'center',
  },
  // Contenedor del contenido
  contentContainer: {
    width: '100%',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
  },
  searchContainer: {
    display: 'flex',
    width: '100%',
    maxWidth: '600px',
    margin: '2rem 0',
  },
  searchInput: {
    flex: 1,
    padding: '0.75rem 1rem',
    fontSize: '1rem',
    border: 'none',
    borderRadius: '8px 0 0 8px',
    outline: 'none',
  },
  searchButton: {
    padding: '0.75rem 1.5rem',
    fontSize: '1rem',
    backgroundColor: '#f0f0f0',
    color: '#121212',
    border: 'none',
    borderRadius: '0 8px 8px 0',
    cursor: 'pointer',
    fontWeight: 'bold',
  },
  title: {
    fontSize: '3rem',
    fontWeight: 'bold',
    margin: 0,
    color: '#E50914',
  },
  subtitle: {
    fontSize: '1.25rem',
    margin: '0.5rem 0',
  },
  footerText: {
    marginTop: '2rem',
    fontStyle: 'italic',
    color: '#aaa',
  },

  // --- NUEVOS ESTILOS PARA RESULTADOS ---
  
  // Mensaje de "Sin resultados" o "Error"
  mensajeResultado: {
    fontSize: '1.5rem',
    color: '#f0f0f0',
    margin: '3rem 0',
  },

  // Botón de "Volver"
  volverButton: {
    padding: '0.75rem 2rem',
    fontSize: '1rem',
    backgroundColor: '#E50914',
    color: 'white',
    border: 'none',
    borderRadius: '8px',
    cursor: 'pointer',
    fontWeight: 'bold',
    marginTop: '2rem',
  },

  // Grid para las tarjetas
  gridResultados: {
    display: 'grid',
    gridTemplateColumns: 'repeat(3, 1fr)', // 3 columnas
    gap: '1.5rem', // Espacio entre tarjetas
    width: '100%',
    marginTop: '3rem',
  },

  // Tarjeta de película
  card: {
    backgroundColor: '#222',
    padding: '1.5rem',
    borderRadius: '8px',
    textAlign: 'left',
    boxShadow: '0 4px 8px rgba(0,0,0,0.3)',
  },
  cardTitle: {
    fontSize: '1.5rem',
    margin: '0 0 0.5rem 0',
    color: '#E50914',
  },
  cardGenero: {
    fontSize: '0.9rem',
    fontStyle: 'italic',
    color: '#aaa',
    margin: '0 0 1rem 0',
    borderBottom: '1px solid #444',
    paddingBottom: '0.5rem',
  },
  cardSinopsis: {
    fontSize: '1rem',
    color: '#ddd',
    margin: 0,
    lineHeight: '1.5',
  }
};

export default App;