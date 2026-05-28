"""
Etapa 2 – Inversión SBAS con MintPy.

Lee los HDF5 generados por dim_to_hdf5.py, construye la red de pares
interferométricos (baseline temporal/perpendicular), ensambla el stack
ifgramStack.h5 en el formato nativo de MintPy y ejecuta la inversión
SBAS para obtener la serie temporal de deformación.

Salida: D:/Toluca/mintpy_ts/timeseries.h5  (formato MintPy estándar)
"""

from __future__ import annotations

import gc
import logging
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

import h5py
import numpy as np

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------
MINTPY_INPUT_DIR = Path("D:/Toluca/mintpy_inputs")
MINTPY_TS_DIR = Path("D:/Toluca/mintpy_ts")
MINTPY_TS_DIR.mkdir(parents=True, exist_ok=True)

IFGRAM_STACK_PATH = MINTPY_TS_DIR / "ifgramStack.h5"
TIMESERIES_PATH = MINTPY_TS_DIR / "timeseries.h5"

# Umbrales de red SBAS
MAX_TEMP_BASELINE_DAYS = 180   # días máximos entre imágenes
MAX_PERP_BASELINE_M = 200.0    # metros de baseline perpendicular máxima

# Parámetros de inversión
COH_THRESHOLD = 0.4            # umbral mínimo de coherencia para pesos


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def _date_from_str(s: str) -> datetime:
    return datetime.strptime(s, "%Y%m%d")


def _load_pair_meta(h5_path: Path) -> dict:
    with h5py.File(h5_path, "r") as hf:
        grp = hf["metadata"]
        attrs = dict(grp.attrs)
    m_str, s_str = attrs["DATE12"].split("_")
    attrs["date_master_dt"] = _date_from_str(m_str)
    attrs["date_slave_dt"] = _date_from_str(s_str)
    attrs["temp_baseline"] = (
        attrs["date_slave_dt"] - attrs["date_master_dt"]
    ).days
    attrs["h5_path"] = h5_path
    return attrs


# ---------------------------------------------------------------------------
# Etapa 2a – Red de pares
# ---------------------------------------------------------------------------

def build_network(h5_files: list[Path]) -> list[dict]:
    """
    Filtra pares por baseline temporal y perpendicular,
    devuelve lista de metadatos de pares aptos.
    """
    log.info("Construyendo red SBAS con %d pares candidatos.", len(h5_files))
    pairs = [_load_pair_meta(p) for p in h5_files]

    valid = []
    for p in pairs:
        if p["temp_baseline"] > MAX_TEMP_BASELINE_DAYS:
            log.debug(
                "Descartado (baseline temporal %d d): %s",
                p["temp_baseline"],
                p["DATE12"],
            )
            continue
        # Baseline perpendicular: se lee del HDF5 si está disponible,
        # de lo contrario se acepta (no hay DEM-based info en SNAP output)
        perp = float(p.get("perp_baseline", 0.0))
        if perp and abs(perp) > MAX_PERP_BASELINE_M:
            log.debug(
                "Descartado (baseline perp %.1f m): %s", perp, p["DATE12"]
            )
            continue
        valid.append(p)

    log.info("Pares válidos en la red: %d", len(valid))
    if len(valid) < 2:
        raise ValueError(
            "Red SBAS con menos de 2 pares. Revisa los umbrales de baseline."
        )
    return valid


# ---------------------------------------------------------------------------
# Etapa 2b – Construir ifgramStack.h5
# ---------------------------------------------------------------------------

def _read_disp(h5_path: Path) -> tuple[np.ndarray, np.ndarray | None]:
    with h5py.File(h5_path, "r") as hf:
        disp = hf["displacement"][:]
        coh = hf["coherence"][:] if "coherence" in hf else None
    return disp, coh


def build_ifgram_stack(pairs: list[dict]) -> Path:
    """
    Ensambla ifgramStack.h5 con la estructura esperada por MintPy:
      /unwrapPhase      (n_ifgram, length, width)  float32
      /coherence        (n_ifgram, length, width)  float32
      /date             (n_ifgram, 2)              bytes  'YYYYMMDD'
      /metadata         atributos globales
    """
    if IFGRAM_STACK_PATH.exists():
        log.info("ifgramStack.h5 ya existe. Saltando construcción.")
        return IFGRAM_STACK_PATH

    log.info("Construyendo ifgramStack.h5 (%d pares)…", len(pairs))

    # Dimensiones de referencia (primer par)
    with h5py.File(pairs[0]["h5_path"], "r") as hf:
        ref_shape = hf["displacement"].shape          # (length, width)
        ref_meta = dict(hf["metadata"].attrs)

    n = len(pairs)
    length, width = ref_shape

    CHUNK = (1, min(256, length), min(256, width))

    with h5py.File(IFGRAM_STACK_PATH, "w") as hf:
        # Datasets principales
        unw_ds = hf.create_dataset(
            "unwrapPhase",
            shape=(n, length, width),
            dtype=np.float32,
            chunks=CHUNK,
            compression="gzip",
            compression_opts=4,
        )
        coh_ds = hf.create_dataset(
            "coherence",
            shape=(n, length, width),
            dtype=np.float32,
            chunks=CHUNK,
            compression="gzip",
            compression_opts=4,
        )
        # Dataset de fechas (cadenas bytes de 8 chars)
        dates_ds = hf.create_dataset(
            "date",
            shape=(n, 2),
            dtype="|S8",
        )

        for i, pair in enumerate(pairs):
            disp, coh = _read_disp(pair["h5_path"])
            # MintPy trabaja con fase; en nuestro caso ya es desplazamiento en
            # metros. Se convierte a radianes usando la longitud de onda C-band:
            # λ ≈ 0.05546 m  → fase = (4π/λ) * desplazamiento
            WAVELENGTH = 0.05546  # C-band Sentinel-1 [m]
            phase = (disp * 4 * np.pi / WAVELENGTH).astype(np.float32)
            phase = np.nan_to_num(phase, nan=0.0)

            unw_ds[i] = phase
            coh_ds[i] = coh.astype(np.float32) if coh is not None else np.ones(
                (length, width), dtype=np.float32
            )
            dates_ds[i] = [
                pair["date_master_dt"].strftime("%Y%m%d").encode(),
                pair["date_slave_dt"].strftime("%Y%m%d").encode(),
            ]

            del disp, coh, phase
            gc.collect()
            log.info("  [%d/%d] %s cargado.", i + 1, n, pair["DATE12"])

        # Atributos globales (metadatos del primer par como referencia)
        for k, v in ref_meta.items():
            hf.attrs[k] = v
        hf.attrs["FILE_TYPE"] = "ifgramStack"
        hf.attrs["UNIT"] = "radian"

    log.info("ifgramStack.h5 construido: %s", IFGRAM_STACK_PATH)
    return IFGRAM_STACK_PATH


