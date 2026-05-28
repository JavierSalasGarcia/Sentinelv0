"""
Pipeline InSAR automatizado para Sentinel-1 SLC – Valle de Toluca
Flujo: Split → AOF → Back-Geocoding → ESD →
       Interferogram → Coherence → Deburst → TopoPhaseRemoval →
       Multilook → GoldsteinFilter → Subset → SNAPHU Unwrapping →
       Phase2Displacement → TerrainCorrection → Statistics
Salida: BEAM-DIMAP en D:/Toluca/
"""

import gc
import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import psutil

# ---------------------------------------------------------------------------
# Configuración de logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("D:/Toluca/insar_pipeline.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Importación de snappy (ESA SNAP Python API)
# ---------------------------------------------------------------------------
try:
    from snappy import (
        GPF,
        HashMap,
        Product,
        ProductIO,
        ProductSubsetDef,
    )
    from snappy import jpy  # Java-Python bridge

    GPF.getDefaultInstance().getOperatorSpiRegistry().loadOperatorSpis()
    log.info("snappy cargado correctamente.")
except ImportError as exc:
    log.critical(
        "No se pudo importar snappy. Asegúrese de que ESA SNAP y "
        "snappy estén correctamente instalados. Detalle: %s", exc
    )
    sys.exit(1)

# ---------------------------------------------------------------------------
# Constantes globales
# ---------------------------------------------------------------------------
OUTPUT_DIR = Path("D:/Toluca")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Coordenadas del Valle de Toluca
LAT_MIN = 19.05   # 19°03′ N
LAT_MAX = 19.583  # 19°35′ N
LON_MIN = -99.90  # 99°54′ O  → valor negativo para referencia oeste
LON_MAX = -99.317 # 99°19′ O

# WKT del área de interés (usado por operadores SNAP que aceptan WKT)
AOI_WKT = (
    f"POLYGON(({LON_MIN} {LAT_MIN}, {LON_MAX} {LAT_MIN}, "
    f"{LON_MAX} {LAT_MAX}, {LON_MIN} {LAT_MAX}, {LON_MIN} {LAT_MIN}))"
)

# Parámetros de sub-swath por defecto (ajustar según geometría real)
DEFAULT_SUBSWATH = "IW1"
DEFAULT_BURSTS_MASTER = "1,2,3"
DEFAULT_BURSTS_SLAVE = "1,2,3"
POLARIZATION = "VV"

# Parámetros Multilook
ML_RG_LOOKS = 4
ML_AZ_LOOKS = 1

# Umbral mínimo de RAM disponible antes de procesar un nuevo par (bytes)
MIN_FREE_RAM_BYTES = 8 * 1024 ** 3  # 8 GB

SNAPHU_BIN = "snaphu"  # debe estar en PATH o especificar ruta completa
SNAPHU_VERSION = "1.4.2"


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def _params(**kwargs) -> HashMap:
    """Construye un HashMap de parámetros para GPF."""
    p = HashMap()
    for k, v in kwargs.items():
        p.put(k, str(v))
    return p


def _save(product: Product, name: str) -> Path:
    """Guarda un producto como BEAM-DIMAP y devuelve su ruta."""
    path = OUTPUT_DIR / name
    ProductIO.writeProduct(product, str(path), "BEAM-DIMAP")
    log.info("Guardado: %s.dim", path)
    return path.with_suffix(".dim")


def _dispose(*products):
    """Cierra productos SNAP y fuerza recolección de basura."""
    for p in products:
        if p is not None:
            try:
                p.dispose()
            except Exception:
                pass
    gc.collect()


def check_free_memory(min_bytes: int = MIN_FREE_RAM_BYTES) -> None:
    """Lanza RuntimeError si la RAM disponible es insuficiente."""
    free = psutil.virtual_memory().available
    free_gb = free / 1024 ** 3
    log.info("RAM disponible: %.1f GB", free_gb)
    if free < min_bytes:
        raise RuntimeError(
            f"Memoria insuficiente: {free_gb:.1f} GB disponibles, "
            f"se requieren al menos {min_bytes / 1024**3:.0f} GB."
        )


