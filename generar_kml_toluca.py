#!/usr/bin/env python3
"""
Genera toluca_pozos_grietas.kml con datos de dos fuentes cartográficas:

  MAPA 1 – Imagen impresa (grid UTM parcial: E 431114 / E 433514)
    • Pozos de extracción de agua subterránea (38 puntos azules)
    • Grietas estimadas (12 trazos amarillos)

  MAPA 2 – Geología Regional, Fallas y Fracturas
            SGM E14-2 / INEGI / CENAPRED / Soc. Mexiquense de Geotecnia
            Grid UTM 14N completo visible:
              E 430419, 432419, 434419  |  N 2131954, 2133954
    • Puntos de verificación "Grieta" (círculos verdes, campo 29-May-2026)
    • Puntos de verificación "Falla normal" (círculos verdes)
    • Fallas cartografiadas INEGI/CENAPRED/SGM (líneas rojas)
    • Falla cartografiada por la Soc. Mexiquense de Geotecnia (línea magenta)

Dependencias:
    pip install pyproj

Uso:
    python generar_kml_toluca.py
    Salida: toluca_pozos_grietas.kml  (Google Earth Pro / QGIS)
"""

from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom.minidom import parseString
from pyproj import Transformer

# ── Transformador UTM Zona 14N (EPSG:32614) → WGS84 (EPSG:4326) ─────────────
transformer = Transformer.from_crs("EPSG:32614", "EPSG:4326", always_xy=True)

def utm_to_lonlat(easting: float, northing: float) -> tuple[float, float]:
    lon, lat = transformer.transform(easting, northing)
    return lon, lat


# ═══════════════════════════════════════════════════════════════════════════════
# MAPA 1 – POZOS DE EXTRACCIÓN (puntos azules)
# Referencia de imagen: E 431114 y E 433514 visibles en borde superior.
# ═══════════════════════════════════════════════════════════════════════════════
pozos_utm = [
    (430650, 2141900, "Pozo-01"),
    (431400, 2141600, "Pozo-02"),
    (431950, 2141700, "Pozo-03"),
    (432400, 2141550, "Pozo-04"),
    (432800, 2141800, "Pozo-05"),
    (433200, 2141650, "Pozo-06"),
    (433700, 2141400, "Pozo-07"),
    (434050, 2141600, "Pozo-08"),
    (434500, 2141350, "Pozo-09"),
    (432100, 2140700, "Pozo-10"),
    (432600, 2140800, "Pozo-11"),
    (433050, 2140500, "Pozo-12"),
    (433450, 2140700, "Pozo-13"),
    (433800, 2140400, "Pozo-14"),
    (434200, 2140550, "Pozo-15"),
    (434550, 2140300, "Pozo-16"),
    (431800, 2139900, "Pozo-17"),
    (432250, 2140000, "Pozo-18"),
    (432750, 2139800, "Pozo-19"),
    (433200, 2139950, "Pozo-20"),
    (433700, 2139700, "Pozo-21"),
    (434150, 2139850, "Pozo-22"),
    (431600, 2139100, "Pozo-23"),
    (432100, 2139200, "Pozo-24"),
    (432700, 2139000, "Pozo-25"),
    (433300, 2139100, "Pozo-26"),
    (433800, 2138900, "Pozo-27"),
    (434300, 2138800, "Pozo-28"),
    (430950, 2137700, "Pozo-29"),
    (431600, 2137500, "Pozo-30"),
    (432200, 2137600, "Pozo-31"),
    (432800, 2137400, "Pozo-32"),
    (433400, 2137550, "Pozo-33"),
    (434000, 2137300, "Pozo-34"),
    (430400, 2136500, "Pozo-35"),
    (431000, 2136300, "Pozo-36"),
    (431700, 2136400, "Pozo-37"),
    (432300, 2136200, "Pozo-38"),
]

