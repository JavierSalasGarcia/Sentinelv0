"""
Etapa 1 – Conversión BEAM-DIMAP → HDF5 compatible con MintPy.

Para cada par fmaster_fslave_..._Disp_TC.dim en D:/Toluca/:
  - Lee la banda de desplazamiento y coherencia con GDAL.
  - Extrae metadatos de órbita/geometría del archivo .dim (XML).
  - Escribe un HDF5 individual en D:/Toluca/mintpy_inputs/
    siguendo el esquema esperado por MintPy (ifgramStack-like).

Ejecutar antes de mintpy_sbas.py.
"""

from __future__ import annotations

import gc
import logging
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import h5py
import numpy as np

try:
    from osgeo import gdal, osr

    gdal.UseExceptions()
except ImportError as e:
    raise ImportError("Instala GDAL: conda install -c conda-forge gdal") from e

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------
TOLUCA_DIR = Path("D:/Toluca")
MINTPY_INPUT_DIR = TOLUCA_DIR / "mintpy_inputs"
MINTPY_INPUT_DIR.mkdir(parents=True, exist_ok=True)

# Patrón de nombre esperado: YYYYMMDD_YYYYMMDD_..._Disp_TC.dim
DIM_PATTERN = re.compile(
    r"(?P<master>\d{8})_(?P<slave>\d{8})_.*_Disp_TC\.dim$"
)

# Bandas de interés dentro del .dim (pueden variar según versión de SNAP)
DISP_BAND_KEYWORDS = ["displacement", "Displacement", "unwrapped"]
COH_BAND_KEYWORDS = ["coherence", "Coherence", "coh"]


# ---------------------------------------------------------------------------
# Helpers GDAL
# ---------------------------------------------------------------------------

def _open_dim(dim_path: Path) -> gdal.Dataset:
    ds = gdal.Open(str(dim_path))
    if ds is None:
        raise FileNotFoundError(f"GDAL no pudo abrir: {dim_path}")
    return ds


def _find_band(ds: gdal.Dataset, keywords: list[str]) -> gdal.Band | None:
    for i in range(1, ds.RasterCount + 1):
        band = ds.GetRasterBand(i)
        desc = (band.GetDescription() or "").lower()
        if any(kw.lower() in desc for kw in keywords):
            return band
    return None


def _read_band_blocked(
    band: gdal.Band,
    block_rows: int = 512,
) -> np.ndarray:
    """Lee una banda completa en bloques para reducir uso de RAM."""
    xsize = band.XSize
    ysize = band.YSize
    dtype = gdal.GetDataTypeName(band.DataType)
    np_dtype = _gdal_to_np(dtype)
    arr = np.empty((ysize, xsize), dtype=np_dtype)
    for row_off in range(0, ysize, block_rows):
        rows = min(block_rows, ysize - row_off)
        chunk = band.ReadAsArray(0, row_off, xsize, rows)
        arr[row_off : row_off + rows, :] = chunk
        del chunk
    gc.collect()
    return arr


def _gdal_to_np(gdal_type_name: str) -> type:
    mapping = {
        "Float32": np.float32,
        "Float64": np.float64,
        "Int16": np.int16,
        "Int32": np.int32,
        "UInt16": np.uint16,
        "Byte": np.uint8,
    }
    return mapping.get(gdal_type_name, np.float32)


def _get_geo_info(ds: gdal.Dataset) -> dict:
    gt = ds.GetGeoTransform()
    proj = ds.GetProjection()
    srs = osr.SpatialReference()
    srs.ImportFromWkt(proj)
    return {
        "geotransform": gt,
        "projection": proj,
        "epsg": srs.GetAttrValue("AUTHORITY", 1),
        "xsize": ds.RasterXSize,
        "ysize": ds.RasterYSize,
        "x_step": gt[1],
        "y_step": gt[5],
        "x_first": gt[0],
        "y_first": gt[3],
    }


def _parse_dim_xml(dim_path: Path) -> dict:
    """Extrae metadatos clave del XML BEAM-DIMAP."""
    meta: dict = {}
    try:
        tree = ET.parse(str(dim_path))
        root = tree.getroot()

        # Wavelength / center frequency
        for elem in root.iter("Abstracted_Metadata"):
            for child in elem:
                tag = child.get("name", "")
                val = child.get("value", child.text or "")
                if tag in {
                    "radar_frequency",
                    "centre_freq",
                    "wavelength",
                    "PASS",
                    "incidence_near",
                    "incidence_far",
                    "first_line_time",
                    "last_line_time",
                    "orbit_state_vector_file",
                }:
                    meta[tag] = val
    except Exception as exc:
        log.warning("No se pudo parsear XML %s: %s", dim_path, exc)
    return meta