def _extract_date(slc_path: str) -> str:
    """Extrae la fecha de adquisición del nombre de archivo SLC (YYYYMMDD)."""
    name = Path(slc_path).stem
    for part in name.split("_"):
        if len(part) >= 8 and part[:8].isdigit():
            return part[:8]
    raise ValueError(f"No se pudo extraer fecha de: {slc_path}")


# ---------------------------------------------------------------------------
# Etapa 1: Pre-procesamiento
# ---------------------------------------------------------------------------

def stage1_preprocessing(
    master_path: str,
    slave_path: str,
    subswath: str = DEFAULT_SUBSWATH,
    bursts_master: str = DEFAULT_BURSTS_MASTER,
    bursts_slave: str = DEFAULT_BURSTS_SLAVE,
    polarization: str = POLARIZATION,
) -> Product:
    """
    Split → Apply Orbit File → Back-Geocoding → Enhanced Spectral Diversity.
    Devuelve el producto apilado con ESD aplicado.
    """
    log.info("=== Etapa 1: Pre-procesamiento ===")

    # -- 1a. Lectura de imágenes --
    log.info("Leyendo master: %s", master_path)
    master_raw = ProductIO.readProduct(master_path)
    log.info("Leyendo slave: %s", slave_path)
    slave_raw = ProductIO.readProduct(slave_path)

    # -- 1b. Split (sub-swath y bursts) --
    log.info("Split master (sub-swath=%s, bursts=%s)", subswath, bursts_master)
    master_split = GPF.createProduct(
        "TOPSAR-Split",
        _params(
            subswath=subswath,
            selectedPolarisations=polarization,
            firstBurstIndex=bursts_master.split(",")[0],
            lastBurstIndex=bursts_master.split(",")[-1],
        ),
        master_raw,
    )

    log.info("Split slave (sub-swath=%s, bursts=%s)", subswath, bursts_slave)
    slave_split = GPF.createProduct(
        "TOPSAR-Split",
        _params(
            subswath=subswath,
            selectedPolarisations=polarization,
            firstBurstIndex=bursts_slave.split(",")[0],
            lastBurstIndex=bursts_slave.split(",")[-1],
        ),
        slave_raw,
    )

    _dispose(master_raw, slave_raw)

    # -- 1c. Apply Orbit File --
    log.info("Apply Orbit File: master")
    master_aof = GPF.createProduct(
        "Apply-Orbit-File",
        _params(
            orbitType="Sentinel Precise (Auto Download)",
            polyDegree=3,
            continueOnFail=False,
        ),
        master_split,
    )

    log.info("Apply Orbit File: slave")
    slave_aof = GPF.createProduct(
        "Apply-Orbit-File",
        _params(
            orbitType="Sentinel Precise (Auto Download)",
            polyDegree=3,
            continueOnFail=False,
        ),
        slave_split,
    )

    _dispose(master_split, slave_split)

    # -- 1d. Back-Geocoding (corregistración con SRTM) --
    log.info("Back-Geocoding (SRTM 3Sec)")
    stack = GPF.createProduct(
        "Back-Geocoding",
        _params(
            demName="SRTM 3Sec",
            demResamplingMethod="BILINEAR_INTERPOLATION",
            resamplingType="BILINEAR_INTERPOLATION",
            maskOutAreaWithoutElevation=True,
            outputRangeAzimuthOffset=True,
            outputDerampDemodPhase=False,
            disableReramp=False,
        ),
        [master_aof, slave_aof],
    )

    _dispose(master_aof, slave_aof)

    # -- 1e. Enhanced Spectral Diversity --
    log.info("Enhanced Spectral Diversity")
    stack_esd = GPF.createProduct(
        "Enhanced-Spectral-Diversity",
        _params(
            fineWinWidthStr=512,
            fineWinHeightStr=512,
            fineWinAccAzimuth=16,
            fineWinAccRange=16,
            fineWinOversampling=128,
            xCorrThreshold=0.1,
            cohThreshold=0.3,
            numBlocksPerOverlap=10,
            useSuppliedRangeShift=False,
            useSuppliedAzimuthShift=False,
        ),
        stack,
    )

    _dispose(stack)
    gc.collect()
    log.info("Etapa 1 completada.")
    return stack_esd