# ═══════════════════════════════════════════════════════════════════════════════
# MAPA 1 – GRIETAS ESTIMADAS (trazos amarillos)
# ═══════════════════════════════════════════════════════════════════════════════
grietas_mapa1 = [
    {
        "id": "G1-01",
        "desc": "Par en X – zona noreste",
        "puntos": [(430050, 2141400), (430450, 2141800)],
    },
    {
        "id": "G1-02",
        "desc": "Par en X – zona noreste (cruce)",
        "puntos": [(430050, 2141800), (430450, 2141400)],
    },
    {
        "id": "G1-03",
        "desc": "Trazo diagonal – norte-centro",
        "puntos": [(431200, 2141000), (431450, 2141300)],
    },
    {
        "id": "G1-04",
        "desc": "Trazo diagonal corto – norte-centro",
        "puntos": [(431600, 2140950), (431850, 2141200)],
    },
    {
        "id": "G1-05",
        "desc": "Grieta principal NNO-SSE – Isidro Fabela / Pino Suárez",
        "puntos": [
            (431900, 2139900), (431930, 2139500), (431960, 2139100),
            (431990, 2138700), (432020, 2138300), (432050, 2137900),
        ],
    },
    {
        "id": "G1-06",
        "desc": "Par en X – zona suroeste",
        "puntos": [(429800, 2139100), (430200, 2139500)],
    },
    {
        "id": "G1-07",
        "desc": "Par en X – zona suroeste (cruce)",
        "puntos": [(429800, 2139500), (430200, 2139100)],
    },
    {
        "id": "G1-08",
        "desc": "Trazo corto – franja suroeste",
        "puntos": [(430050, 2138650), (430350, 2138900)],
    },
    {
        "id": "G1-09",
        "desc": "Trazo diagonal – zona este",
        "puntos": [(433950, 2139800), (434350, 2140100)],
    },
    {
        "id": "G1-10",
        "desc": "Trazo vertical – zona este",
        "puntos": [(434400, 2139300), (434500, 2139750)],
    },
    {
        "id": "G1-11",
        "desc": "Trazo curvo – extremo sureste",
        "puntos": [(434550, 2137850), (434800, 2137600), (435100, 2137500)],
    },
    {
        "id": "G1-12",
        "desc": "Trazo corto – zona norte (Alfredo del Mazo)",
        "puntos": [(433500, 2142100), (433700, 2141800)],
    },
]

# ═══════════════════════════════════════════════════════════════════════════════
# MAPA 2 – PUNTOS DE VERIFICACIÓN "GRIETA"  (círculos verdes etiquetados Grieta)
# Fuente: SGM E14-2 / CENAPRED / Soc. Mexiquense de Geotecnia, 29-May-2026.
# Grid de referencia exacto: E 430419|432419|434419 / N 2131954|2133954
# Digitalización pixel → UTM con escala 4.37 m/px H y 4.40 m/px V.
# ═══════════════════════════════════════════════════════════════════════════════
pv_grietas = [
    # -- margen izquierdo (borde E 430419) --
    (430448, 2132360, "PV-Grieta-01", "Grieta – borde oeste, sector norte"),
    (430448, 2132155, "PV-Grieta-02", "Grieta – borde oeste, sector medio"),
    (430448, 2131968, "PV-Grieta-03", "Grieta – borde oeste, sobre N 2131954"),
    # -- cluster centro-sur (Paseo Tollocan / Lerdo) --
    (431705, 2132070, "PV-Grieta-04", "Grieta – zona centro-sur"),
    (431755, 2131990, "PV-Grieta-05", "Grieta – zona centro-sur"),
    (431800, 2131905, "PV-Grieta-06", "Grieta – zona centro-sur"),
    # -- cluster superior-centro (E ≈ 432419) --
    (432110, 2133710, "PV-Grieta-07", "Grieta – sector norte, junto a falla normal"),
    (432450, 2133725, "PV-Grieta-08", "Grieta – sector norte"),
    # -- extremo derecho superior --
    (434340, 2133560, "PV-Grieta-09", "Grieta – extremo NE del área"),
    # -- margen derecho (E ≈ 434419) --
    (434355, 2132100, "PV-Grieta-10", "Grieta – borde este, sector medio"),
    (434295, 2131720, "PV-Grieta-11", "Grieta – borde este, sector sur"),
]

