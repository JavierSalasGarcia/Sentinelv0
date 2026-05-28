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
├── sentinel1_insar_toluca.py   # Script principal del pipeline
├── config.py                   # Parámetros configurables
├── requirements.txt
└── README.md
```

Todos los resultados se guardan en `D:/Toluca/`.

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
