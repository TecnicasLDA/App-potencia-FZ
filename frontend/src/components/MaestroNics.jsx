import React, { useEffect, useMemo, useState } from 'react'
import apiClient from '../apiClient'

const PAGE_SIZE = 100

const COLUMNS = [
  { key: 'nic', label: 'NIC', editable: false },
  { key: 'referencia', label: 'Referencia', editable: true },
  { key: 'tipo', label: 'Tipo', editable: true },
  { key: 'tarifa', label: 'Tarifa', editable: true },
  { key: 'sector_macro', label: 'Sector Macro', editable: true },
  { key: 'sector', label: 'Sector', editable: true },
  { key: 'denominacion', label: 'Denominacion', editable: true },
  { key: 'combinacion', label: 'Combinacion', editable: true },
]

export default function MaestroNics() {
  const [rows, setRows] = useState([])
  const [total, setTotal] = useState(0)
  const [searchInput, setSearchInput] = useState('')
  const [search, setSearch] = useState('')
  const [offset, setOffset] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [savingNic, setSavingNic] = useState(null)

  const currentPage = Math.floor(offset / PAGE_SIZE) + 1
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE))

  const canPrev = offset > 0
  const canNext = offset + PAGE_SIZE < total

  const loadRows = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await apiClient.get('/maestro-nics', {
        params: {
          search: search || undefined,
          limit: PAGE_SIZE,
          offset,
        },
      })
      setRows(response.data.items || [])
      setTotal(response.data.total || 0)
    } catch (err) {
      console.error('Error cargando maestro NICs:', err)
      setError('No se pudo cargar el Maestro de NICs.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadRows()
  }, [search, offset])

  const handleSearchSubmit = (e) => {
    e.preventDefault()
    setOffset(0)
    setSearch(searchInput.trim())
  }

  const handleFieldChange = (nic, field, value) => {
    setRows(prev => prev.map(row => (
      row.nic === nic ? { ...row, [field]: value } : row
    )))
  }

  const handleSave = async (row) => {
    try {
      setSavingNic(row.nic)
      setError(null)
      const payload = {
        referencia: row.referencia || null,
        tipo: row.tipo || null,
        tarifa: row.tarifa || null,
        sector_macro: row.sector_macro || null,
        sector: row.sector || null,
        denominacion: row.denominacion || null,
        combinacion: row.combinacion || null,
      }
      await apiClient.put(`/maestro-nics/${row.nic}`, payload)
    } catch (err) {
      console.error('Error guardando NIC:', err)
      setError(`No se pudo guardar NIC ${row.nic}.`)
    } finally {
      setSavingNic(null)
    }
  }

  const emptyText = useMemo(() => {
    if (loading) return 'Cargando Maestro de NICs...'
    if (search) return 'Sin resultados para esa busqueda.'
    return 'No hay datos para mostrar.'
  }, [loading, search])

  return (
    <div className="maestro-panel">
      <div className="maestro-header">
        <div>
          <h2 className="panel-title">Maestro de NICs</h2>
          <p className="maestro-subtitle">Gestion centralizada de referencia, tarifa y segmentaciones.</p>
        </div>

        <form onSubmit={handleSearchSubmit} className="maestro-search-form">
          <input
            className="filtro-select"
            type="text"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Buscar por NIC, referencia, sector..."
          />
          <button type="submit" className="maestro-btn">Buscar</button>
        </form>
      </div>

      {error && <div className="error">{error}</div>}

      <div className="maestro-table-wrapper">
        <table className="maestro-table">
          <thead>
            <tr>
              {COLUMNS.map(col => (
                <th key={col.key}>{col.label}</th>
              ))}
              <th>Accion</th>
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 ? (
              <tr>
                <td colSpan={COLUMNS.length + 1} className="maestro-empty">
                  {emptyText}
                </td>
              </tr>
            ) : rows.map(row => (
              <tr key={row.nic}>
                {COLUMNS.map(col => (
                  <td key={`${row.nic}-${col.key}`}>
                    {col.editable ? (
                      <input
                        type="text"
                        className="maestro-cell-input"
                        value={row[col.key] || ''}
                        onChange={(e) => handleFieldChange(row.nic, col.key, e.target.value)}
                      />
                    ) : (
                      <span className="maestro-nic">{row[col.key]}</span>
                    )}
                  </td>
                ))}
                <td>
                  <button
                    className="maestro-btn"
                    disabled={savingNic === row.nic}
                    onClick={() => handleSave(row)}
                  >
                    {savingNic === row.nic ? 'Guardando...' : 'Guardar'}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="maestro-pagination">
        <button className="maestro-btn" disabled={!canPrev} onClick={() => setOffset(prev => Math.max(0, prev - PAGE_SIZE))}>
          Anterior
        </button>
        <span>Pagina {currentPage} de {totalPages} ({total} NICs)</span>
        <button className="maestro-btn" disabled={!canNext} onClick={() => setOffset(prev => prev + PAGE_SIZE)}>
          Siguiente
        </button>
      </div>
    </div>
  )
}
