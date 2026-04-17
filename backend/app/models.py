from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Index
from sqlalchemy.sql import func
from .database import Base

class Medicion(Base):
    """Modelo para mediciones de potencia agregadas mensualmente."""
    __tablename__ = "mediciones"

    id = Column(Integer, primary_key=True, index=True)
    nic = Column(Integer, index=True, nullable=False)
    cliente = Column(String(255), nullable=True)
    domicilio = Column(String(512), nullable=True)
    localidad = Column(String(255), nullable=True)
    departamento = Column(String(255), nullable=True)
    codigo_postal = Column(String(20), nullable=True)
    
    # Fecha base para el mes (se usa F_LECT_ANT del mes anterior facturado)
    fecha_medicion = Column(Date, index=True, nullable=False)
    periodo = Column(String(10), nullable=False)  # MMYYYY format
    
    # Potencias (kW)
    pot_contratada = Column(Float, nullable=True)  # Contratada (carry-forward trimestral)
    pot_demandada_max = Column(Float, nullable=True)  # MAX(POT_DEMANDADA, POT_FACT_PUNTA, POT_FACT_VALLE, POT_FACT_LLANO)
    
    # Energía y costos
    energia_total = Column(Float, nullable=True)
    importe_neto = Column(Float, nullable=True)
    importe_total = Column(Float, nullable=True)
    
    # Segmentación y clasificación
    tarifa = Column(String(50), nullable=True)
    referencia = Column(String(255), nullable=True)
    tipo = Column(String(100), nullable=True)
    sector = Column(String(100), nullable=True)
    denominacion = Column(String(255), nullable=True)
    combinacion = Column(String(255), nullable=True)
    sector_macro = Column(String(100), nullable=True)
    
    # Metadata
    nro_factura = Column(Integer, nullable=True)
    factor_potencia = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    __table_args__ = (
        Index('ix_nic_fecha', 'nic', 'fecha_medicion'),
        Index('ix_sector_macro', 'sector_macro'),
        Index('ix_sector', 'sector'),
    )

class ReferenciaNic(Base):
    """Tabla de referencia para segmentación de NICs."""
    __tablename__ = "referencias_nic"

    id = Column(Integer, primary_key=True, index=True)
    nic = Column(Integer, unique=True, index=True, nullable=False)
    sector = Column(String(100), nullable=True)
    denominacion = Column(String(255), nullable=True)
    tarifa = Column(String(50), nullable=True)
    combinacion = Column(String(255), nullable=True)
    sector_macro = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
