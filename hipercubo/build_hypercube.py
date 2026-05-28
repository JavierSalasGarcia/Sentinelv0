"""
Etapa 3 – Construcción del hipercubo 3D georreferenciado.

Lee timeseries.h5 (MintPy) y genera un cubo NetCDF-4 / HDF5 organizado como:
  eje X → Longitud  (coordenadas Valle de Toluca)
  eje Y → Latitud   (coordenadas Valle de Toluca)
  eje Z → Tiempo    (deformación acumulada en cada fecha, metros)

El cubo se escribe por épocas (slices temporales) para evitar cargar toda
la serie en RAM simultáneamente.

Salida: D:/Toluca/hipercubo/deformation_cube.nc
"""

from __future__ import annotations

import gc
import logging
from datetime import datetime
from pathlib import Path

import h5py
import numpy as np

try:
    import netCDF4 as nc  # type: ignore
except ImportError as e:
    raise ImportError(
        "Instala netCDF4: conda install -c conda-forge netcdf4"
    ) from e

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------
TIMESERIES_PATH = Path("D:/Toluca/mintpy_ts/timeseries.h5")
CUBE_DIR = Path("D:/Toluca/hipercubo")
CUBE_DIR.mkdir(parents=True, exist_ok=True)
CUBE_PATH = CUBE_DIR / "deformation_cube.nc"

# ---------------------------------------------------------------------------
# CRS de salida (WGS-84, igual que SNAP Terrain Correction por defecto)
# ---------------------------------------------------------------------------
EPSG_CODE = 4326
CRS_WKT = (
    'GEOGCS["WGS 84",'
    'DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563]],'
    'PRIMEM["Greenwich",0],'
    'UNIT["degree",0.0174532925199433]]'
)

CHUNK_TIME = 1        # épocas por bloque de escritura (bajo consumo de RAM)
CHUNK_SPACE = 512     # píxeles por dimensión espacial en chunks NC


# ---------------------------------------------------------------------------
# Lectura de metadatos de la serie temporal MintPy
# ---------------------------------------------------------------------------

def _read_timeseries_meta(ts_path: Path) -> dict:
    with h5py.File(ts_path, "r") as hf:
        # MintPy guarda fechas como array de bytes 'YYYYMMDD'
        dates_raw = hf["date"][:]
        dates = [d.decode() if isinstance(d, bytes) else str(d) for d in dates_raw]

        attrs = dict(hf.attrs)
        shape = hf["timeseries"].shape   # (n_dates, length, width)

    x_first = float(attrs.get("X_FIRST", attrs.get("x_first", -99.9)))
    y_first = float(attrs.get("Y_FIRST", attrs.get("y_first", 19.583)))
    x_step = float(attrs.get("X_STEP", attrs.get("x_step", 8.33e-5)))
    y_step = float(attrs.get("Y_STEP", attrs.get("y_step", -8.33e-5)))

    n_dates, length, width = shape

    lons = x_first + np.arange(width) * x_step
    lats = y_first + np.arange(length) * y_step

    return {
        "dates": dates,
        "n_dates": n_dates,
        "length": length,
        "width": width,
        "lons": lons.astype(np.float64),
        "lats": lats.astype(np.float64),
        "x_first": x_first,
        "y_first": y_first,
        "x_step": x_step,
        "y_step": y_step,
        "attrs": attrs,
    }


# ---------------------------------------------------------------------------
# Escritura del cubo NetCDF-4
# ---------------------------------------------------------------------------