# ---------------------------------------------------------------------------
# Etapa 2c – Inversión SBAS vía MintPy CLI
# ---------------------------------------------------------------------------

def _get_unique_dates(pairs: list[dict]) -> list[str]:
    dates = set()
    for p in pairs:
        dates.add(p["date_master_dt"].strftime("%Y%m%d"))
        dates.add(p["date_slave_dt"].strftime("%Y%m%d"))
    return sorted(dates)


def run_mintpy_inversion(
    ifgram_stack: Path,
    pairs: list[dict],
    ref_meta: dict,
) -> Path:
    """
    Ejecuta la inversión de series temporales SBAS usando la API Python de
    MintPy (mintpy.timeseries_inversion). Si MintPy no está disponible,
    intenta ejecutarlo como subproceso CLI.
    """
    if TIMESERIES_PATH.exists():
        log.info("timeseries.h5 ya existe. Saltando inversión.")
        return TIMESERIES_PATH

    log.info("Ejecutando inversión SBAS (MintPy)…")

    try:
        # Intentar API Python de MintPy
        from mintpy import timeseries_inversion as ts_inv  # type: ignore

        inps = ts_inv.cmd_line_parse([str(ifgram_stack)])
        inps.outfile = str(TIMESERIES_PATH)
        inps.weightFunc = "var"          # pesos por coherencia
        inps.minCoherence = COH_THRESHOLD
        inps.minNumPixel = 100
        ts_inv.main(inps)

    except ImportError:
        log.warning(
            "MintPy no encontrado como módulo Python. "
            "Intentando vía CLI (smallbaselineApp.py)…"
        )
        _run_mintpy_cli(ifgram_stack, pairs, ref_meta)

    log.info("Inversión SBAS completada: %s", TIMESERIES_PATH)
    return TIMESERIES_PATH


def _run_mintpy_cli(
    ifgram_stack: Path,
    pairs: list[dict],
    ref_meta: dict,
) -> None:
    """Genera smallbaselineApp.cfg y ejecuta MintPy como subproceso."""
    cfg_path = MINTPY_TS_DIR / "smallbaselineApp.cfg"
    dates = _get_unique_dates(pairs)

    cfg_content = f"""
[mintpy]
mintpy.load.processor      = snap
mintpy.load.ifgramStackFile = {ifgram_stack}
mintpy.load.metaFile       = {ifgram_stack}

mintpy.reference.lalo      = {ref_meta.get('Y_FIRST', 19.3):.4f},{ref_meta.get('X_FIRST', -99.6):.4f}

mintpy.networkInversion.weightFunc     = var
mintpy.networkInversion.minCoherence   = {COH_THRESHOLD}
mintpy.networkInversion.minNumPixel    = 100
mintpy.networkInversion.maskDataset    = coherence
mintpy.networkInversion.maskThreshold  = {COH_THRESHOLD}

mintpy.troposphericDelay.method        = no
mintpy.topographicResidual             = no
mintpy.deramp                          = no

mintpy.save.hdfEos5  = no
mintpy.output.dir    = {MINTPY_TS_DIR}
""".strip()

    cfg_path.write_text(cfg_content, encoding="utf-8")
    log.info("Configuración MintPy escrita: %s", cfg_path)

    cmd = [sys.executable, "-m", "mintpy", str(cfg_path)]
    log.info("Ejecutando: %s", " ".join(cmd))
    result = subprocess.run(
        cmd,
        cwd=str(MINTPY_TS_DIR),
        capture_output=False,
        timeout=14400,  # 4 horas
    )
    if result.returncode != 0:
        raise RuntimeError(f"MintPy CLI finalizó con código {result.returncode}")


# ---------------------------------------------------------------------------
# Punto de entrada
# ---------------------------------------------------------------------------

def run_sbas(input_dir: Path = MINTPY_INPUT_DIR) -> Path:
    h5_files = sorted(input_dir.glob("????????_????????.h5"))
    if not h5_files:
        raise FileNotFoundError(
            f"No se encontraron HDF5 de pares en {input_dir}. "
            "Ejecuta primero dim_to_hdf5.py"
        )

    pairs = build_network(h5_files)

    with h5py.File(pairs[0]["h5_path"], "r") as hf:
        ref_meta = dict(hf["metadata"].attrs)

    stack_path = build_ifgram_stack(pairs)
    ts_path = run_mintpy_inversion(stack_path, pairs, ref_meta)
    return ts_path


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    ts = run_sbas()
    print(f"Serie temporal disponible en: {ts}")