# ═══════════════════════════════════════════════════════════════════════════════
# MAPA 2 – PUNTOS DE VERIFICACIÓN "FALLA NORMAL"  (círculos verdes)
# ═══════════════════════════════════════════════════════════════════════════════
pv_fallas_normales = [
    (432200, 2133760, "PV-FN-01", "Falla normal verificada – sector norte"),
    (432380, 2133755, "PV-FN-02", "Falla normal verificada – sector norte"),
    (432540, 2133745, "PV-FN-03", "Falla normal verificada – sector norte"),
    (434395, 2133820, "PV-FN-04", "Falla normal + Extracción de fluidos – NE"),
    (434350, 2132095, "PV-FN-05", "Falla normal verificada – borde este"),
]

# ═══════════════════════════════════════════════════════════════════════════════
# MAPA 2 – FALLAS CARTOGRAFIADAS (líneas rojas – INEGI / CENAPRED / SGM)
# Trazados por segmentos usando los puntos de verificación como anclas.
# ═══════════════════════════════════════════════════════════════════════════════
fallas_rojas = [
    {
        "id": "Falla-R01",
        "desc": "Falla normal – borde oeste, tendencia NNW-SSE (INEGI/SGM)",
        "puntos": [
            (430450, 2132430),
            (430455, 2132300),
            (430460, 2132150),
            (430465, 2131970),
        ],
    },
    {
        "id": "Falla-R02",
        "desc": "Fallas normales – sector norte, cluster E 432 000-432 600 (CENAPRED)",
        "puntos": [
            (432080, 2133720),
            (432250, 2133750),
            (432420, 2133740),
            (432590, 2133730),
        ],
    },
    {
        "id": "Falla-R03",
        "desc": "Falla normal – extremo NE, tendencia NNE-SSW (INEGI/SGM)",
        "puntos": [
            (434200, 2133760),
            (434320, 2133620),
            (434360, 2133460),
        ],
    },
    {
        "id": "Falla-R04",
        "desc": "Falla normal principal – borde este, tendencia NNW-SSE (SGM/CENAPRED)",
        "puntos": [
            (433760, 2132290),
            (433820, 2132100),
            (433870, 2131900),
            (433910, 2131720),
        ],
    },
]

# ═══════════════════════════════════════════════════════════════════════════════
# MAPA 2 – FALLA CARTOGRAFIADA POR LA SOC. MEXIQUENSE DE GEOTECNIA (magenta)
# Incluye el segmento "(" circundado en azul en la imagen del usuario.
# ═══════════════════════════════════════════════════════════════════════════════
falla_smg = [
    {
        "id": "Falla-SMG-01",
        "desc": "Falla SMG – ramal noreste, zona de influencia 500 m",
        "puntos": [
            (430700, 2133500),
            (431000, 2133470),
            (431350, 2133460),
            (431650, 2133490),
            (431900, 2133540),
        ],
    },
    {
        "id": "Falla-SMG-02",
        "desc": "Falla SMG – segmento central (símbolo '(' señalado en imagen)",
        "puntos": [
            (431720, 2132900),
            (431740, 2132780),
            (431760, 2132660),
            (431750, 2132540),
        ],
    },
]


# ═══════════════════════════════════════════════════════════════════════════════
# CONSTRUCCIÓN KML
# ═══════════════════════════════════════════════════════════════════════════════
def _cs(lon: float, lat: float, alt: float = 0.0) -> str:
    return f"{lon:.7f},{lat:.7f},{alt}"