def build_cube(
    ts_path: Path = TIMESERIES_PATH,
    cube_path: Path = CUBE_PATH,
    chunk_time: int = CHUNK_TIME,
) -> Path:
    """
    Construye el hipercubo NetCDF-4 procesando epoch-by-epoch (bajo RAM).
    """
    if cube_path.exists():
        log.info("Hipercubo ya existe: %s", cube_path)
        return cube_path

    log.info("Leyendo metadatos de la serie temporal: %s", ts_path)
    meta = _read_timeseries_meta(ts_path)

    n_t = meta["n_dates"]
    n_y = meta["length"]
    n_x = meta["width"]
    dates = meta["dates"]

    log.info(
        "Dimensiones del cubo: tiempo=%d, y=%d, x=%d", n_t, n_y, n_x
    )

    # Tiempo como días desde la primera fecha
    t0 = datetime.strptime(dates[0], "%Y%m%d")
    time_days = np.array(
        [(datetime.strptime(d, "%Y%m%d") - t0).days for d in dates],
        dtype=np.float64,
    )

    chunk_x = min(CHUNK_SPACE, n_x)
    chunk_y = min(CHUNK_SPACE, n_y)

    with nc.Dataset(str(cube_path), "w", format="NETCDF4") as ds:
        # ------- Dimensiones -------
        ds.createDimension("time", n_t)
        ds.createDimension("lat", n_y)
        ds.createDimension("lon", n_x)

        # ------- Variables de coordenadas -------
        time_var = ds.createVariable("time", "f8", ("time",))
        time_var.units = f"days since {dates[0]}"
        time_var.calendar = "proleptic_gregorian"
        time_var.long_name = "Time"
        time_var.axis = "T"
        time_var[:] = time_days

        lat_var = ds.createVariable("lat", "f8", ("lat",))
        lat_var.units = "degrees_north"
        lat_var.standard_name = "latitude"
        lat_var.long_name = "Latitude"
        lat_var.axis = "Y"
        lat_var[:] = meta["lats"]

        lon_var = ds.createVariable("lon", "f8", ("lon",))
        lon_var.units = "degrees_east"
        lon_var.standard_name = "longitude"
        lon_var.long_name = "Longitude"
        lon_var.axis = "X"
        lon_var[:] = meta["lons"]

        # ------- Variable principal: deformación -------
        defo_var = ds.createVariable(
            "displacement",
            "f4",
            ("time", "lat", "lon"),
            zlib=True,
            complevel=4,
            fill_value=np.nan,
            chunksizes=(chunk_time, chunk_y, chunk_x),
        )
        defo_var.units = "m"
        defo_var.long_name = "Cumulative LOS displacement"
        defo_var.standard_name = "surface_displacement"
        defo_var.coordinates = "time lat lon"
        defo_var.grid_mapping = "crs"

        # ------- Variable CRS (CF conventions) -------
        crs_var = ds.createVariable("crs", "i4")
        crs_var.grid_mapping_name = "latitude_longitude"
        crs_var.semi_major_axis = 6378137.0
        crs_var.inverse_flattening = 298.257223563
        crs_var.epsg_code = f"EPSG:{EPSG_CODE}"
        crs_var.crs_wkt = CRS_WKT

        # ------- Atributos globales -------
        ds.Conventions = "CF-1.8"
        ds.title = "Serie temporal DInSAR – Valle de Toluca"
        ds.source = "Sentinel-1 SLC, procesado con SNAP + MintPy SBAS"
        ds.history = f"Creado: {datetime.utcnow().isoformat()}Z"
        ds.institution = "SENTINEL InSAR Pipeline"
        ds.geospatial_lat_min = float(meta["lats"].min())
        ds.geospatial_lat_max = float(meta["lats"].max())
        ds.geospatial_lon_min = float(meta["lons"].min())
        ds.geospatial_lon_max = float(meta["lons"].max())
        ds.time_coverage_start = dates[0]
        ds.time_coverage_end = dates[-1]
        ds.epsg = EPSG_CODE

        # ------- Escritura por épocas (bloque a bloque) -------
        log.info("Escribiendo épocas en el cubo (chunk_time=%d)…", chunk_time)
        with h5py.File(ts_path, "r") as hf:
            ts_dset = hf["timeseries"]

            for i_start in range(0, n_t, chunk_time):
                i_end = min(i_start + chunk_time, n_t)
                chunk = ts_dset[i_start:i_end, :, :].astype(np.float32)
                # Reemplazar NaN codificados como 0 o valor de relleno
                nodata = float(hf["timeseries"].attrs.get("FILL_VALUE", 0.0))
                if nodata == 0.0:
                    # Sólo se aplica si hay un patrón claro de ceros en bordes
                    pass
                else:
                    chunk[chunk == nodata] = np.nan

                defo_var[i_start:i_end, :, :] = chunk

                del chunk
                gc.collect()

                if (i_start // chunk_time) % 10 == 0:
                    log.info(
                        "  Épocas escritas: %d/%d", i_end, n_t
                    )

    log.info("Hipercubo escrito: %s", cube_path)
    return cube_path


# ---------------------------------------------------------------------------
# Función auxiliar: acceso a un slice temporal
# ---------------------------------------------------------------------------

def get_epoch(cube_path: Path, date_str: str) -> np.ndarray:
    """
    Devuelve el array 2D de desplazamiento acumulado para una fecha dada.
    date_str: 'YYYY-MM-DD' o 'YYYYMMDD'
    """
    date_str = date_str.replace("-", "")
    target = datetime.strptime(date_str, "%Y%m%d")

    with nc.Dataset(str(cube_path), "r") as ds:
        # Buscar índice de tiempo
        t_units = ds["time"].units   # 'days since YYYYMMDD'
        t_origin_str = t_units.split("since ")[-1].strip().replace("-", "")
        t_origin = datetime.strptime(t_origin_str[:8], "%Y%m%d")
        target_day = (target - t_origin).days

        time_arr = ds["time"][:]
        idx = int(np.argmin(np.abs(time_arr - target_day)))
        found_day = int(time_arr[idx])
        found_date = t_origin + __import__("datetime").timedelta(days=found_day)
        log.info(
            "Fecha solicitada: %s → índice %d (fecha real: %s)",
            date_str,
            idx,
            found_date.strftime("%Y%m%d"),
        )
        epoch = ds["displacement"][idx, :, :]

    return np.array(epoch, dtype=np.float32)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    build_cube()
