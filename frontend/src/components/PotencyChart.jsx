import React, { useState, useEffect } from 'react'
import apiClient from '../apiClient'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'

export default function PotencyChart({ nic, nombreReferencia, loading, onLoading }) {
  const [datos, setDatos] = useState([])
  const [cargando, setCargando] = useState(false)
  const [error, setError] = useState(null)
  const [infoGrafico, setInfoGrafico] = useState({
    referencia: '',
    combinacion: '',
  })

  useEffect(() => {
    if (nic) {
      cargarDatosGrafico(nic)
    }
  }, [nic])

  const cargarDatosGrafico = async (nicValue) => {
    try {
      setCargando(true)
      onLoading(true)
      setError(null)

      const response = await apiClient.get(`/grafico/${nicValue}`)
      
      setDatos(response.data.data || [])
      setInfoGrafico({
        referencia: response.data.referencia,
        combinacion: response.data.combinacion,
      })

      if (!response.data.data || response.data.data.length === 0) {
        setError('No hay datos disponibles para este NIC en el período seleccionado.')
      }
    } catch (err) {
      console.error('Error cargando gráfico:', err)
      setError('Error al cargar los datos del gráfico. Por favor, intenta nuevamente.')
    } finally {
      setCargando(false)
      onLoading(false)
    }
  }

  const formatoTooltip = (value) => {
    return value !== null && value !== undefined ? `${value.toFixed(2)} kW` : 'N/A'
  }

  return (
    <div className="grafico-container">
      <h2 className="grafico-titulo">
        Análisis de Potencia
      </h2>
      
      <p className="grafico-subtitulo">
        {infoGrafico.combinacion || `NIC ${nic}`}
      </p>

      {error && (
        <div className="error">
          {error}
        </div>
      )}

      {cargando ? (
        <div className="loading">
          Cargando datos del gráfico...
        </div>
      ) : datos && datos.length > 0 ? (
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={datos} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
            <XAxis 
              dataKey="mes_label"
              stroke="#888"
              style={{fontSize: '0.875rem'}}
            />
            <YAxis 
              label={{ value: 'Potencia (kW)', angle: -90, position: 'insideLeft' }}
              stroke="#888"
              style={{fontSize: '0.875rem'}}
            />
            <Tooltip 
              formatter={formatoTooltip}
              contentStyle={{
                backgroundColor: '#fafafa',
                border: '1px solid #ddd',
                borderRadius: '4px',
                padding: '8px',
              }}
            />
            <Legend 
              wrapperStyle={{paddingTop: '20px'}}
              formatter={(value) => {
                if (value === 'pot_contratada') return 'Potencia Contratada'
                if (value === 'pot_demandada_max') return 'Potencia Demandada (Máx.)'
                return value
              }}
            />
            <Line
              type="monotone"
              dataKey="pot_contratada"
              stroke="#8B0000"
              strokeWidth={2.5}
              dot={{fill: '#8B0000', r: 4}}
              activeDot={{r: 6}}
              name="Potencia Contratada"
              connectNulls={true}
            />
            <Line
              type="monotone"
              dataKey="pot_demandada_max"
              stroke="#D4AF37"
              strokeWidth={2.5}
              dot={{fill: '#D4AF37', r: 4}}
              activeDot={{r: 6}}
              name="Potencia Demandada (Máx.)"
              connectNulls={true}
            />
          </LineChart>
        </ResponsiveContainer>
      ) : (
        <div className="loading">
          No hay datos disponibles para este NIC.
        </div>
      )}

      <div style={{marginTop: '2rem', paddingTop: '1rem', borderTop: '1px solid #eee', fontSize: '0.875rem', color: '#666'}}>
        <p><strong>Nota:</strong> La Potencia Contratada se muestra de forma continua mensual (carry-forward trimestral). La Potencia Demandada representa el máximo consumo registrado en el período.</p>
      </div>
    </div>
  )
}