# ---------------------------------------------------------------------------
# Etapa 2: Generación de Interferograma
# ---------------------------------------------------------------------------

def stage2_interferogram(stack_esd: Product) -> Product:
    """
    Interferogram → Coherence → Deburst → Topo Phase Removal.
    Devuelve el interferograma sin fase topográfica.
    """
    log.info("=== Etapa 2: Generación de Interferograma ===")

    # -- 2a. Interferograma (producto cruzado conjugado) --
    log.info("Creando Interferograma")
    ifg = GPF.createProduct(
        "Interferogram",
        _params(
            subtractFlatEarthPhase=True,
            srpPolynomialDegree=5,
            srpNumberPoints=501,
            orbitDegree=3,
            includeCoherence=True,
            cohWinAz=10,
            cohWinRg=10,
            squarePixel=True,
        ),
        stack_esd,
    )

    _dispose(stack_esd)

    # -- 2b. Deburst --
    log.info("Deburst")
    ifg_deb = GPF.createProduct(
        "TOPSAR-Deburst",
        _params(selectedPolarisations=POLARIZATION),
        ifg,
    )

    _dispose(ifg)

    # -- 2c. Topo Phase Removal (eliminación de fase topográfica con SRTM) --
    log.info("Topo Phase Removal (SRTM 3Sec)")
    ifg_dinsar = GPF.createProduct(
        "TopoPhaseRemoval",
        _params(
            demName="SRTM 3Sec",
            orbitDegree=3,
            demInterpolation="BILINEAR_INTERPOLATION",
            outputTopoPhaseBand=False,
            outputElevationBand=False,
            outputLatLonBands=False,
        ),
        ifg_deb,
    )

    _dispose(ifg_deb)
    gc.collect()
    log.info("Etapa 2 completada.")
    return ifg_dinsar


# ---------------------------------------------------------------------------
# Etapa 3: Filtrado y Unwrapping (fase envuelta → desenvuelta)
# ---------------------------------------------------------------------------

def stage3_filter_and_unwrap(
    ifg_dinsar: Product,
    date_master: str,
    date_slave: str,
) -> Path:
    """
    Multilook → Goldstein Filter → Subset → exportación → SNAPHU → importación.
    Devuelve la ruta del producto unwrapped (.dim).
    """
    log.info("=== Etapa 3: Filtrado y Unwrapping ===")

    # -- 3a. Multilook --
    log.info("Multilook (rg=%d, az=%d)", ML_RG_LOOKS, ML_AZ_LOOKS)
    ml = GPF.createProduct(
        "Multilook",
        _params(
            nRgLooks=ML_RG_LOOKS,
            nAzLooks=ML_AZ_LOOKS,
            outputIntensity=False,
            grSquarePixel=True,
        ),
        ifg_dinsar,
    )

    _dispose(ifg_dinsar)

    # -- 3b. Goldstein Phase Filtering --
    log.info("Goldstein Phase Filtering")
    flt = GPF.createProduct(
        "GoldsteinPhaseFiltering",
        _params(
            alpha=0.8,
            FFTSizeString=32,
            windowSizeString=3,
            useCoherenceMask=True,
            coherenceThreshold=0.2,
        ),
        ml,
    )

    _dispose(ml)

    # -- 3c. Subset al área de interés --
    log.info("Subset al AOI (Toluca)")
    subset_def = ProductSubsetDef()
    subset_def.setRegion(0, 0, flt.getSceneRasterWidth(), flt.getSceneRasterHeight())

    flt_sub = GPF.createProduct(
        "Subset",
        _params(
            geoRegion=AOI_WKT,
            copyMetadata=True,
        ),
        flt,
    )

    _dispose(flt)
    gc.collect()

    # -- 3d. Exportar para SNAPHU --
    snaphu_export_name = f"{date_master}_{date_slave}_snaphu_export"
    snaphu_export_path = OUTPUT_DIR / snaphu_export_name
    log.info("Exportando para SNAPHU: %s", snaphu_export_path)
    ProductIO.writeProduct(flt_sub, str(snaphu_export_path), "SnaphuExport")
    _dispose(flt_sub)
    gc.collect()

    # -- 3e. Invocar SNAPHU v1.4.2 --
    unwrapped_path = _run_snaphu(snaphu_export_path, date_master, date_slave)

    # -- 3f. Importar resultado de SNAPHU --
    log.info("Importando resultado de SNAPHU")
    snaphu_import_name = f"{date_master}_{date_slave}_Stack_Ifg_Deb_DInSAR_ML_Flt_Sub_Unw"
    unw_product = _snaphu_import(
        snaphu_export_path, unwrapped_path, snaphu_import_name
    )
    out_path = _save(unw_product, snaphu_import_name)
    _dispose(unw_product)
    gc.collect()

    log.info("Etapa 3 completada.")
    return out_path