def _add_style_icon(doc, sid: str, color_abgr: str, scale: str,
                    icon_url: str, label_scale: str = "0.8") -> None:
    sty = SubElement(doc, "Style", id=sid)
    ics = SubElement(sty, "IconStyle")
    SubElement(ics, "color").text = color_abgr
    SubElement(ics, "scale").text = scale
    ic = SubElement(ics, "Icon")
    SubElement(ic, "href").text = icon_url
    lbs = SubElement(sty, "LabelStyle")
    SubElement(lbs, "scale").text = label_scale


def _add_style_line(doc, sid: str, color_abgr: str, width: str) -> None:
    sty = SubElement(doc, "Style", id=sid)
    ls = SubElement(sty, "LineStyle")
    SubElement(ls, "color").text = color_abgr
    SubElement(ls, "width").text = width


def _add_point(folder, name: str, lon: float, lat: float,
               style_url: str, description: str) -> None:
    pm = SubElement(folder, "Placemark")
    SubElement(pm, "name").text = name
    SubElement(pm, "styleUrl").text = style_url
    SubElement(pm, "description").text = description
    pt = SubElement(pm, "Point")
    SubElement(pt, "coordinates").text = _cs(lon, lat)


def _add_line(folder, name: str, puntos_utm: list,
              style_url: str, description: str) -> None:
    coords = " ".join(_cs(*utm_to_lonlat(e, n)) for e, n in puntos_utm)
    pm = SubElement(folder, "Placemark")
    SubElement(pm, "name").text = name
    SubElement(pm, "styleUrl").text = style_url
    SubElement(pm, "description").text = description
    ls = SubElement(pm, "LineString")
    SubElement(ls, "tessellate").text = "1"
    SubElement(ls, "coordinates").text = coords


