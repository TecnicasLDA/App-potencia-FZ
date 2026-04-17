from pydantic import BaseModel
from datetime import date
from typing import Optional, List

class MedicionBase(BaseModel):
    nic: int
    fecha_medicion: date
    periodo: str
    pot_contratada: Optional[float] = None
    pot_demandada_max: Optional[float] = None
    energia_total: Optional[float] = None
    importe_total: Optional[float] = None
    tarifa: Optional[str] = None
    referencia: Optional[str] = None
    tipo: Optional[str] = None
    sector: Optional[str] = None
    denominacion: Optional[str] = None
    combinacion: Optional[str] = None
    sector_macro: Optional[str] = None

class MedicionCreate(MedicionBase):
    nro_factura: Optional[int] = None

class MedicionResponse(MedicionBase):
    id: int
    
    class Config:
        from_attributes = True

class ReferenciaNicBase(BaseModel):
    nic: int
    sector: Optional[str] = None
    denominacion: Optional[str] = None
    tarifa: Optional[str] = None
    combinacion: Optional[str] = None
    sector_macro: Optional[str] = None

class ReferenciaNicCreate(ReferenciaNicBase):
    pass

class ReferenciaNicResponse(ReferenciaNicBase):
    id: int
    
    class Config:
        from_attributes = True

# Schemas para API responses
class FiltroOption(BaseModel):
    value: str
    label: str

class GraficoDataPoint(BaseModel):
    fecha: str
    mes_label: str
    pot_contratada: Optional[float]
    pot_demandada_max: Optional[float]

class GraficoResponse(BaseModel):
    nic: int
    referencia: str
    combinacion: str
    data: List[GraficoDataPoint]
    unidad: str = "kW"

class FiltrosDisponiblesResponse(BaseModel):
    sectores_macro: List[FiltroOption]
    sectores: List[FiltroOption]
    denominaciones: List[FiltroOption]
    nics: List[FiltroOption]