def _run_snaphu(export_dir: Path, date_master: str, date_slave: str) -> Path:
    """
    Lee el archivo de configuración generado por SnaphuExport y ejecuta
    SNAPHU v1.4.2 mediante subprocess. Devuelve la ruta del archivo unwrapped.
    """
    # El operador SnaphuExport de SNAP genera un archivo .conf con los parámetros
    conf_files = list(export_dir.glob("*.conf")) if export_dir.is_dir() else []
    if not conf_files:
        # Intentar buscar en subdirectorio
        conf_files = list(export_dir.parent.glob(f"{export_dir.stem}*/*.conf"))
    if not conf_files:
        raise FileNotFoundError(
            f"No se encontró archivo .conf de SNAPHU en {export_dir}"
        )
    conf_file = conf_files[0]
    log.info("Archivo de configuración SNAPHU: %s", conf_file)

    # Leer la línea que indica el nombre del archivo de fase envuelta
    phase_file: Optional[Path] = None
    unw_file: Optional[Path] = None
    with open(conf_file, "r") as f:
        for line in f:
            line = line.strip()
            if line.startswith("INFILE") and not line.startswith("INFILEFORMAT"):
                phase_file = conf_file.parent / line.split()[-1]
            if line.startswith("OUTFILE") and not line.startswith("OUTFILEFORMAT"):
                unw_file = conf_file.parent / line.split()[-1]

    if phase_file is None or unw_file is None:
        raise ValueError(
            "No se pudieron leer INFILE/OUTFILE del archivo de configuración SNAPHU."
        )

    cmd = [SNAPHU_BIN, "-f", str(conf_file), str(phase_file)]
    log.info("Ejecutando SNAPHU: %s", " ".join(cmd))

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(conf_file.parent),
        timeout=7200,  # 2 horas máximo
    )

    if result.returncode != 0:
        log.error("SNAPHU stderr:\n%s", result.stderr)
        raise RuntimeError(
            f"SNAPHU finalizó con código {result.returncode}. "
            f"Revisar log para detalles."
        )

    log.info("SNAPHU completado exitosamente.")
    log.debug("SNAPHU stdout:\n%s", result.stdout)
    return unw_file


def _snaphu_import(
    export_dir: Path, unwrapped_file: Path, output_name: str
) -> Product:
    """Importa el resultado de SNAPHU usando el operador SnaphuImport."""
    # El producto de referencia es el exportado (contiene metadatos)
    ref_product = ProductIO.readProduct(
        str(next(export_dir.parent.glob(f"{export_dir.stem}*.dim"), export_dir))
    )
    unw_product = GPF.createProduct(
        "SnaphuImport",
        _params(
            doNotKeepWrappedPhase=True,
            targetBandName=f"Phase_ifg_{POLARIZATION}",
        ),
        [ref_product, ProductIO.readProduct(str(unwrapped_file))],
    )
    ref_product.dispose()
    return unw_product


# ---------------------------------------------------------------------------
# Etapa 4: Finalización (fase → desplazamiento → corrección terrain)
# ---------------------------------------------------------------------------