# ---------------------------------------------------------------------------
# Función principal de conversión
# ---------------------------------------------------------------------------

def convert_dim_to_hdf5(dim_path: Path) -> Path | None:
    """
    Convierte un archivo BEAM-DIMAP de desplazamiento a HDF5 para MintPy.
    Devuelve la ruta del HDF5 generado, o None si falla.
    """
    m = DIM_PATTERN.search(dim_path.name)
    if not m:
        log.warning("Nombre de archivo no coincide con patrón: %s", dim_path.name)
        return None

    date_master = m.group("master")
    date_slave = m.group("slave")
    out_name = f"{date_master}_{date_slave}.h5"
    out_path = MINTPY_INPUT_DIR / out_name

    if out_path.exists():
        log.info("Ya existe: %s. Saltando.", out_path)
        return out_path

    log.info("Convirtiendo: %s", dim_path.name)

    try:
        ds = _open_dim(dim_path)
        geo = _get_geo_info(ds)
        meta_xml = _parse_dim_xml(dim_path)

        disp_band = _find_band(ds, DISP_BAND_KEYWORDS)
        coh_band = _find_band(ds, COH_BAND_KEYWORDS)

        if disp_band is None:
            # Fallback: tomar la primera banda disponible
            log.warning(
                "Banda de desplazamiento no encontrada en %s. "
                "Usando banda 1 como fallback.",
                dim_path.name,
            )
            disp_band = ds.GetRasterBand(1)

        disp_arr = _read_band_blocked(disp_band)
        nodata = disp_band.GetNoDataValue()
        if nodata is not None:
            disp_arr = np.where(disp_arr == nodata, np.nan, disp_arr).astype(np.float32)
        else:
            disp_arr = disp_arr.astype(np.float32)

        coh_arr: np.ndarray | None = None
        if coh_band is not None:
            coh_arr = _read_band_blocked(coh_band).astype(np.float32)

        ds = None  # cierra el dataset
        gc.collect()

        # Escribir HDF5 -------------------------------------------------------
        with h5py.File(out_path, "w") as hf:
            # Datos de desplazamiento (metros)
            dset = hf.create_dataset(
                "displacement",
                data=disp_arr,
                compression="gzip",
                compression_opts=4,
                chunks=True,
            )
            dset.attrs["unit"] = "m"
            dset.attrs["date_master"] = date_master
            dset.attrs["date_slave"] = date_slave

            if coh_arr is not None:
                hf.create_dataset(
                    "coherence",
                    data=coh_arr,
                    compression="gzip",
                    compression_opts=4,
                    chunks=True,
                )

            # Metadatos geoespaciales
            grp = hf.create_group("metadata")
            grp.attrs["DATE12"] = f"{date_master}_{date_slave}"
            grp.attrs["X_FIRST"] = geo["x_first"]
            grp.attrs["Y_FIRST"] = geo["y_first"]
            grp.attrs["X_STEP"] = geo["x_step"]
            grp.attrs["Y_STEP"] = geo["y_step"]
            grp.attrs["LENGTH"] = geo["ysize"]
            grp.attrs["WIDTH"] = geo["xsize"]
            grp.attrs["EPSG"] = geo["epsg"] or "4326"
            grp.attrs["PROJECTION"] = geo["projection"]
            # Metadatos del .dim
            for k, v in meta_xml.items():
                grp.attrs[k] = str(v)

        del disp_arr, coh_arr
        gc.collect()

        log.info("HDF5 guardado: %s", out_path)
        return out_path

    except Exception:
        log.exception("Error convirtiendo %s", dim_path)
        if out_path.exists():
            out_path.unlink()
        return None


# ---------------------------------------------------------------------------
# Lote completo
# ---------------------------------------------------------------------------

def convert_all(toluca_dir: Path = TOLUCA_DIR) -> list[Path]:
    """Convierte todos los .dim de desplazamiento en toluca_dir."""
    dim_files = sorted(toluca_dir.glob("*_Disp_TC.dim"))
    if not dim_files:
        log.warning("No se encontraron archivos *_Disp_TC.dim en %s", toluca_dir)
        return []

    log.info("Archivos .dim encontrados: %d", len(dim_files))
    results = []
    for dim_path in dim_files:
        h5 = convert_dim_to_hdf5(dim_path)
        if h5:
            results.append(h5)
        gc.collect()

    log.info("Conversión completada: %d/%d archivos.", len(results), len(dim_files))
    return results


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    convert_all()
