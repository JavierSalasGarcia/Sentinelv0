# Hipercubo InSAR – Valle de Toluca

Pipeline para generar un cubo 3D de deformación superficial a partir de interferogramas procesados con SNAP+SNAPHU, usando MintPy SBAS.

## Estructura de archivos

```
hipercubo/
├── run_pipeline.py       # Orquestador completo (punto de entrada)
├── dim_to_hdf5.py        # Etapa 1: BEAM-DIMAP → HDF5
├── mintpy_sbas.py        # Etapa 2: Red SBAS + inversión MintPy
├── build_hypercube.py    # Etapa 3: Cubo 3D NetCDF-4
├── validate_pair.py      # Etapa 5: Validación diferencia → GeoTIFF
└── requirements.txt
```

## Flujo completo

```
D:/Toluca/*_Disp_TC.dim
         │
         ▼  [dim_to_hdf5.py]
D:/Toluca/mintpy_inputs/YYYYMMDD_YYYYMMDD.h5  (uno por par)
         │
         ▼  [mintpy_sbas.py]
D:/Toluca/mintpy_ts/ifgramStack.h5    ← stack de interferogramas
D:/Toluca/mintpy_ts/timeseries.h5     ← serie temporal SBAS (MintPy)
         │
         ▼  [build_hypercube.py]
D:/Toluca/hipercubo/deformation_cube.nc
         │  (X=Lon, Y=Lat, Z=Tiempo, valor=desplazamiento acumulado [m])
         │
         ▼  [validate_pair.py]
D:/Toluca/hipercubo/diff_20190831_20200215.tif
```

## Requisitos

```
conda create -n insar python=3.10
conda activate insar
conda install -c conda-forge gdal netcdf4 h5py numpy psutil mintpy
```

> **snappy** se configura aparte al instalar ESA SNAP (ver README raíz).

## Uso

### Pipeline completo
```bash
python run_pipeline.py --toluca-dir D:/Toluca
```

### Etapas individuales
```bash
# Solo conversión
python dim_to_hdf5.py

# Solo inversión SBAS (requiere HDF5 de conversión)
python mintpy_sbas.py

# Solo cubo (requiere timeseries.h5)
python build_hypercube.py

# Validación: diferencia entre dos fechas → GeoTIFF
python validate_pair.py --date1 2019-08-31 --date2 2020-02-15
```

### Opciones de run_pipeline.py
```
--toluca-dir    Directorio raíz (default: D:/Toluca)
--skip-conversion   Omite conversión DIMAP→HDF5
--skip-inversion    Omite la inversión SBAS
--skip-cube         Omite la construcción del cubo
```

## Producto final – deformation_cube.nc

Cubo NetCDF-4 con estructura CF-1.8:

| Dimensión | Contenido |
|---|---|
| `time` | Días desde la primera adquisición |
| `lat`  | Latitud WGS-84 (19.05° – 19.58° N) |
| `lon`  | Longitud WGS-84 (−99.90° – −99.32° O) |
| `displacement` | Desplazamiento LOS acumulado [m] |

- CRS: EPSG:4326 (WGS-84)
- Compresión: gzip nivel 4
- Chunks: `(1, 512, 512)` para acceso eficiente por época

## Gestión de memoria

- Conversión: lectura por bloques de 512 filas; `gc.collect()` por par.
- Construcción del cubo: escritura época a época (`chunk_time=1`).
- No se carga nunca más de un slice temporal completo en RAM.
- Verificación de RAM libre (≥ 6 GB) antes de cada etapa.

## Validación

```bash
python validate_pair.py --date1 2019-08-31 --date2 2020-02-15
```

Genera `diff_20190831_20200215.tif` (Float32, EPSG:4326, LZW) listo para
comparar con la figura del artículo en QGIS o cualquier SIG.

### Ejemplo de estadísticas impresas
```
Píxeles válidos : 1 245 830
Mínimo         : -0.0842 m
Máximo         :  0.0213 m
Media          : -0.0124 m
Desv. estándar :  0.0088 m
Rango IQR      : -0.0178 – -0.0071 m
```
