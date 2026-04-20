"""
Importador independiente de Maestro de NICs desde Excel/CSV.
No reemplaza la ingesta principal; sirve para carga/actualizacion puntual del maestro.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, Optional, Tuple

import pandas as pd

from app.database import SessionLocal
from app import models
from ingest_data import detectar_columnas_maestro, limpiar_valor_texto, resolver_ruta_datos


PG_INT_MAX = 2_147_483_647


def _leer_archivo_maestro(path: Path) -> Dict[int, dict]:
    """Lee un archivo maestro (xlsx/xlsm/csv) y devuelve datos por NIC."""
    referencias: Dict[int, dict] = {}

    def procesar_dataframe(df: pd.DataFrame, source_label: str) -> int:
        columnas = detectar_columnas_maestro(df)
        if not columnas:
            return 0

        # Campo opcional extra para referencia explicita.
        referencia_col = None
        for col in df.columns:
            col_norm = str(col).strip().upper().replace(" ", "")
            if col_norm in {"REFERENCIA", "NOMBRENIC", "NOMBRENIC"}:
                referencia_col = col
                break

        usados = 0
        for _, row in df.iterrows():
            nic_val = pd.to_numeric(row.get(columnas["nic"]), errors="coerce")
            if pd.isna(nic_val):
                continue

            nic = int(nic_val)
            if nic <= 0:
                continue

            combinacion = limpiar_valor_texto(row.get(columnas["combinacion"])) if columnas["combinacion"] else None
            referencia = limpiar_valor_texto(row.get(referencia_col)) if referencia_col else None

            referencias[nic] = {
                "sector": limpiar_valor_texto(row.get(columnas["sector"])) if columnas["sector"] else None,
                "denominacion": limpiar_valor_texto(row.get(columnas["denominacion"])) if columnas["denominacion"] else None,
                "tarifa": limpiar_valor_texto(row.get(columnas["tarifa"])) if columnas["tarifa"] else None,
                "combinacion": combinacion,
                "referencia": referencia or combinacion,
                "sector_macro": limpiar_valor_texto(row.get(columnas["sector_macro"])) if columnas["sector_macro"] else None,
            }
            usados += 1

        if usados > 0:
            print(f"Maestro detectado en {source_label}: {usados} filas procesadas")
        return usados

    ext = path.suffix.lower()
    if ext == ".csv":
        df = pd.read_csv(path, sep=None, engine="python")
        procesar_dataframe(df, str(path))
        return referencias

    if ext in {".xlsx", ".xlsm"}:
        sheets = pd.read_excel(path, sheet_name=None)
        for name, df in sheets.items():
            procesar_dataframe(df, f"{path} [{name}]")
        return referencias

    raise ValueError(f"Formato no soportado: {path.suffix}")


def _resolver_path_entrada(path_arg: Optional[str]) -> Tuple[Path, bool]:
    """Resuelve ruta de entrada. Si no se pasa argumento, usa busqueda por defecto."""
    if path_arg:
        p = Path(path_arg).expanduser().resolve()
        return p, True

    candidates = [
        resolver_ruta_datos("MAESTRO_NICS.xlsx"),
        resolver_ruta_datos("MAESTRO_NICS.csv"),
        resolver_ruta_datos("Maestro de NICs.xlsx"),
        resolver_ruta_datos("maestro_nics.xlsx"),
        resolver_ruta_datos("GRAFICOS DE POTENCIAS 2026-MARZO.xlsx"),
    ]

    for c in candidates:
        if c.exists():
            return c.resolve(), True

    # Mostrar un candidato sugerido para facilitar uso.
    return candidates[0].resolve(), False


def importar_maestro(path: Path, dry_run: bool = False) -> None:
    db = SessionLocal()
    try:
        maestro = _leer_archivo_maestro(path)
        if not maestro:
            print("No se detectaron filas validas de maestro (revisar encabezados/hoja)")
            return

        print(f"Total NICs en archivo: {len(maestro)}")

        updated_refs = 0
        updated_mediciones = 0
        missing_in_mediciones = 0
        skipped_out_of_range = 0
        skipped_examples = []

        for nic, data in maestro.items():
            if nic > PG_INT_MAX:
                skipped_out_of_range += 1
                if len(skipped_examples) < 10:
                    skipped_examples.append(nic)
                continue

            ref = db.query(models.ReferenciaNic).filter(models.ReferenciaNic.nic == nic).first()
            if not ref:
                ref = models.ReferenciaNic(nic=nic)
                db.add(ref)

            for key in ["sector", "denominacion", "tarifa", "combinacion", "sector_macro"]:
                if data.get(key) is not None:
                    setattr(ref, key, data[key])
            updated_refs += 1

            update_values = {}
            for key in ["referencia", "tarifa", "sector_macro", "sector", "denominacion", "combinacion"]:
                if data.get(key) is not None:
                    update_values[getattr(models.Medicion, key)] = data[key]

            if update_values:
                q = db.query(models.Medicion).filter(models.Medicion.nic == nic)
                count_nic = q.count()
                if count_nic == 0:
                    missing_in_mediciones += 1
                else:
                    q.update(update_values, synchronize_session=False)
                    updated_mediciones += count_nic

        if dry_run:
            db.rollback()
            print("Dry-run: no se guardaron cambios en base")
        else:
            db.commit()
            print("Importacion de maestro completada")

        print(f"Referencias upsert: {updated_refs}")
        print(f"Filas de mediciones actualizadas: {updated_mediciones}")
        print(f"NICs del maestro no encontrados en mediciones: {missing_in_mediciones}")
        print(f"NICs fuera de rango INTEGER omitidos: {skipped_out_of_range}")
        if skipped_examples:
            print(f"Ejemplos omitidos: {', '.join(str(x) for x in skipped_examples)}")

    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Importa Maestro de NICs desde Excel/CSV")
    parser.add_argument(
        "--file",
        dest="file_path",
        default=None,
        help="Ruta al archivo .xlsx/.xlsm/.csv del maestro",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Valida y muestra resumen sin guardar cambios",
    )
    args = parser.parse_args()

    input_path, exists = _resolver_path_entrada(args.file_path)
    if not exists:
        print(f"No se encontro archivo de maestro. Colocalo en: {input_path}")
        raise SystemExit(1)

    print(f"Usando archivo maestro: {input_path}")
    importar_maestro(input_path, dry_run=args.dry_run)
