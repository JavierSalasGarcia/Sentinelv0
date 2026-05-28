# Guía de Descarga de Imágenes Sentinel-1 SLC – Valle de Toluca

Esta guía cubre el registro en los portales de datos, la búsqueda y descarga
de imágenes Sentinel-1 SLC aptas para el procesamiento InSAR, y la organización
de archivos que requiere el pipeline.

---

## 1. Portales de descarga disponibles

| Portal | URL | Ventaja principal |
|---|---|---|
| **Copernicus Data Space** (recomendado) | `dataspace.copernicus.eu` | Acceso directo, descarga gratuita, API REST |
| **Alaska Satellite Facility (ASF)** | `search.asf.alaska.edu` | Interfaz gráfica intuitiva, filtros InSAR integrados |
| **Copernicus Browser** | `browser.dataspace.copernicus.eu` | Visualización rápida antes de descargar |

> El antiguo portal **SciHub** (scihub.copernicus.eu) fue **retirado en mayo 2023**
> y ya no está disponible. Usar exclusivamente Copernicus Data Space o ASF.

---

## 2. Registro en Copernicus Data Space (portal principal)

### 2.1 Crear cuenta

1. Ir a `https://dataspace.copernicus.eu`
2. Hacer clic en **"Register"** (esquina superior derecha)
3. Completar el formulario:
   - Nombre y apellidos
   - Correo electrónico institucional o personal
   - Contraseña (mínimo 8 caracteres, una mayúscula y un número)
   - País de residencia
   - Uso previsto (seleccionar *"Scientific Research"*)
4. Aceptar los **Términos y Condiciones** de uso de datos Copernicus
5. Hacer clic en **"Register"**
6. Revisar el correo electrónico y hacer clic en el enlace de **verificación**

### 2.2 Verificar acceso

- Iniciar sesión en `https://dataspace.copernicus.eu`
- En el panel de usuario confirmar que el estado es **"Active"**
- Las mismas credenciales funcionan para el **Copernicus Browser** y la **API**

---

## 3. Registro en Alaska Satellite Facility (alternativo)

1. Ir a `https://search.asf.alaska.edu`
2. Hacer clic en **"Sign In"** → **"Register"**
3. Crear cuenta NASA EarthData:
   - Ir a `https://urs.earthdata.nasa.gov/users/new`
   - Completar usuario, contraseña y correo
   - En *"Affiliations"* seleccionar el tipo de organización
   - Aceptar términos y enviar
4. Volver a ASF y vincular la cuenta EarthData
5. Aceptar los acuerdos de datos específicos de Sentinel-1

---

## 4. Parámetros de búsqueda para el Valle de Toluca

Antes de buscar, identificar la geometría correcta:

| Parámetro | Valor |
|---|---|
| Sensor | Sentinel-1A o Sentinel-1B |
| Modo de adquisición | **IW** (Interferometric Wide Swath) |
| Nivel de procesamiento | **SLC** (Single Look Complex) |
| Polarización | **VV+VH** (dual-pol) o **VV** |
| Latitud | 19.05° – 19.58° N |
| Longitud | −99.90° – −99.32° (99°54′ – 99°19′ O) |
| Órbita | Relativa **143** (ascendente) o **56** (descendente) — verificar cobertura |
| Intervalo temporal | 12 días (ciclo de revisita de S-1) |
| Baseline temporal máximo recomendado | 180 días (para SBAS) |

> **Nota sobre la órbita:** Para el Valle de Toluca, la **órbita 143 ascendente**
> suele ofrecer mejor cobertura. Confirmar con la primera búsqueda visual.

---

## 5. Búsqueda y descarga en Copernicus Data Space

### 5.1 Usando el Copernicus Browser (interfaz gráfica)

1. Ir a `https://browser.dataspace.copernicus.eu`
2. Iniciar sesión con las credenciales del paso 2
3. En el panel izquierdo:
   - **"Search"** → seleccionar **"Sentinel-1"**
   - Tipo de colección: **"S1_SLC_IW"**
