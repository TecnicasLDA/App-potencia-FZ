import React, { useState, useEffect } from 'react'
import apiClient from '../apiClient'
import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'

export default function PotencyChart({ nic, nombreReferencia, fechaInicio, fechaFin, loading, onLoading }) {
  const [datos, setDatos] = useState([])
  const [cargando, setCargando] = useState(false)
  const [error, setError] = useState(null)
  const [infoGrafico, setInfoGrafico] = useState({
    referencia: '',
    combinacion: '',
  })

  useEffect(() => {
    if (nic) {
      cargarDatosGrafico(nic, fechaInicio, fechaFin)
    }
  }, [nic, fechaInicio, fechaFin])

  const cargarDatosGrafico = async (nicValue, fechaInicioValue, fechaFinValue) => {
    try {
      setCargando(true)
      onLoading(true)
      setError(null)

      if (fechaInicioValue && fechaFinValue && fechaInicioValue > fechaFinValue) {
        setError('La fecha desde no puede ser mayor a la fecha hasta.')
        setDatos([])
        return
      }

      const params = {}
      if (fechaInicioValue) {
        params.fecha_inicio = fechaInicioValue
      }
      if (fechaFinValue) {
        params.fecha_fin = fechaFinValue
      }

      const response = await apiClient.get(`/grafico/${nicValue}`, { params })
      
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
          <ComposedChart data={datos} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(173, 198, 255, 0.2)" />
            <XAxis 
              dataKey="mes_label"
              stroke="#9aa8ba"
              style={{fontSize: '0.875rem'}}
            />
            <YAxis 
              label={{ value: 'Potencia (kW)', angle: -90, position: 'insideLeft' }}
              stroke="#9aa8ba"
              style={{fontSize: '0.875rem'}}
            />
            <Tooltip 
              formatter={formatoTooltip}
              contentStyle={{
                backgroundColor: 'rgba(20, 27, 36, 0.96)',
                border: '1px solid rgba(173, 198, 255, 0.26)',
                borderRadius: '10px',
                padding: '10px',
                color: '#e8ecf2',
              }}
              labelStyle={{ color: '#a5b2c3' }}
            />
            <Legend 
              wrapperStyle={{paddingTop: '20px'}}
              formatter={(value) => {
                if (value === 'pot_contratada') return 'Potencia Contratada'
                if (value === 'pot_demandada_max') return 'Potencia Demandada (Máx.)'
                return value
              }}
            />

            <Bar
              dataKey="pot_demandada_max"
              name="Potencia Demandada (Máx.)"
              fill="#ffb961"
              fillOpacity={0.82}
              stroke="#ffcf95"
              strokeWidth={1}
              radius={[4, 4, 0, 0]}
              maxBarSize={18}
            />

            <Line
              type="monotone"
              dataKey="pot_contratada"
              stroke="#adc6ff"
              strokeWidth={3}
              dot={false}
              activeDot={false}
              name="Potencia Contratada"
              connectNulls={true}
            />
          </ComposedChart>
        </ResponsiveContainer>
      ) : (
        <div className="loading">
          No hay datos disponibles para este NIC.
        </div>
      )}

      <div className="grafico-nota">
        <p><strong>Nota:</strong> La Potencia Contratada se muestra de forma continua mensual (carry-forward trimestral). La Potencia Demandada representa el máximo consumo registrado en el período.</p>
      </div>
    </div>
  )
}
