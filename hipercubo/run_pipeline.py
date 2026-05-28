"""
Orquestador del pipeline hipercubo completo.

Ejecuta en orden:
  1. dim_to_hdf5.py   – Conversión BEAM-DIMAP → HDF5
  2. mintpy_sbas.py   – Red SBAS + inversión de series temporales
  3. build_hypercube.py – Construcción del cubo 3D NetCDF-4

Uso:
    python run_pipeline.py [--toluca-dir D:/Toluca] [--skip-conversion]
"""

from __future__ import annotations

import argparse
import gc
import logging
import sys
from pathlib import Path

import psutil

log = logging.getLogger(__name__)

MIN_FREE_RAM_GB = 6.0


def _check_ram() -> None:
    free_gb = psutil.virtual_memory().available / 1024 ** 3
    log.info("RAM disponible: %.1f GB", free_gb)
    if free_gb < MIN_FREE_RAM_GB:
        log.warning(
            "RAM disponible (%.1f GB) por debajo del mínimo recomendado (%.0f GB).",
            free_gb,
            MIN_FREE_RAM_GB,
        )


def _parse() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Pipeline hipercubo InSAR Toluca")
    p.add_argument(
        "--toluca-dir",
        default="D:/Toluca",
        help="Directorio raíz con los .dim procesados",
    )
    p.add_argument(
        "--skip-conversion",
        action="store_true",
        help="Omitir la conversión DIMAP→HDF5 (si ya se realizó)",
    )
    p.add_argument(
        "--skip-inversion",
        action="store_true",
        help="Omitir la inversión SBAS (si timeseries.h5 ya existe)",
    )
    p.add_argument(
        "--skip-cube",
        action="store_true",
        help="Omitir la construcción del cubo (si deformation_cube.nc ya existe)",
    )
    return p.parse_args()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("D:/Toluca/hipercubo_pipeline.log", encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )

    args = _parse()
    toluca_dir = Path(args.toluca_dir)

    log.info("╔══════════════════════════════════════════════════╗")
    log.info("  Pipeline Hipercubo InSAR – Valle de Toluca")
    log.info("  Directorio raíz: %s", toluca_dir)
    log.info("╚══════════════════════════════════════════════════╝")

    _check_ram()

    # ── Etapa 1: Conversión ──────────────────────────────────────────────────
    if not args.skip_conversion:
        log.info("══ Etapa 1: Conversión BEAM-DIMAP → HDF5 ══")
        from dim_to_hdf5 import convert_all
        h5_list = convert_all(toluca_dir)
        if not h5_list:
            log.error("No se generaron archivos HDF5. Abortando.")
            sys.exit(1)
        gc.collect()
    else:
        log.info("Etapa 1 omitida (--skip-conversion).")

    # ── Etapa 2: Inversión SBAS ──────────────────────────────────────────────
    if not args.skip_inversion:
        log.info("══ Etapa 2: Inversión SBAS (MintPy) ══")
        _check_ram()
        from mintpy_sbas import run_sbas
        ts_path = run_sbas(toluca_dir / "mintpy_inputs")
        log.info("Serie temporal: %s", ts_path)
        gc.collect()
    else:
        log.info("Etapa 2 omitida (--skip-inversion).")

    # ── Etapa 3: Hipercubo ──────────────────────────────────────────────────
    if not args.skip_cube:
        log.info("══ Etapa 3: Construcción del Hipercubo 3D ══")
        _check_ram()
        from build_hypercube import build_cube
        cube_path = build_cube()
        log.info("Hipercubo: %s", cube_path)
        gc.collect()
    else:
        log.info("Etapa 3 omitida (--skip-cube).")

    log.info("══ Pipeline completo ══")
    log.info("Resultados en: D:/Toluca/hipercubo/")
    log.info(
        "Para validar un par: python validate_pair.py "
        "--date1 2019-08-31 --date2 2020-02-15"
    )


if __name__ == "__main__":
    main()