4. En el mapa:
   - Hacer zoom hasta el **Valle de Toluca** (Estado de México, México)
   - Dibujar el área de interés con la herramienta **"Draw area"** (polígono o rectángulo)
   - Coordenadas a cubrir: 19.05°N–19.58°N / 99.90°O–99.32°O
5. Filtros de fecha:
   - Establecer rango temporal de interés (p. ej. `2019-01-01` a `2021-12-31`)
6. Hacer clic en **"Search"**
7. En los resultados, verificar:
   - Que el modo sea **IW**
   - Que el nivel sea **SLC**
   - Que la huella cubra completamente el área de Toluca
8. Para cada imagen de interés:
   - Hacer clic en el ícono de **descarga** (nube con flecha)
   - Si aparece *"Offline"*, hacer clic en **"Order"** y esperar la restauración
     (puede tardar de minutos a horas)

### 5.2 Usando la API REST (descarga masiva recomendada)

Requiere obtener primero un token de autenticación:

```bash
# Obtener token de acceso
curl -s -X POST "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password" \
  -d "client_id=cdse-public" \
  -d "username=TU_EMAIL@ejemplo.com" \
  -d "password=TU_CONTRASEÑA" \
  | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])"
```

Guardar el token en una variable de entorno:

```bash
export CDSE_TOKEN="<token_obtenido_arriba>"
```

Buscar imágenes SLC en el área de Toluca:

```bash
curl -s "https://catalogue.dataspace.copernicus.eu/odata/v1/Products?\
\$filter=Collection/Name eq 'SENTINEL-1' \
and Attributes/OData.CSC.StringAttribute/any(att:att/Name eq 'productType' and att/OData.CSC.StringAttribute/Value eq 'IW_SLC__1S') \
and OData.CSC.Intersects(area=geography'SRID=4326;POLYGON((-99.90 19.05,-99.32 19.05,-99.32 19.58,-99.90 19.58,-99.90 19.05))') \
and ContentDate/Start gt 2019-01-01T00:00:00.000Z \
and ContentDate/Start lt 2022-01-01T00:00:00.000Z\
&\$orderby=ContentDate/Start asc\
&\$top=100\
&\$expand=Attributes" \
| python -m json.tool > resultados_toluca.json
```

Descargar una imagen por su ID:

```bash
# Reemplazar {PRODUCT_ID} con el Id obtenido del JSON anterior
curl -L \
  -H "Authorization: Bearer $CDSE_TOKEN" \
  "https://zipper.dataspace.copernicus.eu/odata/v1/Products({PRODUCT_ID})/\$value" \
  --output "S1A_IW_SLC_FECHA.zip"
```

### 5.3 Script de descarga masiva (Python)

