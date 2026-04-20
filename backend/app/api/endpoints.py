from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import date
from typing import Optional

from .. import crud, schemas
from ..database import get_db

router = APIRouter(prefix="/api", tags=["potencia"])

@router.get("/filtros", response_model=schemas.FiltrosDisponiblesResponse)
def obtener_filtros_disponibles(db: Session = Depends(get_db)):
    """Obtiene los filtros disponibles (sectores, denominaciones, NICs)."""

    try:
        # Sectores macro (con "Todo Zuccardi" primero)
        sectores_macro_query = crud.obtener_sectores_macro(db)
        sectores_macro_set = set([sm[0] for sm in sectores_macro_query if sm[0]])
        sectores_macro_list = [
            schemas.FiltroOption(value="*", label="Todo Zuccardi")
        ] + [
            schemas.FiltroOption(value=s, label=s)
            for s in sorted(sectores_macro_set)
        ]

        # Sectores (sin filtro macro, mostrar todos)
        sectores_query = crud.obtener_sectores_por_macro(db)
        sectores_set = set([s[0] for s in sectores_query if s[0]])
        sectores_list = [
            schemas.FiltroOption(value="*", label="Todos")
        ] + [
            schemas.FiltroOption(value=s, label=s)
            for s in sorted(sectores_set)
        ]

        # Denominaciones
        denominaciones_query = crud.obtener_denominaciones(db)
        denominaciones_set = set([d[0] for d in denominaciones_query if d[0]])
        denominaciones_list = [
            schemas.FiltroOption(value="*", label="Todos")
        ] + [
            schemas.FiltroOption(value=d, label=d)
            for d in sorted(denominaciones_set)
        ]

        # NICs
        nics_query = crud.obtener_nics_filtrados(db)
        nics_list = [
            schemas.FiltroOption(value=str(m.nic), label=f"{m.nic} - {m.referencia or m.denominacion or 'S/N'}")
            for m in nics_query
            if m.nic
        ]

        return schemas.FiltrosDisponiblesResponse(
            sectores_macro=sectores_macro_list,
            sectores=sectores_list,
            denominaciones=denominaciones_list,
            nics=nics_list,
        )
    except SQLAlchemyError as e:
        db.rollback()
        print(f"Error DB en /api/filtros: {e}")
        return schemas.FiltrosDisponiblesResponse(
            sectores_macro=[schemas.FiltroOption(value="*", label="Todo Zuccardi")],
            sectores=[schemas.FiltroOption(value="*", label="Todos")],
            denominaciones=[schemas.FiltroOption(value="*", label="Todos")],
            nics=[],
        )

@router.get("/filtros/cascada")
def obtener_filtros_cascada(
    sector_macro: Optional[str] = Query(None),
    sector: Optional[str] = Query(None),
    denominacion: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Obtiene filtros cascada: sectores según sector_macro, etc."""

    try:
        result = {}

        # Si sector_macro está especificado y no es "*", filtrarlo
        sector_macro_filter = sector_macro if sector_macro and sector_macro != "*" else None

        # Sectores según sector_macro
        sectores_query = crud.obtener_sectores_por_macro(db, sector_macro_filter)
        sectores_set = set([s[0] for s in sectores_query if s[0]])
        result["sectores"] = [
            {"value": s, "label": s}
            for s in sorted(sectores_set)
        ]

        # Denominaciones según sector_macro y sector
        sector_filter = sector if sector and sector != "*" else None
        denominaciones_query = crud.obtener_denominaciones(
            db,
            sector_macro=sector_macro_filter,
            sector=sector_filter,
        )
        denominaciones_set = set([d[0] for d in denominaciones_query if d[0]])
        result["denominaciones"] = [
            {"value": d, "label": d}
            for d in sorted(denominaciones_set)
        ]

        # NICs según todos los filtros
        denominacion_filter = denominacion if denominacion and denominacion != "*" else None
        nics_query = crud.obtener_nics_filtrados(
            db,
            sector_macro=sector_macro_filter,
            sector=sector_filter,
            denominacion=denominacion_filter,
        )
        result["nics"] = [
            {"value": str(m.nic), "label": f"{m.nic} - {m.referencia or m.denominacion or 'S/N'}"}
            for m in nics_query
            if m.nic
        ]

        return result
    except SQLAlchemyError as e:
        db.rollback()
        print(f"Error DB en /api/filtros/cascada: {e}")
        return {"sectores": [], "denominaciones": [], "nics": []}

@router.get("/grafico/{nic}", response_model=schemas.GraficoResponse)
def obtener_datos_grafico(
    nic: int,
    fecha_inicio: Optional[date] = Query(None),
    fecha_fin: Optional[date] = Query(None),
    db: Session = Depends(get_db)
):
    """Obtiene datos de potencia contratada vs demandada para un NIC."""

    try:
        mediciones = crud.obtener_mediciones_por_nic(db, nic, fecha_inicio, fecha_fin)
    except SQLAlchemyError as e:
        db.rollback()
        print(f"Error DB en /api/grafico/{nic}: {e}")
        return schemas.GraficoResponse(
            nic=nic,
            referencia="",
            combinacion="",
            data=[],
            unidad="kW",
        )
    
    if not mediciones:
        # Si no hay datos, retornar response vacío
        return schemas.GraficoResponse(
            nic=nic,
            referencia="",
            combinacion="",
            data=[],
            unidad="kW"
        )
    
    # Usar referencia y combinación del primer registro disponible
    referencia = mediciones[0].referencia or ""
    combinacion = mediciones[0].combinacion or ""
    
    # Convertir mediciones a puntos de gráfico
    data_points = []
    for med in mediciones:
        try:
            # Parsear período MMYYYY para generar label
            periodo_str = str(med.periodo).zfill(6)
            mes = int(periodo_str[:2])
            año = int(periodo_str[2:])
            mes_label = f"{mes:02d}/{año}"
        except:
            mes_label = str(med.periodo)
        
        data_points.append(schemas.GraficoDataPoint(
            fecha=med.fecha_medicion.isoformat() if med.fecha_medicion else "",
            mes_label=mes_label,
            pot_contratada=med.pot_contratada,
            pot_demandada_max=med.pot_demandada_max
        ))
    
    return schemas.GraficoResponse(
        nic=nic,
        referencia=referencia,
        combinacion=combinacion,
        data=data_points,
        unidad="kW"
    )

@router.get("/salud")
def salud():
    """Endpoint de healthcheck."""
    return {"estado": "ok", "servicio": "API Potencia"}
