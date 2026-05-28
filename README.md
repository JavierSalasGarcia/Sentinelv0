# Pipeline InSAR Sentinel-1 – Valle de Toluca

Pipeline automatizado para procesamiento de pares Sentinel-1 SLC (modo IW) y generación de mapas de deformación superficial mediante interferometría diferencial (DInSAR).

## Requisitos

| Componente | Versión mínima | Notas |
|---|---|---|
| ESA SNAP | 9.x | Incluye `snappy` (API Python) |
| Python | 3.9+ | Debe ser el Python vinculado a SNAP |
| SNAPHU | 1.4.2 | Debe estar en `PATH` |
| psutil | 5.9.0+ | `pip install psutil` |

## Estructura de archivos

```
Sentinelv0/
├── sentinel1_insar_toluca.py   # Script principal del pipeline DInSAR
├── config.py                   # Parámetros configurables (AOI, sub-swath, looks…)
├── requirements.txt
├── README.md
└── hipercubo/                  # Pipeline de series temporales SBAS + cubo 3D
    ├── run_pipeline.py         # Orquestador completo (punto de entrada)
    ├── dim_to_hdf5.py          # Etapa 1: BEAM-DIMAP → HDF5 por par
    ├── mintpy_sbas.py          # Etapa 2: red SBAS + inversión MintPy
    ├── build_hypercube.py      # Etapa 3: cubo 3D NetCDF-4 georreferenciado
    ├── validate_pair.py        # Validación: resta de épocas → GeoTIFF
    ├── requirements.txt        # Dependencias del módulo hipercubo
    └── README.md               # Documentación detallada del hipercubo
```

Todos los resultados del pipeline DInSAR se guardan en `D:/Toluca/`.  
Los resultados del hipercubo se guardan en `D:/Toluca/hipercubo/`.

## Flujo de trabajo

```
Split (IW/bursts) ──► Apply Orbit File ──► Back-Geocoding ──► ESD
                                                                │
                                                                ▼
                     Topo Phase Removal ◄── Deburst ◄── Interferogram + Coherence
                                │
                                ▼
            Multilook ──► Goldstein Filter ──► Subset (AOI Toluca)
                                                        │
                                                        ▼
                                              SNAPHU Unwrapping
                                                        │
                                                        ▼
                            Terrain Correction ◄── Phase → Displacement
                                    │
                                    ▼
                          Estadísticas + .dim final
```

## Nomenclatura de salida

```
{YYYYMMDD_master}_{YYYYMMDD_slave}_Stack_Ifg_Deb_DInSAR_ML_Flt_Sub_Unw_Disp_TC.dim
```

Ejemplo: `20200101_20200113_Stack_Ifg_Deb_DInSAR_ML_Flt_Sub_Unw_Disp_TC.dim`

## Área de interés (AOI)

| Parámetro | Valor |
|---|---|
| Latitud mín | 19°03′ N |
| Latitud máx | 19°35′ N |
| Longitud mín | 99°54′ O |
| Longitud máx | 99°19′ O |

## Uso

1. **Configurar pares de imágenes** en `sentinel1_insar_toluca.py`, sección `IMAGE_PAIRS`:

```python
IMAGE_PAIRS = [
    (
        "D:/data/S1A_IW_SLC__1SDV_20200101T120000_....zip",
        "D:/data/S1A_IW_SLC__1SDV_20200113T120000_....zip",
    ),
    # ... más pares
]
```

2. **Ajustar parámetros** en `config.py` (sub-swath, bursts, polarización, looks, etc.).

3. **Ejecutar**:

```bash
python sentinel1_insar_toluca.py
```

El progreso se registra en `D:/Toluca/insar_pipeline.log` y en consola.

---

## Módulo Hipercubo – Series temporales SBAS

Una vez generados los archivos `.dim` de desplazamiento, el módulo `hipercubo/` realiza la inversión SBAS con MintPy y construye un cubo 3D de deformación acumulada.

### Flujo hipercubo

```
*_Disp_TC.dim  (D:/Toluca/)
      ↓  dim_to_hdf5.py
mintpy_inputs/YYYYMMDD_YYYYMMDD.h5   ← desplazamiento + coherencia por par
      ↓  mintpy_sbas.py
mintpy_ts/ifgramStack.h5             ← stack SBAS (fase + coherencia)
mintpy_ts/timeseries.h5              ← serie temporal de deformación
      ↓  build_hypercube.py
hipercubo/deformation_cube.nc        ← cubo (X=Lon, Y=Lat, Z=Tiempo) [m]
      ↓  validate_pair.py
hipercubo/diff_YYYYMMDD_YYYYMMDD.tif ← diferencia entre 2 fechas (GeoTIFF)
```

### Estructura del cubo NetCDF-4

| Dimensión | Contenido |
|---|---|
| `time` | Días desde la primera adquisición |
| `lat`  | Latitud WGS-84 (19.05° – 19.58° N) |
| `lon`  | Longitud WGS-84 (−99.90° – −99.32° O) |
| `displacement` | Desplazamiento LOS acumulado [m] |

CRS: **EPSG:4326** (WGS-84), convención CF-1.8, compresión gzip.

### Requisitos adicionales

```bash
conda install -c conda-forge gdal netcdf4 h5py mintpy
```

### Uso del hipercubo

```bash
# Pipeline completo
python hipercubo/run_pipeline.py --toluca-dir D:/Toluca

# Validación: diferencia entre dos épocas → GeoTIFF
python hipercubo/validate_pair.py --date1 2019-08-31 --date2 2020-02-15
```

Ver `hipercubo/README.md` para documentación completa de cada módulo.

## Gestión de memoria

- Se verifica disponibilidad de al menos **8 GB de RAM libre** antes de cada par.
- Se llama a `product.dispose()` y `gc.collect()` tras cada etapa crítica.
- Si hay memoria insuficiente al inicio de un par, se espera 60 s y se reintenta; si persiste, se omite el par y continúa con el siguiente.

## Reanudación de lotes

Si el archivo `.dim` final de un par ya existe en `D:/Toluca/`, ese par se omite automáticamente, permitiendo reanudar un lote interrumpido.

## Personalización del sub-swath y bursts

El sub-swath y rango de bursts que cubren el Valle de Toluca dependen de la geometría de la pasada (órbita ascendente/descendente). Identificarlos con SNAP Desktop antes de ejecutar el batch y actualizar `config.py`:

```python
DEFAULT_SUBSWATH  = "IW2"   # sub-swath que cubre Toluca
DEFAULT_BURSTS_MASTER = "2,4"
DEFAULT_BURSTS_SLAVE  = "2,4"
```