```python
"""
Descarga imágenes Sentinel-1 SLC para el Valle de Toluca
desde Copernicus Data Space Ecosystem (CDSE).
Guardar como: download_sentinel1.py
"""
import json
import os
import sys
import time
from pathlib import Path

import requests

EMAIL    = "TU_EMAIL@ejemplo.com"       # reemplazar
PASSWORD = "TU_CONTRASEÑA"              # reemplazar

RAW_DIR  = Path("D:/data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)

AOI_WKT = "POLYGON((-99.90 19.05,-99.32 19.05,-99.32 19.58,-99.90 19.58,-99.90 19.05))"
DATE_START = "2019-01-01T00:00:00.000Z"
DATE_END   = "2022-01-01T00:00:00.000Z"
MAX_RESULTS = 200


def get_token(email: str, password: str) -> str:
    r = requests.post(
        "https://identity.dataspace.copernicus.eu/auth/realms/CDSE"
        "/protocol/openid-connect/token",
        data={
            "grant_type": "password",
            "client_id": "cdse-public",
            "username": email,
            "password": password,
        },
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["access_token"]


def search_products(token: str) -> list[dict]:
    url = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"
    params = {
        "$filter": (
            "Collection/Name eq 'SENTINEL-1' "
            "and Attributes/OData.CSC.StringAttribute/any("
            "  att:att/Name eq 'productType' "
            "  and att/OData.CSC.StringAttribute/Value eq 'IW_SLC__1S') "
            f"and OData.CSC.Intersects(area=geography'SRID=4326;{AOI_WKT}') "
            f"and ContentDate/Start gt {DATE_START} "
            f"and ContentDate/Start lt {DATE_END}"
        ),
        "$orderby": "ContentDate/Start asc",
        "$top": MAX_RESULTS,
        "$expand": "Attributes",
    }
    r = requests.get(url, params=params, headers={"Authorization": f"Bearer {token}"}, timeout=60)
    r.raise_for_status()
    return r.json().get("value", [])


def download(product: dict, token: str) -> None:
    pid  = product["Id"]
    name = product["Name"]
    dest = RAW_DIR / f"{name}.zip"

    if dest.exists():
        print(f"  Ya existe: {name}")
        return

    print(f"  Descargando: {name}")
    url = f"https://zipper.dataspace.copernicus.eu/odata/v1/Products({pid})/$value"

    for attempt in range(4):
        try:
            with requests.get(
                url,
                headers={"Authorization": f"Bearer {token}"},
                stream=True,
                timeout=300,
            ) as r:
                if r.status_code == 202:
                    print(f"    Producto offline, esperando restauración…")
                    time.sleep(60 * (attempt + 1))
                    continue
                r.raise_for_status()
                with open(dest, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            print(f"  Guardado: {dest}")
            return
        except Exception as exc:
            wait = 2 ** (attempt + 1)
            print(f"  Error (intento {attempt+1}/4): {exc}. Reintentando en {wait}s…")
            time.sleep(wait)

    print(f"  FALLO definitivo: {name}")


def main():
    print("Obteniendo token…")
    token = get_token(EMAIL, PASSWORD)

    print("Buscando imágenes Sentinel-1 SLC sobre Toluca…")
    products = search_products(token)
    print(f"Productos encontrados: {len(products)}")

    for i, p in enumerate(products, 1):
        print(f"[{i}/{len(products)}] {p['Name']}")
        download(p, token)


if __name__ == "__main__":
    main()
```

---

## 6. Búsqueda y descarga en Alaska Satellite Facility (alternativo)

### 6.1 Interfaz gráfica (ASF Vertex)

1. Ir a `https://search.asf.alaska.edu`
2. Iniciar sesión con la cuenta EarthData
3. En el panel lateral izquierdo:
   - **Dataset**: `Sentinel-1`
   - **File Type**: `L1 Single Look Complex (SLC)`
   - **Beam Mode**: `IW`
4. En el mapa, dibujar el rectángulo del Valle de Toluca
5. Establecer **Date Range**: p. ej. `2019-01-01` → `2022-01-01`
6. Hacer clic en **"Search"**
7. En los resultados, activar la columna **"Path/Frame"** para filtrar
   por trayectoria relativa (órbita 143 ascendente)
8. Seleccionar todas las imágenes de interés → **"Download All"**
9. Descargar el archivo de metadatos CSV haciendo clic en **"Export CSV"**
   (útil para verificar la lista de pares)

### 6.2 Herramienta CLI `asf_search` (Python)

```bash
pip install asf_search
```

```python
import asf_search as asf
from pathlib import Path

RAW_DIR = Path("D:/data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)

results = asf.geo_search(
    platform=asf.PLATFORM.SENTINEL1,
    processingLevel=asf.PRODUCT_TYPE.SLC,
    beamMode=asf.BEAMMODE.IW,
    intersectsWith="POLYGON((-99.90 19.05,-99.32 19.05,-99.32 19.58,-99.90 19.58,-99.90 19.05))",
    start="2019-01-01T00:00:00Z",
    end="2022-01-01T00:00:00Z",
    maxResults=200,
)

print(f"Imágenes encontradas: {len(results)}")
for r in results:
    print(r.properties["sceneName"], r.properties["startTime"])

# Descargar con credenciales EarthData
session = asf.ASFSession().auth_with_creds("TU_USUARIO_EARTHDATA", "TU_CONTRASEÑA")
results.download(path=str(RAW_DIR), session=session)
```