def build_kml() -> str:
    kml = Element("kml", xmlns="http://www.opengis.net/kml/2.2")
    doc = SubElement(kml, "Document")
    SubElement(doc, "name").text = "Toluca – Pozos, Grietas y Fallas"
    SubElement(doc, "description").text = (
        "Datos geoestructurales de Toluca de Lerdo, Estado de México.\n"
        "Fuentes: mapa impreso de pozos/grietas + SGM E14-2 / INEGI / CENAPRED / "
        "Sociedad Mexiquense de Geotecnia (levantamiento 29-May-2026).\n"
        "Proyección: UTM Zona 14N / WGS84. Coordenadas digitalizadas manualmente."
    )

    # Estilos
    _add_style_icon(doc, "s_pozo",    "ffff0000",  "1.1",
                    "http://maps.google.com/mapfiles/kml/shapes/water.png")
    _add_style_icon(doc, "s_grieta_pv", "ff00aa00", "1.0",
                    "http://maps.google.com/mapfiles/kml/paddle/grn-circle.png")
    _add_style_icon(doc, "s_falla_pv",  "ff0000ff", "1.0",
                    "http://maps.google.com/mapfiles/kml/paddle/red-circle.png")
    _add_style_line(doc, "s_grieta_m1",  "ff00ffff", "3")   # amarillo
    _add_style_line(doc, "s_falla_roja", "ff0000ff", "4")   # rojo
    _add_style_line(doc, "s_falla_smg",  "ffff00ff", "4")   # magenta

    # ── Carpeta 1: Pozos de extracción (Mapa 1) ──────────────────────────────
    f1 = SubElement(doc, "Folder")
    SubElement(f1, "name").text = "Pozos de extracción (Mapa 1)"
    SubElement(f1, "visibility").text = "1"
    for e, n, pid in pozos_utm:
        lon, lat = utm_to_lonlat(e, n)
        _add_point(f1, pid, lon, lat, "#s_pozo",
                   f"Pozo de extracción de agua subterránea\nUTM 14N  E:{e}  N:{n}")

    # ── Carpeta 2: Grietas estimadas (Mapa 1) ─────────────────────────────────
    f2 = SubElement(doc, "Folder")
    SubElement(f2, "name").text = "Grietas estimadas (Mapa 1)"
    SubElement(f2, "visibility").text = "1"
    for g in grietas_mapa1:
        _add_line(f2, g["id"], g["puntos"], "#s_grieta_m1", g["desc"])

    # ── Carpeta 3: Puntos verificación – Grietas (Mapa 2) ────────────────────
    f3 = SubElement(doc, "Folder")
    SubElement(f3, "name").text = "Grietas verificadas en campo (Mapa 2 – SMG/CENAPRED)"
    SubElement(f3, "visibility").text = "1"
    for e, n, pid, desc in pv_grietas:
        lon, lat = utm_to_lonlat(e, n)
        _add_point(f3, pid, lon, lat, "#s_grieta_pv",
                   f"{desc}\nUTM 14N  E:{e}  N:{n}\nLevantamiento: 29-May-2026")

    # ── Carpeta 4: Puntos verificación – Fallas normales (Mapa 2) ────────────
    f4 = SubElement(doc, "Folder")
    SubElement(f4, "name").text = "Fallas normales verificadas (Mapa 2 – SMG/CENAPRED)"
    SubElement(f4, "visibility").text = "1"
    for e, n, pid, desc in pv_fallas_normales:
        lon, lat = utm_to_lonlat(e, n)
        _add_point(f4, pid, lon, lat, "#s_falla_pv",
                   f"{desc}\nUTM 14N  E:{e}  N:{n}\nLevantamiento: 29-May-2026")

    # ── Carpeta 5: Fallas cartografiadas INEGI/CENAPRED/SGM (rojas) ──────────
    f5 = SubElement(doc, "Folder")
    SubElement(f5, "name").text = "Fallas cartografiadas INEGI/CENAPRED/SGM (Mapa 2)"
    SubElement(f5, "visibility").text = "1"
    for fl in fallas_rojas:
        _add_line(f5, fl["id"], fl["puntos"], "#s_falla_roja", fl["desc"])

    # ── Carpeta 6: Falla Soc. Mexiquense de Geotecnia (magenta) ──────────────
    f6 = SubElement(doc, "Folder")
    SubElement(f6, "name").text = "Falla cartografiada – Soc. Mexiquense de Geotecnia"
    SubElement(f6, "visibility").text = "1"
    for seg in falla_smg:
        _add_line(f6, seg["id"], seg["puntos"], "#s_falla_smg", seg["desc"])

    raw = tostring(kml, encoding="unicode")
    return parseString(raw).toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")


if __name__ == "__main__":
    output = "toluca_pozos_grietas.kml"
    with open(output, "w", encoding="utf-8") as f:
        f.write(build_kml())

    total_puntos = len(pozos_utm) + len(pv_grietas) + len(pv_fallas_normales)
    total_lineas = len(grietas_mapa1) + len(fallas_rojas) + len(falla_smg)

    print(f"KML generado: {output}")
    print(f"  Pozos de extracción            : {len(pozos_utm)}")
    print(f"  Grietas estimadas (Mapa 1)     : {len(grietas_mapa1)}")
    print(f"  Grietas verificadas (Mapa 2)   : {len(pv_grietas)}")
    print(f"  Fallas normales verif. (Mapa 2): {len(pv_fallas_normales)}")
    print(f"  Fallas INEGI/CENAPRED/SGM      : {len(fallas_rojas)}")
    print(f"  Falla SMG cartografiada        : {len(falla_smg)} segmentos")
    print(f"  ─────────────────────────────────")
    print(f"  Total puntos                   : {total_puntos}")
    print(f"  Total líneas/polilíneas        : {total_lineas}")
    print()
    print("Abre en Google Earth Pro o QGIS.")
    print("NOTA: coordenadas digitalizadas manualmente; validar con GPS.")
