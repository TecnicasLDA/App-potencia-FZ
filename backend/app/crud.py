from sqlalchemy.orm import Session
from sqlalchemy import func, and_
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
