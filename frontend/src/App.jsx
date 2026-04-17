import React, { useState, useEffect } from 'react'
import Filters from './components/Filters'
import PotencyChart from './components/PotencyChart'
import './index.css'

export default function App() {
  const [filtros, setFiltros] = useState({
    sectorMacro: '*',
    sector: '*',
    denominacion: '*',
    nic: null,
  })

  const [selectedNic, setSelectedNic] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (filtros.nic) {
      setSelectedNic(filtros.nic)
    }
  }, [filtros.nic])

  return (
    <div className="container-app">
      <header className="header">
        <div className="header-left">
          <img 
            src="/logoZuccardi.png" 
            alt="Familia Zuccardi" 
            className="logo-img"
            onError={(e) => {
              e.target.style.display = 'none'
            }}
          />
          <div>
            <h1 className="header-title">Visualizador de Potencia</h1>
            <p style={{fontSize: '0.875rem', opacity: 0.9}}>Familia Zuccardi</p>
          </div>
        </div>
      </header>

      <main className="main-content">
        <Filters 
          filtros={filtros} 
          setFiltros={setFiltros}
          onLoading={setLoading}
          onError={setError}
        />

        {error && (
          <div className="error">
            {error}
          </div>
        )}

        {selectedNic ? (
          <PotencyChart 
            nic={selectedNic}
            nombreReferencia={filtros.nic}
            loading={loading}
            onLoading={setLoading}
          />
        ) : (
          <div className="grafico-container">
            <div className="loading">
              Selecciona un NIC para ver el gráfico de potencia
            </div>
          </div>
        )}
      </main>

      <footer className="footer">
        <p>© 2026 Familia Zuccardi - Sistema de Gestión de Potencia Eléctrica</p>
      </footer>
    </div>
  )
}
