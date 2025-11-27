import React, { useState } from 'react';
import axios from 'axios';

function App() {
  const [descripcion, setDescripcion] = useState("");
  const [recomendaciones, setRecomendaciones] = useState([]);
  const [estadoApp, setEstadoApp] = useState("buscando"); 
  const [error, setError] = useState(null);

  const API_URL = "http://127.0.0.1:8000/recomendar";

  // --- LÓGICA DE BÚSQUEDA ---
  const handleBuscar = async () => {
    if (descripcion.trim() === "") return;
    setError(null);
    setEstadoApp("cargando");

    try {
      const respuesta = await axios.post(API_URL, { descripcion: descripcion });
      if (respuesta.data && respuesta.data.length > 0) {
        setRecomendaciones(respuesta.data);
        setEstadoApp("resultados");
      } else {
        setRecomendaciones([]);
        setEstadoApp("sin_resultados");
      }
    } catch (err) {
      console.error(err);
      setError("Error de conexión con el servidor.");
      setEstadoApp("error");
    }
  };

  // --- NUEVO: Detectar tecla ENTER ---
  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      handleBuscar();
    }
  };

  const volverABuscar = () => {
    setEstadoApp("buscando");
    setRecomendaciones([]);
    setDescripcion("");
    setError(null);
  };

  // --- VISTAS ---

  // 1. Buscador (Con diseño de pastilla e icono)
  const renderBuscando = () => (
    <>
      <div style={styles.searchWrapper}>
        <input 
          type="text" 
          placeholder="Películas de terror sobre brujería." 
          style={styles.searchInput}
          value={descripcion}
          onChange={(e) => setDescripcion(e.target.value)}
          onKeyDown={handleKeyDown} // <-- Aquí está la magia del Enter
        />
        <button style={styles.searchButton} onClick={handleBuscar}>
          {/* Icono de Lupa SVG */}
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="11" cy="11" r="8"></circle>
            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
          </svg>
        </button>
      </div>
    </>
  );

  // 2. Resultados (Tarjetas blancas)
  const renderResultados = () => (
    <>
      <div style={styles.gridResultados}>
        {recomendaciones.map((peli, index) => (
          <div key={index} style={styles.card}>
            <h3 style={styles.cardTitle}>{peli.titulo}</h3>
            {/* Si tuvieramos año lo ponemos, si no, lo quitamos */}
            <p style={styles.cardInfo}>{peli.anio ? peli.anio : ''} • {peli.genero}</p>
            <p style={styles.cardSinopsis}>{peli.sinopsis}</p>
          </div>
        ))}
      </div>
      
      <div style={styles.buttonsContainer}>
        {/* Botón oscuro "Quiero más opciones" (Simulado por ahora) */}
        <button style={styles.darkButton} onClick={() => alert("¡Próximamente en el Sprint 5!")}>
          ¡Quiero más opciones!
        </button>
        
        {/* Botón claro "Volver a intentar" */}
        <button style={styles.lightButton} onClick={volverABuscar}>
          Volver a intentar
        </button>
      </div>
    </>
  );

  const renderSinResultados = () => (
    <>
      <h2 style={styles.mensajeGrande}>
        Parece que no encontramos ninguna película que coincida, intenta con otra búsqueda :)
      </h2>
      <button style={styles.lightButton} onClick={volverABuscar}>
        Volver a intentar
      </button>
    </>
  );

  return (
    <div style={styles.appContainer}>
      {/* El título siempre visible */}
      <h1 style={styles.title}>MexCine</h1>
      
      {/* Subtítulo solo si estamos buscando */}
      {estadoApp === 'buscando' && (
        <p style={styles.subtitle}>
          Danos una descripción y nosotros te recomendaremos una película
        </p>
      )}

      {/* Contenido Dinámico */}
      <div style={styles.contentContainer}>
        {(estadoApp === 'buscando' || estadoApp === 'cargando') && renderBuscando()}
        {estadoApp === 'resultados' && renderResultados()}
        {estadoApp === 'sin_resultados' && renderSinResultados()}
        {estadoApp === 'error' && <h2 style={styles.mensajeGrande}>{error}</h2>}
      </div>

      <p style={styles.footerText}>
        “El cine mexicano al alcance de tu mano”
      </p>
    </div>
  );
}

