from sqlalchemy.orm import Session
from sqlalchemy import func, and_, cast, String, or_
from typing import List, Optional
from datetime import date
from . import models, schemas

# Mediciones
def crear_medicion(db: Session, medicion: schemas.MedicionCreate) -> models.Medicion:
    db_medicion = models.Medicion(**medicion.dict())
    db.add(db_medicion)
    db.commit()
    db.refresh(db_medicion)
    return db_medicion

def obtener_mediciones_por_nic(
    db: Session, 
    nic: int, 
    fecha_inicio: Optional[date] = None,
    fecha_fin: Optional[date] = None
) -> List[models.Medicion]:
    query = db.query(models.Medicion).filter(models.Medicion.nic == nic)
    
    if fecha_inicio:
        query = query.filter(models.Medicion.fecha_medicion >= fecha_inicio)
    if fecha_fin:
        query = query.filter(models.Medicion.fecha_medicion <= fecha_fin)
    
    return query.order_by(models.Medicion.fecha_medicion).all()

def obtener_nics_unicos(db: Session) -> List[int]:
    return db.query(models.Medicion.nic).distinct().all()

def obtener_sectores_macro(db: Session) -> List[str]:
    return db.query(models.Medicion.sector_macro).filter(
        models.Medicion.sector_macro.isnot(None)
    ).distinct().all()

def obtener_sectores_por_macro(db: Session, sector_macro: Optional[str] = None) -> List[str]:
    query = db.query(models.Medicion.sector).filter(
        models.Medicion.sector.isnot(None)
    )
    if sector_macro:
        query = query.filter(models.Medicion.sector_macro == sector_macro)
    
    return query.distinct().all()

def obtener_denominaciones(
    db: Session, 
    sector_macro: Optional[str] = None,
    sector: Optional[str] = None
) -> List[str]:
    query = db.query(models.Medicion.denominacion).filter(
        models.Medicion.denominacion.isnot(None)
    )
    
    if sector_macro:
        query = query.filter(models.Medicion.sector_macro == sector_macro)
    if sector:
        query = query.filter(models.Medicion.sector == sector)
    
    return query.distinct().all()

def obtener_nics_filtrados(
    db: Session,
    sector_macro: Optional[str] = None,
    sector: Optional[str] = None,
    denominacion: Optional[str] = None
) -> List[models.Medicion]:
    query = db.query(models.Medicion).filter(models.Medicion.nic.isnot(None))
    
    if sector_macro:
        query = query.filter(models.Medicion.sector_macro == sector_macro)
    if sector:
        query = query.filter(models.Medicion.sector == sector)
    if denominacion:
        query = query.filter(models.Medicion.denominacion == denominacion)
    
    return query.order_by(models.Medicion.nic).distinct(models.Medicion.nic).all()

# Referencias NIC
def crear_referencia_nic(db: Session, ref: schemas.ReferenciaNicCreate) -> models.ReferenciaNic:
    db_ref = models.ReferenciaNic(**ref.dict())
    db.add(db_ref)
    db.commit()
    db.refresh(db_ref)
    return db_ref

def obtener_referencia_nic(db: Session, nic: int) -> Optional[models.ReferenciaNic]:
    return db.query(models.ReferenciaNic).filter(models.ReferenciaNic.nic == nic).first()

def actualizar_o_crear_referencia_nic(db: Session, ref: schemas.ReferenciaNicCreate) -> models.ReferenciaNic:
    db_ref = db.query(models.ReferenciaNic).filter(models.ReferenciaNic.nic == ref.nic).first()
    if db_ref:
        for key, value in ref.dict().items():
            setattr(db_ref, key, value)
        db.commit()
        db.refresh(db_ref)
        return db_ref
    else:
        return crear_referencia_nic(db, ref)


def obtener_maestro_nics(
    db: Session,
    search: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[int, List[schemas.MaestroNicItem]]:
    """Lista un registro por NIC para edicion de maestro."""
    latest_by_nic = (
        db.query(
            models.Medicion.nic.label("nic"),
            func.max(models.Medicion.id).label("max_id"),
        )
        .group_by(models.Medicion.nic)
        .subquery()
    )

    query = (
        db.query(models.Medicion)
        .join(latest_by_nic, models.Medicion.id == latest_by_nic.c.max_id)
    )

    if search:
        pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(
                cast(models.Medicion.nic, String).ilike(pattern),
                models.Medicion.referencia.ilike(pattern),
                models.Medicion.combinacion.ilike(pattern),
                models.Medicion.sector_macro.ilike(pattern),
                models.Medicion.sector.ilike(pattern),
                models.Medicion.denominacion.ilike(pattern),
                models.Medicion.tarifa.ilike(pattern),
            )
        )

    total = query.count()
    rows = query.order_by(models.Medicion.nic).offset(offset).limit(limit).all()

    items = [
        schemas.MaestroNicItem(
            nic=row.nic,
            referencia=row.referencia,
            tipo=row.tipo,
            tarifa=row.tarifa,
            sector_macro=row.sector_macro,
            sector=row.sector,
            denominacion=row.denominacion,
            combinacion=row.combinacion,
        )
        for row in rows
    ]

    return total, items


def actualizar_maestro_nic(
    db: Session,
    nic: int,
    payload: schemas.MaestroNicUpdate,
) -> Optional[schemas.MaestroNicItem]:
    """Actualiza maestro para un NIC en referencias_nic y en mediciones."""
    update_data = payload.dict(exclude_unset=True)
    if not update_data:
        row = (
            db.query(models.Medicion)
            .filter(models.Medicion.nic == nic)
            .order_by(models.Medicion.id.desc())
            .first()
        )
        if not row:
            return None
        return schemas.MaestroNicItem(
            nic=row.nic,
            referencia=row.referencia,
            tipo=row.tipo,
            tarifa=row.tarifa,
            sector_macro=row.sector_macro,
            sector=row.sector,
            denominacion=row.denominacion,
            combinacion=row.combinacion,
        )

    # Sincronizar tabla de referencia
    ref = db.query(models.ReferenciaNic).filter(models.ReferenciaNic.nic == nic).first()
    if not ref:
        ref = models.ReferenciaNic(nic=nic)
        db.add(ref)

    ref_fields = ["sector", "denominacion", "tarifa", "combinacion", "sector_macro"]
    for key in ref_fields:
        if key in update_data:
            setattr(ref, key, update_data[key])

    # Propagar cambios a todas las mediciones del NIC para que filtros/grafico reflejen al instante
    mediciones_query = db.query(models.Medicion).filter(models.Medicion.nic == nic)
    if mediciones_query.count() == 0:
        db.rollback()
        return None

    med_fields = ["referencia", "tipo", "tarifa", "sector_macro", "sector", "denominacion", "combinacion"]
    for key in med_fields:
        if key in update_data:
            mediciones_query.update({getattr(models.Medicion, key): update_data[key]}, synchronize_session=False)

    db.commit()

    row = (
        db.query(models.Medicion)
        .filter(models.Medicion.nic == nic)
        .order_by(models.Medicion.id.desc())
        .first()
    )
    if not row:
        return None

    return schemas.MaestroNicItem(
        nic=row.nic,
        referencia=row.referencia,
        tipo=row.tipo,
        tarifa=row.tarifa,
        sector_macro=row.sector_macro,
        sector=row.sector,
        denominacion=row.denominacion,
        combinacion=row.combinacion,
    )
