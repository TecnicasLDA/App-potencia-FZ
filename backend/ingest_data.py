"""
Script de ingesta de datos EDEMSA.csv a PostgreSQL.
Aplica lógica de negocio: carry-forward trimestral de POT_CONTRATADA y MAX POT.
"""

import pandas as pd
from typing import Dict, Optional, Tuple
import sys
import os
from pathlib import Path
import re

from sqlalchemy.orm import Session
from app.database import Base, SessionLocal, engine
from app import models


def resolver_ruta_datos(filename: str) -> Path:
    """Resuelve archivos de datos ubicados en backend/ o en la raíz del repo."""
    backend_dir = Path(__file__).parent
    candidates = [
        backend_dir / filename,
        backend_dir.parent / filename,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def normalizar_texto(valor: object) -> str:
    """Normaliza texto para comparar encabezados de forma robusta."""
    s = str(valor or "").strip().upper()
    reemplazos = {
        "Á": "A",
        "É": "E",
        "Í": "I",
        "Ó": "O",
        "Ú": "U",
        "Ü": "U",
        "Ñ": "N",
        "º": " ",
        "°": " ",
    }
    for origen, destino in reemplazos.items():
        s = s.replace(origen, destino)
    s = re.sub(r"[^A-Z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def limpiar_valor_texto(valor: object) -> Optional[str]:
    if pd.isna(valor):
        return None
    texto = str(valor).strip()
    return texto if texto else None


def detectar_columnas_maestro(df: pd.DataFrame) -> Optional[Dict[str, str]]:
    """Detecta columnas del maestro por encabezado, sin depender de nombre de hoja."""
    normalizadas = {col: normalizar_texto(col) for col in df.columns}

    def buscar_columna(candidatas):
        for original, norm in normalizadas.items():
            if norm in candidatas:
                return original
        return None

    col_nic = buscar_columna({"NIC", "N NIC", "NUMERO NIC", "NRO NIC", "NO NIC"})
    col_sector_macro = buscar_columna({"SECTOR MACRO", "SECTORMACRO"})
    col_sector = buscar_columna({"SECTOR"})
    col_denominacion = buscar_columna({"DENOMINACION"})
    col_tarifa = buscar_columna({"TARIFA"})
    col_combinacion = buscar_columna({"COMBINACION", "REFERENCIA", "COMBINACION NIC"})

    if not col_nic:
        return None

    # Aceptar el maestro si al menos aporta una columna de segmentacion.
    if not any([col_sector_macro, col_sector, col_denominacion, col_combinacion, col_tarifa]):
        return None

    return {
        "nic": col_nic,
        "sector_macro": col_sector_macro,
        "sector": col_sector,
        "denominacion": col_denominacion,
        "tarifa": col_tarifa,
        "combinacion": col_combinacion,
    }


def cargar_maestro_nics(backend_dir: Path) -> Dict[int, dict]:
    """Carga maestro de NICs desde CSV/XLSX buscando encabezados estandar."""
    repo_root = backend_dir.parent
    candidates = [
        backend_dir / "MAESTRO_NICS.xlsx",
        backend_dir / "MAESTRO_NICS.csv",
        backend_dir / "Maestro de NICs.xlsx",
        backend_dir / "maestro_nics.xlsx",
        repo_root / "MAESTRO_NICS.xlsx",
        repo_root / "MAESTRO_NICS.csv",
        repo_root / "Maestro de NICs.xlsx",
        repo_root / "maestro_nics.xlsx",
        repo_root / "GRAFICOS DE POTENCIAS 2026-MARZO.xlsx",
    ]

    referencias_dict: Dict[int, dict] = {}

    def agregar_desde_dataframe(df: pd.DataFrame, source_label: str):
        columnas = detectar_columnas_maestro(df)
        if not columnas:
            return 0

        usados = 0
        for _, row in df.iterrows():
            nic_val = pd.to_numeric(row.get(columnas["nic"]), errors="coerce")
            if pd.isna(nic_val):
                continue

            nic = int(nic_val)
            if nic <= 0:
                continue

            referencias_dict[nic] = {
                "sector": limpiar_valor_texto(row.get(columnas["sector"])) if columnas["sector"] else None,
                "denominacion": limpiar_valor_texto(row.get(columnas["denominacion"])) if columnas["denominacion"] else None,
                "tarifa": limpiar_valor_texto(row.get(columnas["tarifa"])) if columnas["tarifa"] else None,
                "combinacion": limpiar_valor_texto(row.get(columnas["combinacion"])) if columnas["combinacion"] else None,
                "sector_macro": limpiar_valor_texto(row.get(columnas["sector_macro"])) if columnas["sector_macro"] else None,
            }
            usados += 1

        if usados > 0:
            print(f"Maestro NICs detectado en {source_label}: {usados} filas procesadas")
        return usados

    for path in candidates:
        if not path.exists():
            continue

        try:
            ext = path.suffix.lower()
            if ext == ".csv":
                df = pd.read_csv(path, sep=None, engine="python")
                agregar_desde_dataframe(df, str(path))
                if referencias_dict:
                    return referencias_dict
            elif ext in {".xlsx", ".xlsm"}:
                hojas = pd.read_excel(path, sheet_name=None)
                for nombre_hoja, df in hojas.items():
                    agregar_desde_dataframe(df, f"{path} [{nombre_hoja}]")
                if referencias_dict:
                    return referencias_dict
        except Exception as e:
            print(f"Advertencia: no se pudo leer maestro NICs en {path}: {e}")

    print("Advertencia: no se encontró Maestro de NICs con columnas esperadas")
    return referencias_dict

def parse_periodo(periodo_str: str) -> Tuple[int, int]:
    """Parsea MMYYYY a (mes, año)."""
    s = str(periodo_str).strip()
    if len(s) >= 6:
        mes = int(s[:2])
        año = int(s[2:6])
        return mes, año
    return None, None

def fecha_de_periodo(mes: int, año: int) -> pd.Timestamp:
    """Convierte mes, año a fecha del primer día del mes."""
    return pd.Timestamp(year=año, month=mes, day=1)

def limpiar_valor_numerico(val) -> float:
    """Convierte valor con coma decimal a float."""
    if pd.isna(val):
        return None
    val_str = str(val).strip()
    if not val_str or val_str.upper() == 'NAN':
        return None
    # Reemplazar coma por punto para parsear
    val_str = val_str.replace(',', '.')
    try:
        return float(val_str)
    except:
        return None

def calcular_pot_demandada_max(row: pd.Series) -> float:
    """Calcula MAX(POT_DEMANDADA, POT_FACT_PUNTA, POT_FACT_VALLE, POT_FACT_LLANO)."""
    valores = []
    for col in ['POT_DEMANDADA', 'POT_FACT_PUNTA', 'POT_FACT_VALLE', 'POT_FACT_LLANO']:
        v = limpiar_valor_numerico(row.get(col))
        if v is not None and v > 0:
            valores.append(v)
    
    return max(valores) if valores else None

def aplicar_carry_forward_trimestral(df_nic: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica carry-forward trimestral de POT_CONTRATADA.
    POT_CONTRATADA se repite cada trimestre.
    """
    df_nic = df_nic.sort_values('fecha_medicion').copy()
    
    # Rellenar POT_CONTRATADA hacia adelante (método 'ffill') pero máximo 3 meses
    pot_contratada = df_nic['pot_contratada'].copy()
    
    for i in range(len(df_nic)):
        if pd.notna(pot_contratada.iloc[i]):
            # Este mes tiene valor, propagarlo a los próximos 2 meses (trimestre)
            for j in range(i+1, min(i+3, len(df_nic))):
                if pd.isna(pot_contratada.iloc[j]):
                    pot_contratada.iloc[j] = pot_contratada.iloc[i]
                else:
                    # Si el siguiente mes ya tiene valor, parar la propagación
                    break
    
    df_nic['pot_contratada'] = pot_contratada
    return df_nic

def limpiar_y_deduplicar(df: pd.DataFrame) -> pd.DataFrame:
    """
    Deduplica por NIC+PERIODO, manteniendo la factura con mayor NRO_FACTURA.
    """
    # Ordenar por NRO_FACTURA descendente, para que keep='first' quede con mayor NRO_FACTURA
    df = df.sort_values('nro_factura', ascending=False, na_position='last')
    
    # Deduplicar por NIC + PERIODO
    df = df.drop_duplicates(subset=['nic', 'periodo'], keep='first')
    
    return df

def ingestar_csv(csv_path: str, db: Session):
    """Lee CSV EDEMSA y carga en PostgreSQL."""
    
    print(f"Leyendo {csv_path}...")
    df = pd.read_csv(csv_path, sep=';', encoding='utf-8')
    
    print(f"Total de filas crudas: {len(df)}")
    
    # Limpiar nombres de columnas
    df.columns = df.columns.str.strip()
    
    # Filtrar columnas relevantes
    columnas_necesarias = [
        'NIC', 'CLIENTE', 'DOMICILIO_SUMINISTRO', 'LOCALIDAD', 'DEPARTAMENTO', 
        'COD_POSTAL', 'PERIODO', 'TARIFA', 'IMPORTE_TOTAL', 'IMPORTE_NETO',
        'F_LECT_ANT', 'F_LECT_ACT', 'NRO_FACTURA',
        'POT_CONTRATADA', 'POT_DEMANDADA', 'POT_FACT_PUNTA', 'POT_FACT_VALLE', 
        'POT_FACT_LLANO', 'COS_FI'
    ]
    
    # Verificar que existen todas las columnas
    cols_faltantes = [c for c in columnas_necesarias if c not in df.columns]
    if cols_faltantes:
        print(f"Advertencia: columnas faltantes: {cols_faltantes}")
    
    # Mantener solo columnas que existen
    df = df[[c for c in columnas_necesarias if c in df.columns]]
    
    # Limpiar datos numéricos
    print("Limpiando datos numéricos...")
    df['nic'] = pd.to_numeric(df['NIC'], errors='coerce').astype('Int64')
    df['nro_factura'] = pd.to_numeric(df['NRO_FACTURA'], errors='coerce').astype('Int64')
    df['pot_contratada'] = df['POT_CONTRATADA'].apply(limpiar_valor_numerico)
    df['pot_demandada_max'] = df.apply(calcular_pot_demandada_max, axis=1)
    df['importe_total'] = df['IMPORTE_TOTAL'].apply(limpiar_valor_numerico)
    df['importe_neto'] = df['IMPORTE_NETO'].apply(limpiar_valor_numerico)
    df['factor_potencia'] = df['COS_FI'].apply(limpiar_valor_numerico)
    
    # Parsear período y fecha
    print("Procesando períodos y fechas...")
    df['periodo'] = df['PERIODO'].astype(str).str.strip()
    df[['mes_periodo', 'año_periodo']] = df['periodo'].apply(
        lambda p: pd.Series(parse_periodo(p))
    )
    
    # Usar F_LECT_ANT como fecha de medición (mes anterior al facturado)
    df['fecha_medicion'] = pd.to_datetime(df['F_LECT_ANT'], format='%d/%m/%Y', errors='coerce')
    
    # Filtrar filas sin NIC o fecha
    df = df.dropna(subset=['nic', 'fecha_medicion'])
    df = df[df['nic'] > 0]
    
    print(f"Filas después de limpieza: {len(df)}")
    
    # Deduplicar por NIC+PERIODO
    print("Deduplicando por NIC+PERIODO...")
    df = limpiar_y_deduplicar(df)
    
    print(f"Filas después de deduplicación: {len(df)}")
    
    # Aplicar carry-forward trimestral por NIC
    print("Aplicando carry-forward trimestral de POT_CONTRATADA...")
    df_procesar = []
    for nic, group in df.groupby('nic'):
        group_procesado = aplicar_carry_forward_trimestral(group)
        df_procesar.append(group_procesado)
    
    df = pd.concat(df_procesar, ignore_index=True)
    df = df.sort_values(['nic', 'fecha_medicion'])
    
    print(f"Filas después de carry-forward: {len(df)}")
    
    # Cargar tabla de referencias NIC desde Maestro (CSV/XLSX).
    print("Construyendo referencias NIC...")
    backend_dir = Path(__file__).parent
    referencias_dict = cargar_maestro_nics(backend_dir)
    
    # Mapear referencias a mediciones
    print("Mapeando referencias a mediciones...")
    for idx, row in df.iterrows():
        nic = row['nic']
        if nic in referencias_dict:
            ref = referencias_dict[nic]
            df.at[idx, 'sector'] = ref['sector']
            df.at[idx, 'denominacion'] = ref['denominacion']
            df.at[idx, 'tarifa'] = ref['tarifa']
            df.at[idx, 'combinacion'] = ref['combinacion']
            df.at[idx, 'sector_macro'] = ref['sector_macro']
            df.at[idx, 'referencia'] = ref['combinacion']  # REFERENCIA = COMBINACION (con NIC)
            df.at[idx, 'tipo'] = 'Medición'  # tipo por defecto

    # Fallback de segmentacion para NICs sin maestro.
    df['sector_macro'] = df.get('sector_macro', pd.Series(index=df.index)).fillna(df['DEPARTAMENTO'])
    df['sector'] = df.get('sector', pd.Series(index=df.index)).fillna(df['LOCALIDAD'])
    df['denominacion'] = df.get('denominacion', pd.Series(index=df.index)).fillna(df['CLIENTE'])

    combinacion_fallback = (
        df['CLIENTE'].astype(str).str.strip().replace('nan', '') + '-' + df['nic'].astype(str)
    )
    df['combinacion'] = df.get('combinacion', pd.Series(index=df.index)).fillna(combinacion_fallback)
    df['referencia'] = df.get('referencia', pd.Series(index=df.index)).fillna(df['combinacion'])
    
    # Mapear tipo desde VLOOKUP (columna AF en BASE DATOS)
    # Por ahora usar tarifa para deducir tipo
    def deducir_tipo(tarifa):
        if pd.isna(tarifa):
            return 'Medición'
        t = str(tarifa).upper()
        if 'RIEGO' in t or 'RIEGO AGRICOLA' in t:
            return 'Riego'
        elif 'MT' in t or 'BT' in t:
            return 'Industrial'
        else:
            return 'Otros'
    
    df['tarifa_final'] = df.get('tarifa', pd.Series(index=df.index)).fillna(df['TARIFA'])
    df['tipo'] = df['tarifa_final'].apply(deducir_tipo)
    
    # Insertar en BD
    print("Insertando datos en PostgreSQL...")

    # En recargas completas, limpiar primero para evitar duplicados acumulados.
    replace_existing = os.getenv("INGEST_REPLACE_EXISTING", "true").lower() == "true"
    if replace_existing:
        deleted = db.query(models.Medicion).delete()
        db.commit()
        print(f"Registros previos eliminados: {deleted}")
    
    batch_size = 1000
    registros_insertados = 0
    
    for idx in range(0, len(df), batch_size):
        batch = df.iloc[idx:idx+batch_size]
        
        for _, row in batch.iterrows():
            medicion = models.Medicion(
                nic=int(row['nic']) if pd.notna(row['nic']) else None,
                cliente=str(row['CLIENTE']).strip() if pd.notna(row['CLIENTE']) else None,
                domicilio=str(row['DOMICILIO_SUMINISTRO']).strip() if pd.notna(row['DOMICILIO_SUMINISTRO']) else None,
                localidad=str(row['LOCALIDAD']).strip() if pd.notna(row['LOCALIDAD']) else None,
                departamento=str(row['DEPARTAMENTO']).strip() if pd.notna(row['DEPARTAMENTO']) else None,
                codigo_postal=str(row['COD_POSTAL']).strip() if pd.notna(row['COD_POSTAL']) else None,
                fecha_medicion=row['fecha_medicion'],
                periodo=row['periodo'],
                pot_contratada=float(row['pot_contratada']) if pd.notna(row['pot_contratada']) else None,
                pot_demandada_max=float(row['pot_demandada_max']) if pd.notna(row['pot_demandada_max']) else None,
                energia_total=None,  # No en CSV actual
                importe_neto=row['importe_neto'],
                importe_total=row['importe_total'],
                tarifa=row['tarifa_final'] if pd.notna(row['tarifa_final']) else None,
                referencia=row.get('referencia'),
                tipo=row['tipo'],
                sector=row.get('sector'),
                denominacion=row.get('denominacion'),
                combinacion=row.get('combinacion'),
                sector_macro=row.get('sector_macro'),
                nro_factura=int(row['nro_factura']) if pd.notna(row['nro_factura']) else None,
                factor_potencia=row['factor_potencia'],
            )
            db.add(medicion)
            registros_insertados += 1
        
        db.commit()
        print(f"Insertados {registros_insertados}...")
    
    print(f"Total insertado: {registros_insertados} registros")
    return registros_insertados

if __name__ == "__main__":
    csv_path = resolver_ruta_datos("EDEMSA.csv")
    
    if not csv_path.exists():
        print(f"Error: no se encuentra {csv_path}")
        sys.exit(1)
    
    db = SessionLocal()
    try:
        # Inicializar esquema en despliegues nuevos (Neon/Render) antes de insertar.
        Base.metadata.create_all(bind=engine)
        ingestar_csv(str(csv_path), db)
        print("✓ Ingesta completada exitosamente")
    except Exception as e:
        print(f"✗ Error durante ingesta: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()