// --- ESTILOS RESPONSIVE (Estilo Figma) ---
const styles = {
  appContainer: {
    width: '100%',
    maxWidth: '1200px',
    textAlign: 'center',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
  },
  title: {
    fontSize: '4rem', // Grande como en el diseño
    fontWeight: 'bold',
    margin: '0 0 10px 0',
    color: 'white', 
    textShadow: '0 2px 10px rgba(0,0,0,0.5)',
  },
  subtitle: {
    fontSize: '1.5rem',
    fontWeight: '500',
    marginBottom: '2rem',
    textShadow: '0 2px 4px rgba(0,0,0,0.5)',
  },
  
  // --- BUSCADOR TIPO PASTILLA ---
  searchWrapper: {
    display: 'flex',
    alignItems: 'center',
    backgroundColor: 'white',
    borderRadius: '50px', // Borde totalmente redondo
    padding: '5px 5px 5px 25px', // Padding interno
    width: '100%',
    maxWidth: '700px', // Ancho máximo del buscador
    boxShadow: '0 4px 20px rgba(0,0,0,0.3)',
  },
  searchInput: {
    flex: 1,
    border: 'none',
    outline: 'none',
    fontSize: '1.2rem',
    color: '#333',
  },
  searchButton: {
    backgroundColor: '#444', // Gris oscuro para el botón de lupa
    color: 'white',
    border: 'none',
    borderRadius: '50%', // Círculo perfecto
    width: '50px',
    height: '50px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    cursor: 'pointer',
    marginLeft: '10px',
    transition: 'background 0.3s',
  },

  // --- TARJETAS TIPO FIGMA ---
  gridResultados: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', // Responsive automático
    gap: '20px',
    width: '100%',
    marginBottom: '3rem',
  },
  card: {
    backgroundColor: 'white',
    color: 'black', // Texto negro sobre fondo blanco
    padding: '2rem',
    borderRadius: '30px', // Bordes muy redondeados
    textAlign: 'left',
    boxShadow: '0 10px 25px rgba(0,0,0,0.2)',
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'flex-start',
  },
  cardTitle: {
    fontSize: '1.8rem',
    fontWeight: 'bold',
    margin: '0 0 10px 0',
  },
  cardInfo: {
    fontSize: '0.9rem',
    color: '#666',
    fontWeight: 'bold',
    textTransform: 'uppercase',
    marginBottom: '1rem',
  },
  cardSinopsis: {
    fontSize: '1rem',
    lineHeight: '1.6',
    color: '#333',
  },

  // --- BOTONES INFERIORES ---
  buttonsContainer: {
    display: 'flex',
    gap: '20px',
    flexWrap: 'wrap',
    justifyContent: 'center',
  },
  darkButton: {
    backgroundColor: '#444',
    color: 'white',
    border: 'none',
    padding: '15px 30px',
    fontSize: '1rem',
    fontWeight: 'bold',
    borderRadius: '50px',
    cursor: 'pointer',
  },
  lightButton: {
    backgroundColor: '#ddd',
    color: 'black',
    border: 'none',
    padding: '15px 30px',
    fontSize: '1rem',
    fontWeight: 'bold',
    borderRadius: '50px',
    cursor: 'pointer',
  },

  // --- MENSAJES ---
  mensajeGrande: {
    fontSize: '2.5rem',
    fontWeight: 'bold',
    lineHeight: '1.2',
    maxWidth: '800px',
    marginBottom: '2rem',
    textShadow: '0 2px 10px rgba(0,0,0,0.5)',
  },
  footerText: {
    marginTop: '4rem',
    fontSize: '1rem',
    fontStyle: 'italic',
    opacity: 0.8,
  },
  contentContainer: {
    width: '100%',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
  }
};

export default App;