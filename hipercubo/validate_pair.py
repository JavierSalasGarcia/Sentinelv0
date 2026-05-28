"""
Etapa 5 – Validación: resta entre dos épocas del hipercubo → GeoTIFF.

Uso:
    python validate_pair.py --date1 2019-08-31 --date2 2020-02-15

Genera:
    D:/Toluca/hipercubo/diff_20190831_20200215.tif
"""

from __future__ import annotations

import argparse
import logging
from datetime import datetime
from pathlib import Path

import numpy as np

try:
    from osgeo import gdal, osr

    gdal.UseExceptions()
except ImportError as e:
    raise ImportError("Instala GDAL: conda install -c conda-forge gdal") from e

try:
    import netCDF4 as nc  # type: ignore
except ImportError as e:
    raise ImportError(
        "Instala netCDF4: conda install -c conda-forge netcdf4"
    ) from e

from build_hypercube import CUBE_PATH, get_epoch

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Parámetros de salida por defecto
# ---------------------------------------------------------------------------
OUTPUT_DIR = Path("D:/Toluca/hipercubo")


# ---------------------------------------------------------------------------
# Exportar diferencia como GeoTIFF
# ---------------------------------------------------------------------------

def _get_cube_geo(cube_path: Path) -> dict:
    """Extrae información geoespacial del hipercubo NetCDF."""
    with nc.Dataset(str(cube_path), "r") as ds:
        lats = ds["lat"][:]
        lons = ds["lon"][:]
        epsg = int(getattr(ds, "epsg", 4326))

    lat_step = float(lats[1] - lats[0]) if len(lats) > 1 else -8.33e-5
    lon_step = float(lons[1] - lons[0]) if len(lons) > 1 else 8.33e-5

    return {
        "x_origin": float(lons[0]),
        "y_origin": float(lats[0]),
        "x_step": lon_step,
        "y_step": lat_step,
        "epsg": epsg,
        "width": len(lons),
        "height": len(lats),
    }


def export_diff_geotiff(
    date1_str: str,
    date2_str: str,
    cube_path: Path = CUBE_PATH,
    output_dir: Path = OUTPUT_DIR,
) -> Path:
    """
    Calcula la diferencia de desplazamiento entre date2 y date1 y la
    exporta como GeoTIFF de un solo canal (Float32) con el mismo CRS
    que el hipercubo.

    date1_str, date2_str: 'YYYY-MM-DD'
    """
    d1 = date1_str.replace("-", "")
    d2 = date2_str.replace("-", "")
    out_name = f"diff_{d1}_{d2}.tif"
    out_path = output_dir / out_name

    log.info("Cargando época 1 (%s)…", d1)
    epoch1 = get_epoch(cube_path, d1)

    log.info("Cargando época 2 (%s)…", d2)
    epoch2 = get_epoch(cube_path, d2)

    diff = (epoch2 - epoch1).astype(np.float32)
    log.info(
        "Diferencia calculada: min=%.4f m, max=%.4f m, mean=%.4f m",
        float(np.nanmin(diff)),
        float(np.nanmax(diff)),
        float(np.nanmean(diff)),
    )

    geo = _get_cube_geo(cube_path)

    # Geotransform GDAL: (x_origin, x_step, 0, y_origin, 0, y_step)
    gt = (
        geo["x_origin"],
        geo["x_step"],
        0.0,
        geo["y_origin"],
        0.0,
        geo["y_step"],
    )

    driver: gdal.Driver = gdal.GetDriverByName("GTiff")
    ds_out: gdal.Dataset = driver.Create(
        str(out_path),
        geo["width"],
        geo["height"],
        1,
        gdal.GDT_Float32,
        options=[
            "COMPRESS=LZW",
            "TILED=YES",
            "BIGTIFF=IF_SAFER",
        ],
    )
    if ds_out is None:
        raise RuntimeError(f"GDAL no pudo crear: {out_path}")

    ds_out.SetGeoTransform(gt)

    srs = osr.SpatialReference()
    srs.ImportFromEPSG(geo["epsg"])
    ds_out.SetProjection(srs.ExportToWkt())

    band = ds_out.GetRasterBand(1)
    band.SetNoDataValue(np.nan)
    band.WriteArray(diff)

    # Calcular y guardar estadísticas en el GeoTIFF
    band.ComputeStatistics(False)
    ds_out.FlushCache()
    ds_out = None  # cerrar

    log.info("GeoTIFF exportado: %s", out_path)
    _print_validation_summary(diff, d1, d2)
    return out_path


def _print_validation_summary(diff: np.ndarray, d1: str, d2: str) -> None:
    valid = diff[~np.isnan(diff)]
    log.info("─── Resumen de validación %s – %s ───", d1, d2)
    log.info("  Píxeles válidos : %d", valid.size)
    log.info("  Mínimo         : %.4f m", float(valid.min()))
    log.info("  Máximo         : %.4f m", float(valid.max()))
    log.info("  Media          : %.4f m", float(valid.mean()))
    log.info("  Desv. estándar : %.4f m", float(valid.std()))
    log.info(
        "  Rango intercuartil: %.4f – %.4f m",
        float(np.percentile(valid, 25)),
        float(np.percentile(valid, 75)),
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Valida el hipercubo: resta dos épocas y exporta GeoTIFF."
    )
    p.add_argument(
        "--date1",
        required=True,
        help="Fecha inicial (YYYY-MM-DD o YYYYMMDD)",
    )
    p.add_argument(
        "--date2",
        required=True,
        help="Fecha final (YYYY-MM-DD o YYYYMMDD)",
    )
    p.add_argument(
        "--cube",
        default=str(CUBE_PATH),
        help=f"Ruta al hipercubo .nc (default: {CUBE_PATH})",
    )
    p.add_argument(
        "--outdir",
        default=str(OUTPUT_DIR),
        help=f"Directorio de salida (default: {OUTPUT_DIR})",
    )
    return p.parse_args()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    args = _parse_args()
    tif = export_diff_geotiff(
        args.date1,
        args.date2,
        cube_path=Path(args.cube),
        output_dir=Path(args.outdir),
    )
    print(f"\nGeoTIFF de validación: {tif}")