---

## 7. Verificación de las imágenes descargadas

Antes de procesar, confirmar que cada archivo:

1. **Tiene el nombre correcto** (formato estándar ESA):
   ```
   S1A_IW_SLC__1SDV_YYYYMMDDTHHMMSS_YYYYMMDDTHHMMSS_OOOOOO_PPPPPP_CCCC.zip
   ```
   Donde `OOOOOO` es el número de órbita absoluta y `PPPPPP` es el ID de trayectoria.

2. **Está completo** — verificar tamaño típico de ~4 GB por imagen:
   ```bash
   # En Windows PowerShell
   Get-ChildItem D:\data\raw\*.zip | Select-Object Name, @{N='GB';E={[math]::Round($_.Length/1GB,2)}}
   ```
   ```bash
   # En Linux/macOS
   ls -lh D:/data/raw/*.zip
   ```

3. **No está corrupto** — validar checksum MD5 contra el valor del portal:
   ```bash
   # Windows PowerShell
   Get-FileHash -Algorithm MD5 S1A_IW_SLC__....zip
   ```
   ```bash
   # Linux
   md5sum S1A_IW_SLC__....zip
   ```

4. **Pertenece a la misma trayectoria relativa** — el número de trayectoria
   debe ser idéntico entre todas las imágenes de un lote InSAR.

---

## 8. Criterios para formar pares interferométricos válidos

| Criterio | Recomendación para Toluca |
|---|---|
| Misma trayectoria relativa | Obligatorio |
| Misma geometría (asc./desc.) | Obligatorio (no mezclar) |
| Baseline temporal | 12 – 180 días |
| Baseline perpendicular | < 200 m (idealmente < 150 m) |
| Condiciones atmosféricas | Evitar épocas de temporada de lluvias intensa (jun–sep) si es posible |
| Separación estacional | Preferir pares del mismo mes en años distintos para minimizar decorrelación |

### Ejemplo de lista de pares válida

```
Master              Slave               Baseline temp.
20190831            20190912            12 días
20190912            20190924            12 días
20190924            20191006            12 días
20200101            20200113            12 días
20200113            20200215            33 días
20200215            20200309            23 días
```

---

## 9. Organización de archivos para el pipeline

### 9.1 Estructura de directorios requerida

```
D:/
├── data/
│   └── raw/                          ← Imágenes SLC descargadas (.zip o .SAFE)
│       ├── S1A_IW_SLC__1SDV_20190831T120000_...zip
│       ├── S1A_IW_SLC__1SDV_20190912T120000_...zip
│       ├── S1A_IW_SLC__1SDV_20190924T120000_...zip
│       └── ...
└── Toluca/                           ← Resultados del pipeline (creado automáticamente)
    ├── insar_pipeline.log
    ├── hipercubo_pipeline.log
    ├── 20190831_20190912_Stack_..._Disp_TC.dim
    ├── 20190831_20190912_Stack_..._Disp_TC.data/
    ├── 20190912_20190924_Stack_..._Disp_TC.dim
    ├── 20190912_20190924_Stack_..._Disp_TC.data/
    ├── ...
    ├── mintpy_inputs/
    │   ├── 20190831_20190912.h5
    │   └── ...
    ├── mintpy_ts/
    │   ├── ifgramStack.h5
    │   └── timeseries.h5
    └── hipercubo/
        ├── deformation_cube.nc
        └── diff_20190831_20200215.tif
```

### 9.2 Reglas de nomenclatura de las imágenes crudas

Los archivos `.zip` descargados **no deben renombrarse**. El pipeline extrae
las fechas automáticamente del nombre estándar de ESA:

```
S1A_IW_SLC__1SDV_20190831T120000_20190831T120027_028677_033F7E_1A2B.zip
              ↑↑↑↑↑↑↑↑                                  
         Fecha de adquisición (YYYYMMDD)  ← se usa como fecha de la imagen
```

### 9.3 Verificar descompresión (opcional)

SNAP puede leer los `.zip` directamente. Si se descomprime manualmente,
la carpeta `.SAFE` debe quedar así:

```
S1A_IW_SLC__1SDV_20190831T120000_...SAFE/
├── manifest.safe
├── annotation/
│   ├── s1a-iw1-slc-vv-....xml
│   ├── s1a-iw2-slc-vv-....xml
│   └── s1a-iw3-slc-vv-....xml
├── measurement/
│   ├── s1a-iw1-slc-vv-....tiff
│   └── ...
└── support/
```

---

## 10. Configurar el pipeline con las rutas descargadas

Editar `sentinel1_insar_toluca.py`, sección `IMAGE_PAIRS`:

```python
IMAGE_PAIRS = [
    # Pares con intervalo de 12 días
    (
        r"D:\data\raw\S1A_IW_SLC__1SDV_20190831T120000_....zip",
        r"D:\data\raw\S1A_IW_SLC__1SDV_20190912T120000_....zip",
    ),
    (
        r"D:\data\raw\S1A_IW_SLC__1SDV_20190912T120000_....zip",
        r"D:\data\raw\S1A_IW_SLC__1SDV_20190924T120000_....zip",
    ),
    # Pares con mayor separación temporal (SBAS)
    (
        r"D:\data\raw\S1A_IW_SLC__1SDV_20200101T120000_....zip",
        r"D:\data\raw\S1A_IW_SLC__1SDV_20200215T120000_....zip",
    ),
]
```

> **Consejo:** Usar rutas raw strings (`r"..."`) en Windows para evitar
> problemas con la barra invertida.

---

## 11. Identificar el sub-swath y bursts correctos

Este paso se hace **una sola vez** con SNAP Desktop antes del procesamiento masivo:

1. Abrir SNAP Desktop
2. `File → Open Product` → seleccionar cualquier imagen `.zip` de la serie
3. En el *Product Explorer*, expandir → `Bands` → abrir la banda de amplitud VV
4. En el menú: `Tools → Radar → Sentinel-1 TOPS → S1 TOPS Split`
5. En el diálogo:
   - Seleccionar el **Sub-swath** (IW1, IW2 o IW3) y observar el mapa de cobertura
   - Ajustar los **Bursts** hasta que el rectángulo de cobertura incluya el Valle de Toluca
   - Anotar los valores: p. ej. `IW2`, bursts `2` a `4`
6. Actualizar `config.py`:
   ```python
   DEFAULT_SUBSWATH      = "IW2"
   DEFAULT_BURSTS_MASTER = "2,4"
   DEFAULT_BURSTS_SLAVE  = "2,4"
   ```

---

## 12. Lista de verificación antes de procesar

- [ ] Cuenta activa en Copernicus Data Space o ASF EarthData
- [ ] Todas las imágenes `.zip` descargadas en `D:/data/raw/`
- [ ] Tamaños de archivo verificados (~4 GB c/u)
- [ ] Todas las imágenes pertenecen a la **misma trayectoria relativa**
- [ ] Sub-swath y bursts identificados con SNAP Desktop
- [ ] `config.py` actualizado con sub-swath y bursts correctos
- [ ] Lista `IMAGE_PAIRS` completa en `sentinel1_insar_toluca.py`
- [ ] ESA SNAP 9.x instalado y `snappy` configurado
- [ ] SNAPHU 1.4.2 disponible en `PATH`
- [ ] Al menos **16 GB de RAM** disponible (recomendado 32 GB)
- [ ] Al menos **500 GB de espacio en disco** libre en `D:/`
