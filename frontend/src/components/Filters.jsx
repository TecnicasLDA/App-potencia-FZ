import React, { useState, useEffect } from 'react'
import apiClient from '../apiClient'

export default function Filters({ filtros, setFiltros, onLoading, onError }) {
  const [opciones, setOpciones] = useState({
    sectoresMacro: [],
    sectores: [],
    denominaciones: [],
    nics: [],
  })

  const [cargando, setCargando] = useState(false)

  // Cargar filtros disponibles inicialmente
  useEffect(() => {
    cargarFiltrosDisponibles()
  }, [])

  // Cargar filtros cascada cuando cambien sector_macro, sector o denominacion
  useEffect(() => {
    if (
      filtros.sectorMacro !== '*' ||
      filtros.sector !== '*' ||
      filtros.denominacion !== '*'
    ) {
      cargarFiltrosCascada()
    }
  }, [filtros.sectorMacro, filtros.sector, filtros.denominacion])

  const cargarFiltrosDisponibles = async () => {
    try {
      setCargando(true)
      const response = await apiClient.get('/filtros')
      setOpciones({
        sectoresMacro: response.data.sectores_macro || [],
        sectores: response.data.sectores || [],
        denominaciones: response.data.denominaciones || [],
        nics: response.data.nics || [],
      })
      onError(null)
    } catch (err) {
      console.error('Error cargando filtros:', err)
      onError('No se pudieron cargar los filtros. Verifica la conexión con el servidor.')
    } finally {
      setCargando(false)
    }
  }

  const cargarFiltrosCascada = async () => {
    try {
      setCargando(true)
      const params = new URLSearchParams()
      
      if (filtros.sectorMacro && filtros.sectorMacro !== '*') {
        params.append('sector_macro', filtros.sectorMacro)
      }
      if (filtros.sector && filtros.sector !== '*') {
        params.append('sector', filtros.sector)
      }
      if (filtros.denominacion && filtros.denominacion !== '*') {
        params.append('denominacion', filtros.denominacion)
      }

      const response = await apiClient.get(`/filtros/cascada?${params}`)
      setOpciones(prev => ({
        ...prev,
        sectores: response.data.sectores || prev.sectores,
        denominaciones: response.data.denominaciones || prev.denominaciones,
        nics: response.data.nics || prev.nics,
      }))
      onError(null)
    } catch (err) {
      console.error('Error cargando cascada:', err)
      onError('Error al cargar filtros cascada.')
    } finally {
      setCargando(false)
    }
  }

  const handleSectorMacroChange = (e) => {
    const valor = e.target.value
    setFiltros(prev => ({
      ...prev,
      sectorMacro: valor,
      sector: '*',
      denominacion: '*',
      nic: null,
    }))
  }

  const handleSectorChange = (e) => {
    const valor = e.target.value
    setFiltros(prev => ({
      ...prev,
      sector: valor,
      denominacion: '*',
      nic: null,
    }))
  }

  const handleDenominacionChange = (e) => {
    const valor = e.target.value
    setFiltros(prev => ({
      ...prev,
      denominacion: valor,
      nic: null,
    }))
  }

  const handleNicChange = (e) => {
    const valor = e.target.value
    setFiltros(prev => ({
      ...prev,
      nic: valor,
    }))
  }

  const handleFechaInicioChange = (e) => {
    const valor = e.target.value
    setFiltros(prev => ({
      ...prev,
      fechaInicio: valor,
    }))
  }

  const handleFechaFinChange = (e) => {
    const valor = e.target.value
    setFiltros(prev => ({
      ...prev,
      fechaFin: valor,
    }))
  }

  return (
    <div className="filtros-panel">
      <h2 className="panel-title">Filtros</h2>

      <div className="filtro-row">
        <div className="filtro-group">
          <label className="filtro-label">Sector Macro</label>
          <select 
            className="filtro-select"
            value={filtros.sectorMacro}
            onChange={handleSectorMacroChange}
            disabled={cargando}
          >
            {opciones.sectoresMacro.map(opt => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        <div className="filtro-group">
          <label className="filtro-label">Sector</label>
          <select 
            className="filtro-select"
            value={filtros.sector}
            onChange={handleSectorChange}
            disabled={cargando}
          >
            <option value="*">Todos</option>
            {opciones.sectores.map(opt => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        <div className="filtro-group">
          <label className="filtro-label">Denominación</label>
          <select 
            className="filtro-select"
            value={filtros.denominacion}
            onChange={handleDenominacionChange}
            disabled={cargando}
          >
            <option value="*">Todos</option>
            {opciones.denominaciones.map(opt => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        <div className="filtro-group">
          <label className="filtro-label">NIC</label>
          <select 
            className="filtro-select"
            value={filtros.nic || ''}
            onChange={handleNicChange}
            disabled={cargando}
          >
            <option value="">-- Selecciona un NIC --</option>
            {opciones.nics.map(opt => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="filtro-row filtro-row-secondary">
        <div className="filtro-group">
          <label className="filtro-label">Fecha desde</label>
          <input
            type="date"
            className="filtro-select"
            value={filtros.fechaInicio || ''}
            onChange={handleFechaInicioChange}
            disabled={cargando}
          />
        </div>

        <div className="filtro-group">
          <label className="filtro-label">Fecha hasta</label>
          <input
            type="date"
            className="filtro-select"
            value={filtros.fechaFin || ''}
            onChange={handleFechaFinChange}
            disabled={cargando}
          />
        </div>
      </div>

      {cargando && (
        <p className="filtro-loading-text">
          Cargando opciones...
        </p>
      )}
    </div>
  )
}
