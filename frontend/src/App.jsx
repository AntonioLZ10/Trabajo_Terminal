import React, { useState } from 'react';
import axios from 'axios';

/**
 * -----------------------------------------------------------------------------
 * MÓDULO DE INTERFAZ DE USUARIO (CLIENTE WEB)
 * TRABAJO TERMINAL - SISTEMA "MEXCINE"
 * -----------------------------------------------------------------------------
 * Descripción:
 * Componente principal de la Single Page Application (SPA).
 * Implementa la lógica de interacción con el usuario, consumo de la API REST
 * y renderizado dinámico basado en estados finitos.
 *
 * Tecnologías: React.js, Axios (Cliente HTTP).
 * Autores: [Nombre de tu equipo]
 * Versión: 1.0.0
 * -----------------------------------------------------------------------------
 */

function App() {
  // ---------------------------------------------------------------------------
  // GESTIÓN DEL ESTADO DE LA APLICACIÓN
  // ---------------------------------------------------------------------------
  
  // Almacena el input del usuario (Two-way data binding)
  const [descripcion, setDescripcion] = useState("");
  
  // Almacena la respuesta del modelo de ML (Lista de objetos película)
  const [recomendaciones, setRecomendaciones] = useState([]);
  
  // Control de flujo mediante Máquina de Estados Finitos (FSM)
  // Estados posibles: 'buscando' | 'cargando' | 'resultados' | 'sin_resultados' | 'error'
  // Decisión de diseño: Usar un string de estado en lugar de múltiples booleanos 
  // (isLoading, isError, etc.) simplifica la lógica de renderizado y evita estados inconsistentes.
  const [estadoApp, setEstadoApp] = useState("buscando"); 
  
  // Gestión de errores para feedback al usuario
  const [error, setError] = useState(null);

  // ---------------------------------------------------------------------------
  // LÓGICA DE PAGINACIÓN (CLIENT-SIDE)
  // ---------------------------------------------------------------------------
  // Controlamos cuántos elementos se renderizan inicialmente para no saturar el DOM.
  // Estrategia: "Lazy Loading" o carga bajo demanda manual.
  const [cantidadVisible, setCantidadVisible] = useState(3);

  // Punto de acceso al Microservicio de Recomendación
  // Nota: En producción, esto se debe inyectar vía variables de entorno (process.env).
  const API_URL = "http://127.0.0.1:8000/recomendar";


  // ---------------------------------------------------------------------------
  // CONTROLADORES DE EVENTOS Y LÓGICA DE NEGOCIO
  // ---------------------------------------------------------------------------

  const handleBuscar = async () => {
    // Validación de entrada vacía para evitar peticiones innecesarias
    if (descripcion.trim() === "") return;
    
    // Reset de estados previos
    setError(null);
    setEstadoApp("cargando"); // Transición a estado de espera (UX)
    setCantidadVisible(3);    // Reinicio del paginador

    try {
      // Petición asíncrona al Backend
      const respuesta = await axios.post(API_URL, { descripcion: descripcion });
      
      // Evaluación de la respuesta
      if (respuesta.data && respuesta.data.length > 0) {
        setRecomendaciones(respuesta.data);
        setEstadoApp("resultados"); // Transición a éxito
      } else {
        setRecomendaciones([]);
        setEstadoApp("sin_resultados"); // Transición a fallo lógico (sin coincidencias)
      }
    } catch (err) {
      // Manejo de excepciones de red o servidor (500, 404, Network Error)
      console.error("Error en la capa de transporte:", err);
      setError("No se pudo establecer conexión con el motor de recomendación.");
      setEstadoApp("error"); // Transición a estado de error crítico
    }
  };

  // Accesibilidad: Permite buscar presionando ENTER
  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      handleBuscar();
    }
  };

  // Reseteo completo del ciclo de interacción
  const volverABuscar = () => {
    setEstadoApp("buscando");
    setRecomendaciones([]);
    setDescripcion("");
    setError(null);
    setCantidadVisible(3);
  };

  /**
   * Manejador de paginación.
   * Incrementa el límite de slicing del array de resultados.
   */
  const mostrarMas = () => {
    setCantidadVisible(prev => prev + 3);
    
    // Mejora de UX: Desplazamiento suave hacia arriba para mantener el contexto visual
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // ---------------------------------------------------------------------------
  // SUB-COMPONENTES DE RENDERIZADO (VISTAS)
  // ---------------------------------------------------------------------------
  // Separamos la lógica de presentación para mantener el return principal limpio (Clean Code).

  const renderBuscando = () => (
    <>
      <div style={styles.searchWrapper}>
        <input 
          type="text" 
          placeholder="Ej: Películas de terror sobre brujería." 
          style={styles.searchInput}
          value={descripcion}
          onChange={(e) => setDescripcion(e.target.value)}
          onKeyDown={handleKeyDown}
          aria-label="Descripción de la película buscada"
        />
        <button 
          style={styles.searchButton} 
          onClick={handleBuscar}
          aria-label="Buscar recomendaciones"
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="11" cy="11" r="8"></circle>
            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
          </svg>
        </button>
      </div>
    </>
  );

  const renderResultados = () => {
    // Algoritmo de Paginación:
    // Extraemos solo el subconjunto de películas que el usuario ha solicitado ver.
    // slice(cantidadVisible - 3, cantidadVisible) muestra de 3 en 3, ocultando las anteriores.
    // Si quisiéramos lista acumulativa, usaríamos slice(0, cantidadVisible).
    const peliculasVisibles = recomendaciones.slice(cantidadVisible - 3, cantidadVisible);
    
    const hayMasOpciones = cantidadVisible < recomendaciones.length;

    return (
      <>
        <div style={styles.gridResultados}>
          {peliculasVisibles.map((peli, index) => (
            <div key={index} style={styles.card}>
              <h3 style={styles.cardTitle}>{peli.titulo}</h3>
              <p style={styles.cardInfo}>
                {peli.anio ? peli.anio : 'N/D'} • {peli.genero}
              </p>
              <p style={styles.cardSinopsis}>{peli.sinopsis}</p>
            </div>
          ))}
        </div>
        
        <div style={styles.buttonsContainer}>
          {hayMasOpciones && (
            <button style={styles.darkButton} onClick={mostrarMas}>
              ¡Quiero más opciones!
            </button>
          )}
          
          <button style={styles.lightButton} onClick={volverABuscar}>
            Volver a intentar
          </button>
        </div>
      </>
    );
  };

  const renderSinResultados = () => (
    <>
      <h2 style={styles.mensajeGrande}>
        El modelo no encontró similitudes suficientes. Intenta ser más específico.
      </h2>
      <button style={styles.lightButton} onClick={volverABuscar}>
        Nueva búsqueda
      </button>
    </>
  );

  // ---------------------------------------------------------------------------
  // RENDERIZADO PRINCIPAL (DOM)
  // ---------------------------------------------------------------------------
  return (
    <div style={styles.appContainer}>
      <h1 style={styles.title}>MexCine</h1>
      
      {estadoApp === 'buscando' && (
        <p style={styles.subtitle}>
          Danos una descripción y la IA te recomendará cine mexicano.
        </p>
      )}

      {/* Renderizado Condicional basado en el Estado de la Aplicación */}
      <div style={styles.contentContainer}>
        {(estadoApp === 'buscando' || estadoApp === 'cargando') && renderBuscando()}
        
        {estadoApp === 'cargando' && <p style={{color: 'white', marginTop: '20px'}}>Analizando sinopsis...</p>}
        
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

// -----------------------------------------------------------------------------
// HOJA DE ESTILOS (CSS-IN-JS)
// -----------------------------------------------------------------------------
// Para este prototipo, utilizamos objetos de estilo en línea para mantener
// la portabilidad del componente sin dependencias externas de CSS.
const styles = {
  appContainer: {
    width: '100%',
    maxWidth: '1200px',
    textAlign: 'center',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    // margin: '0 auto', // Centrado horizontal en pantallas grandes
  },
  title: {
    fontSize: '4rem', 
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
  searchWrapper: {
    display: 'flex',
    alignItems: 'center',
    backgroundColor: 'white',
    borderRadius: '50px', 
    padding: '5px 5px 5px 25px', 
    width: '100%',
    maxWidth: '700px', 
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
    backgroundColor: '#444', 
    color: 'white',
    border: 'none',
    borderRadius: '50%', 
    width: '50px',
    height: '50px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    cursor: 'pointer',
    marginLeft: '10px',
    transition: 'background 0.3s',
  },
  gridResultados: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', 
    gap: '20px',
    width: '100%',
    marginBottom: '3rem',
  },
  card: {
    backgroundColor: 'white',
    color: 'black', 
    padding: '2rem',
    borderRadius: '30px', 
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