def stage4_finalization(
    unw_dim_path: Path,
    date_master: str,
    date_slave: str,
) -> Path:
    """
    Phase to Displacement → Terrain Correction → Statistics.
    Devuelve la ruta del producto final .dim.
    """
    log.info("=== Etapa 4: Finalización ===")

    unw_product = ProductIO.readProduct(str(unw_dim_path))

    # -- 4a. Phase to Displacement (metros) --
    log.info("Phase to Displacement")
    disp = GPF.createProduct(
        "PhaseToDisplacement",
        _params(),
        unw_product,
    )

    _dispose(unw_product)

    # -- 4b. Terrain Correction (SRTM) --
    log.info("Terrain Correction (Range-Doppler, SRTM 3Sec)")
    tc = GPF.createProduct(
        "Terrain-Correction",
        _params(
            demName="SRTM 3Sec",
            demResamplingMethod="BILINEAR_INTERPOLATION",
            imgResamplingMethod="BILINEAR_INTERPOLATION",
            pixelSpacingInMeter=10.0,
            mapProjection="AUTO:42001",
            nodataValueAtSea=False,
            saveDEM=False,
            saveLatLon=False,
            saveIncidenceAngleFromEllipsoid=False,
            saveLocalIncidenceAngle=False,
            saveProjectedLocalIncidenceAngle=False,
            saveSelectedSourceBand=True,
        ),
        disp,
    )

    _dispose(disp)

    # -- 4c. Guardar producto final --
    final_name = f"{date_master}_{date_slave}_Stack_Ifg_Deb_DInSAR_ML_Flt_Sub_Unw_Disp_TC"
    final_path = _save(tc, final_name)

    # -- 4d. Estadísticas de coherencia y desplazamiento --
    _compute_statistics(tc, date_master, date_slave)
    _dispose(tc)
    gc.collect()

    log.info("Etapa 4 completada. Producto final: %s", final_path)
    return final_path


