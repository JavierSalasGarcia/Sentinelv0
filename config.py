"""
Configuración centralizada del pipeline InSAR – Valle de Toluca.
Modifica este archivo para ajustar parámetros sin tocar la lógica principal.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------
OUTPUT_DIR = Path("D:/Toluca")

# ---------------------------------------------------------------------------
# Área de Interés – Valle de Toluca
# ---------------------------------------------------------------------------
# Latitud:  19°03′ N → 19°35′ N
# Longitud: 99°54′ O → 99°19′ O  (negativo en convenio Este/Oeste)
LAT_MIN: float = 19.050    # 19°03′  N
LAT_MAX: float = 19.583    # 19°35′  N
LON_MIN: float = -99.900   # 99°54′  O
LON_MAX: float = -99.317   # 99°19′  O

AOI_WKT: str = (
    f"POLYGON(({LON_MIN} {LAT_MIN}, {LON_MAX} {LAT_MIN}, "
    f"{LON_MAX} {LAT_MAX}, {LON_MIN} {LAT_MAX}, {LON_MIN} {LAT_MIN}))"
)

# ---------------------------------------------------------------------------
# Parámetros de adquisición Sentinel-1 IW SLC
# ---------------------------------------------------------------------------
DEFAULT_SUBSWATH: str = "IW1"       # IW1 / IW2 / IW3
DEFAULT_BURSTS_MASTER: str = "1,3"  # rango de bursts (primer_burst,último_burst)
DEFAULT_BURSTS_SLAVE: str = "1,3"
POLARIZATION: str = "VV"

# ---------------------------------------------------------------------------
# Parámetros de procesamiento
# ---------------------------------------------------------------------------

# Apply Orbit File
ORBIT_TYPE: str = "Sentinel Precise (Auto Download)"
ORBIT_POLY_DEGREE: int = 3

# Back-Geocoding
BG_DEM: str = "SRTM 3Sec"
BG_DEM_RESAMPLING: str = "BILINEAR_INTERPOLATION"

# Enhanced Spectral Diversity
ESD_WIN_W: int = 512
ESD_WIN_H: int = 512
ESD_COH_THRESHOLD: float = 0.3

# Interferogram
IFG_SRP_POLY_DEGREE: int = 5
IFG_SRP_NUM_POINTS: int = 501
IFG_ORBIT_DEGREE: int = 3
IFG_COH_WIN_AZ: int = 10
IFG_COH_WIN_RG: int = 10

# Topo Phase Removal
TPR_DEM: str = "SRTM 3Sec"

# Multilook
ML_RG_LOOKS: int = 4
ML_AZ_LOOKS: int = 1

# Goldstein Phase Filter
GPF_ALPHA: float = 0.8
GPF_FFT_SIZE: int = 32
GPF_WIN_SIZE: int = 3
GPF_COH_THRESHOLD: float = 0.2

# Terrain Correction
TC_DEM: str = "SRTM 3Sec"
TC_PIXEL_SPACING_M: float = 10.0

# ---------------------------------------------------------------------------
# SNAPHU
# ---------------------------------------------------------------------------
SNAPHU_BIN: str = "snaphu"   # binario en PATH, o ruta absoluta
SNAPHU_TIMEOUT_SEC: int = 7200  # 2 horas

# ---------------------------------------------------------------------------
# Gestión de memoria
# ---------------------------------------------------------------------------
MIN_FREE_RAM_BYTES: int = 8 * 1024 ** 3   # 8 GB
MEM_WAIT_SEC: int = 60                    # espera si RAM insuficiente
