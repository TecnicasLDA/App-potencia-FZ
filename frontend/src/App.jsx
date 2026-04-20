import React, { useState, useEffect } from 'react'
import Filters from './components/Filters'
import PotencyChart from './components/PotencyChart'
import MaestroNics from './components/MaestroNics'
import './index.css'

export default function App() {
  const [filtros, setFiltros] = useState({
    sectorMacro: '*',
    sector: '*',
    denominacion: '*',
    nic: null,
    fechaInicio: '',
    fechaFin: '',
  })

  const [selectedNic, setSelectedNic] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [activeView, setActiveView] = useState('visualizador')

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
          <div className="header-copy">
            <h1 className="header-title">Visualizador de Potencia</h1>
            <p className="header-subtitle">Familia Zuccardi</p>
          </div>
        </div>
        <div className="header-badge">Monitoreo Activo</div>
      </header>

      <main className="main-content">
        <div className="view-switcher">
          <button
            className={`view-btn ${activeView === 'visualizador' ? 'active' : ''}`}
            onClick={() => setActiveView('visualizador')}
          >
            Visualizador
          </button>
          <button
            className={`view-btn ${activeView === 'maestro' ? 'active' : ''}`}
            onClick={() => setActiveView('maestro')}
          >
            Maestro de NICs
          </button>
        </div>

        {activeView === 'visualizador' ? (
          <>
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
                fechaInicio={filtros.fechaInicio}
                fechaFin={filtros.fechaFin}
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
          </>
        ) : (
          <MaestroNics />
        )}
      </main>

      <footer className="footer">
        <p>© 2026 Familia Zuccardi - Sistema de Gestión de Potencia Eléctrica</p>
      </footer>
    </div>
  )
}