def _compute_statistics(product: Product, date_master: str, date_slave: str) -> None:
    """Calcula y registra estadísticas básicas de coherencia y desplazamiento."""
    stats_path = OUTPUT_DIR / f"{date_master}_{date_slave}_statistics.txt"
    lines = [
        f"Par InSAR: {date_master} / {date_slave}",
        f"Generado: {datetime.now().isoformat()}",
        "",
    ]
    band_names = list(product.getBandNames())
    for band_name in band_names:
        band = product.getBand(band_name)
        if band is None:
            continue
        # Forzar cálculo de estadísticas
        band.loadRasterData()
        stats = band.getStx(True, None)
        if stats is not None:
            lines.append(
                f"Banda: {band_name}  |  "
                f"Min={stats.getMin():.6f}  "
                f"Max={stats.getMax():.6f}  "
                f"Media={stats.getMean():.6f}  "
                f"StdDev={stats.getStandardDeviation():.6f}"
            )
    with open(stats_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    log.info("Estadísticas guardadas: %s", stats_path)


# ---------------------------------------------------------------------------
# Pipeline completo para un par master/slave
# ---------------------------------------------------------------------------

def process_pair(
    master_path: str,
    slave_path: str,
    subswath: str = DEFAULT_SUBSWATH,
    bursts_master: str = DEFAULT_BURSTS_MASTER,
    bursts_slave: str = DEFAULT_BURSTS_SLAVE,
    polarization: str = POLARIZATION,
) -> Optional[Path]:
    """
    Ejecuta el pipeline InSAR completo para un par de imágenes SLC.
    Devuelve la ruta del producto final o None si hubo error.
    """
    date_master = _extract_date(master_path)
    date_slave = _extract_date(slave_path)
    pair_id = f"{date_master}_{date_slave}"
    log.info("╔══════════════════════════════════════════════════╗")
    log.info("  Procesando par: %s → %s", date_master, date_slave)
    log.info("╚══════════════════════════════════════════════════╝")

    # Verificar archivo final previo (reanudar si ya existe)
    final_name = f"{pair_id}_Stack_Ifg_Deb_DInSAR_ML_Flt_Sub_Unw_Disp_TC.dim"
    if (OUTPUT_DIR / final_name).exists():
        log.info("Par %s ya procesado. Saltando.", pair_id)
        return OUTPUT_DIR / final_name

    check_free_memory()

    try:
        # Etapa 1
        stack_esd = stage1_preprocessing(
            master_path, slave_path, subswath, bursts_master, bursts_slave, polarization
        )

        # Etapa 2
        ifg_dinsar = stage2_interferogram(stack_esd)

        # Etapa 3
        unw_dim = stage3_filter_and_unwrap(ifg_dinsar, date_master, date_slave)

        # Etapa 4
        final_path = stage4_finalization(unw_dim, date_master, date_slave)

        log.info("Par %s procesado correctamente: %s", pair_id, final_path)
        return final_path

    except Exception as exc:
        log.exception("Error procesando par %s: %s", pair_id, exc)
        gc.collect()
        return None


# ---------------------------------------------------------------------------
# Procesamiento por lotes
# ---------------------------------------------------------------------------

def run_batch(
    pairs: list[tuple[str, str]],
    subswath: str = DEFAULT_SUBSWATH,
    bursts_master: str = DEFAULT_BURSTS_MASTER,
    bursts_slave: str = DEFAULT_BURSTS_SLAVE,
    polarization: str = POLARIZATION,
) -> dict[str, Optional[Path]]:
    """
    Procesa una lista de pares (master_path, slave_path) en secuencia.
    Retorna un diccionario {par_id: ruta_final_o_None}.
    """
    results: dict[str, Optional[Path]] = {}
    total = len(pairs)

    for idx, (master_path, slave_path) in enumerate(pairs, start=1):
        date_m = _extract_date(master_path)
        date_s = _extract_date(slave_path)
        pair_id = f"{date_m}_{date_s}"
        log.info("─── Par %d/%d: %s ───", idx, total, pair_id)

        # Verificar RAM antes de cada par
        try:
            check_free_memory()
        except RuntimeError as mem_err:
            log.warning(
                "Memoria insuficiente para iniciar par %s. Esperando 60s. %s",
                pair_id, mem_err
            )
            time.sleep(60)
            try:
                check_free_memory()
            except RuntimeError:
                log.error("Memoria aún insuficiente. Saltando par %s.", pair_id)
                results[pair_id] = None
                continue

        result = process_pair(
            master_path, slave_path, subswath, bursts_master, bursts_slave, polarization
        )
        results[pair_id] = result

        # Limpieza agresiva entre pares
        gc.collect()

    # Resumen final
    ok = sum(1 for v in results.values() if v is not None)
    fail = total - ok
    log.info("═══ Resumen: %d/%d pares completados, %d fallidos ═══", ok, total, fail)
    for pid, path in results.items():
        status = "OK" if path else "FAIL"
        log.info("  [%s] %s → %s", status, pid, path or "—")

    return results


# ---------------------------------------------------------------------------
# Punto de entrada
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # -----------------------------------------------------------------------
    # Definir aquí los pares a procesar.
    # Cada elemento es (ruta_master_SLC.zip, ruta_slave_SLC.zip).
    # Las rutas deben apuntar a los archivos .zip o .SAFE descargados de
    # Copernicus Open Access Hub / Alaska Satellite Facility.
    # -----------------------------------------------------------------------
    IMAGE_PAIRS: list[tuple[str, str]] = [
        # Ejemplo:
        # (
        #     "D:/data/S1A_IW_SLC__1SDV_20200101T000000_....zip",
        #     "D:/data/S1A_IW_SLC__1SDV_20200113T000000_....zip",
        # ),
    ]

    if not IMAGE_PAIRS:
        log.error(
            "No hay pares definidos. Edite la lista IMAGE_PAIRS en __main__ "
            "antes de ejecutar el script."
        )
        sys.exit(1)

    run_batch(
        IMAGE_PAIRS,
        subswath=DEFAULT_SUBSWATH,
        bursts_master=DEFAULT_BURSTS_MASTER,
        bursts_slave=DEFAULT_BURSTS_SLAVE,
        polarization=POLARIZATION,
    )
