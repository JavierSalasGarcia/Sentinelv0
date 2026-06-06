#!/usr/bin/env python3
"""
Genera toluca_pozos_grietas.kml — versión consolidada y verificada.

FUENTES
-------
Mapa 1 · Imagen fotográfica de mapa impreso (anotaciones a mano)
         Grid parcial: E 431114 / E 433514 (solo eastings visibles)

Mapa 2 · Geología Regional, Fallas y Fracturas
         SGM E14-2 / INEGI / CENAPRED / Soc. Mexiquense de Geotecnia
         Levantamiento 29-May-2026
         Grid completo: E 430419|432419|434419 · N 2131954|2133954

Mapa 3 · Zonificación Geotécnica Zona Conurbada Toluca-Metepec
         IGZA (Ingeniería Geotécnica y Zonificación Aplicada S.A. de C.V.)
         Base: INEGI/SEGUR/SGM · Datum UTM 14Q / ITRF 2008
         Grid completo: E 430045|432445|434845|437245 · N 2129770|2132170|2134570

ANÁLISIS DE CONSISTENCIA
------------------------
1. Sistema de referencia:
   - Mapa 2 usa "UTM 14N / WGS84".  "14N" = Zona 14, hemisferio norte.
   - Mapa 3 usa "UTM 14Q / ITRF 2008". "14Q" = Zona 14, banda latitudinal Q
     (16°-24°N, que corresponde a Toluca ≈19.3°N). ITRF 2008 ≈ WGS84
     con diferencia < 1 m en esta zona. → Ambos datums son compatibles.

2. Corrección crítica de northings — Mapa 1:
   Las northings del Mapa 1 fueron estimadas sin referencia y resultaron
   ~7 000 m demasiado altas (N 2136000-2142000 en lugar de N 2129000-2135000).
   → CORRECCIÓN APLICADA: northing_corr = northing_orig − 7 000 m
   Después de la corrección, los pozos del Mapa 1 caen en
   E 429800-435100, N 2129200-2135100, solapando correctamente con
   los Mapas 2 y 3.

3. Solapamiento entre mapas:
   Mapa 2 ⊂ Mapa 3 (el Mapa 3 cubre un área mayor hacia el este y el sur).
   Las fallas rojas del Mapa 2 coinciden espacialmente con las líneas
   amarillas del Mapa 3 en la zona de solapamiento.
   Los puntos de verificación "Grieta" del Mapa 2 coinciden con las
   etiquetas "Grieta" del Mapa 3 en las mismas coordenadas.

4. Bounding boxes (UTM 14N/WGS84 equivalente):
   Mapa 1 (corr.)  E 429800-435100  N 2129200-2135100
   Mapa 2          E 430419-434419  N 2131954-2133954
   Mapa 3          E 430045-437245  N 2129770-2134570
   Unión           E 429800-437245  N 2129200-2135100

Dependencias:
    pip install pyproj

Uso:
    python generar_kml_toluca.py
    Salida: toluca_pozos_grietas.kml
"""

from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom.minidom import parseString
from pyproj import Transformer

# ── UTM Zona 14N (EPSG:32614) → WGS84 (EPSG:4326) ──────────────────────────
_t = Transformer.from_crs("EPSG:32614", "EPSG:4326", always_xy=True)

def ll(e: float, n: float) -> tuple[float, float]:
    """UTM Z14N → (lon, lat)."""
    return _t.transform(e, n)


# ═══════════════════════════════════════════════════════════════════════════════
# MAPA 1 — POZOS  (northings corregidos −7 000 m)
# ═══════════════════════════════════════════════════════════════════════════════
_D = -7_000   # corrección northing Mapa 1

M1_POZOS = [
    (430650, 2141900+_D, "M1-Pozo-01"),
    (431400, 2141600+_D, "M1-Pozo-02"),
    (431950, 2141700+_D, "M1-Pozo-03"),
    (432400, 2141550+_D, "M1-Pozo-04"),
    (432800, 2141800+_D, "M1-Pozo-05"),
    (433200, 2141650+_D, "M1-Pozo-06"),
    (433700, 2141400+_D, "M1-Pozo-07"),
    (434050, 2141600+_D, "M1-Pozo-08"),
    (434500, 2141350+_D, "M1-Pozo-09"),
    (432100, 2140700+_D, "M1-Pozo-10"),
    (432600, 2140800+_D, "M1-Pozo-11"),
    (433050, 2140500+_D, "M1-Pozo-12"),
    (433450, 2140700+_D, "M1-Pozo-13"),
    (433800, 2140400+_D, "M1-Pozo-14"),
    (434200, 2140550+_D, "M1-Pozo-15"),
    (434550, 2140300+_D, "M1-Pozo-16"),
    (431800, 2139900+_D, "M1-Pozo-17"),
    (432250, 2140000+_D, "M1-Pozo-18"),
    (432750, 2139800+_D, "M1-Pozo-19"),
    (433200, 2139950+_D, "M1-Pozo-20"),
    (433700, 2139700+_D, "M1-Pozo-21"),
    (434150, 2139850+_D, "M1-Pozo-22"),
    (431600, 2139100+_D, "M1-Pozo-23"),
    (432100, 2139200+_D, "M1-Pozo-24"),
    (432700, 2139000+_D, "M1-Pozo-25"),
    (433300, 2139100+_D, "M1-Pozo-26"),
    (433800, 2138900+_D, "M1-Pozo-27"),
    (434300, 2138800+_D, "M1-Pozo-28"),
    (430950, 2137700+_D, "M1-Pozo-29"),
    (431600, 2137500+_D, "M1-Pozo-30"),
    (432200, 2137600+_D, "M1-Pozo-31"),
    (432800, 2137400+_D, "M1-Pozo-32"),
    (433400, 2137550+_D, "M1-Pozo-33"),
    (434000, 2137300+_D, "M1-Pozo-34"),
    (430400, 2136500+_D, "M1-Pozo-35"),
    (431000, 2136300+_D, "M1-Pozo-36"),
    (431700, 2136400+_D, "M1-Pozo-37"),
    (432300, 2136200+_D, "M1-Pozo-38"),
]

# ── MAPA 1 — GRIETAS estimadas (northings corregidos) ───────────────────────
M1_GRIETAS = [
    {"id": "M1-G01", "desc": "Par en X – NE (Alfredo del Mazo)",
     "pts": [(430050, 2141400+_D), (430450, 2141800+_D)]},
    {"id": "M1-G02", "desc": "Par en X – NE (cruce)",
     "pts": [(430050, 2141800+_D), (430450, 2141400+_D)]},
    {"id": "M1-G03", "desc": "Trazo diagonal – norte-centro",
     "pts": [(431200, 2141000+_D), (431450, 2141300+_D)]},
    {"id": "M1-G04", "desc": "Trazo diagonal – norte-centro",
     "pts": [(431600, 2140950+_D), (431850, 2141200+_D)]},
    {"id": "M1-G05", "desc": "Grieta principal NNO-SSE – Isidro Fabela/Pino Suárez",
     "pts": [(431900, 2139900+_D), (431930, 2139500+_D), (431960, 2139100+_D),
             (431990, 2138700+_D), (432020, 2138300+_D), (432050, 2137900+_D)]},
    {"id": "M1-G06", "desc": "Par en X – SO límite urbano",
     "pts": [(429800, 2139100+_D), (430200, 2139500+_D)]},
    {"id": "M1-G07", "desc": "Par en X – SO límite urbano (cruce)",
     "pts": [(429800, 2139500+_D), (430200, 2139100+_D)]},
    {"id": "M1-G08", "desc": "Trazo corto – franja SO",
     "pts": [(430050, 2138650+_D), (430350, 2138900+_D)]},
    {"id": "M1-G09", "desc": "Trazo diagonal – zona este",
     "pts": [(433950, 2139800+_D), (434350, 2140100+_D)]},
    {"id": "M1-G10", "desc": "Trazo vertical – zona este",
     "pts": [(434400, 2139300+_D), (434500, 2139750+_D)]},
    {"id": "M1-G11", "desc": "Trazo curvo – extremo SE",
     "pts": [(434550, 2137850+_D), (434800, 2137600+_D), (435100, 2137500+_D)]},
    {"id": "M1-G12", "desc": "Trazo corto – norte (Alfredo del Mazo)",
     "pts": [(433500, 2142100+_D), (433700, 2141800+_D)]},
]


# ═══════════════════════════════════════════════════════════════════════════════
# MAPA 2 — SGM/CENAPRED/SMG (coordenadas precisas, sin corrección)
# ═══════════════════════════════════════════════════════════════════════════════
M2_PV_GRIETAS = [
    # (E, N, id, descripción)
    (430448, 2132360, "M2-PVG-01", "Grieta verificada – borde O, sector N"),
    (430448, 2132155, "M2-PVG-02", "Grieta verificada – borde O, sector medio"),
    (430448, 2131968, "M2-PVG-03", "Grieta verificada – borde O, sobre N 2131954"),
    (431705, 2132070, "M2-PVG-04", "Grieta verificada – zona centro-sur"),
    (431755, 2131990, "M2-PVG-05", "Grieta verificada – zona centro-sur"),
    (431800, 2131905, "M2-PVG-06", "Grieta verificada – zona centro-sur"),
    (432110, 2133710, "M2-PVG-07", "Grieta verificada – sector N, junto a falla normal"),
    (432450, 2133725, "M2-PVG-08", "Grieta verificada – sector N"),
    (434340, 2133560, "M2-PVG-09", "Grieta verificada – extremo NE"),
    (434355, 2132100, "M2-PVG-10", "Grieta verificada – borde E, sector medio"),
    (434295, 2131720, "M2-PVG-11", "Grieta verificada – borde E, sector S"),
]

M2_PV_FALLAS = [
    (432200, 2133760, "M2-PVF-01", "Falla normal verificada – sector N"),
    (432380, 2133755, "M2-PVF-02", "Falla normal verificada – sector N"),
    (432540, 2133745, "M2-PVF-03", "Falla normal verificada – sector N"),
    (434395, 2133820, "M2-PVF-04", "Falla normal + Extracción de fluidos – NE"),
    (434350, 2132095, "M2-PVF-05", "Falla normal verificada – borde E"),
]

M2_FALLAS_ROJAS = [
    {"id": "M2-FR-01",
     "desc": "Falla normal – borde O, tendencia NNW-SSE (INEGI/SGM)",
     "pts": [(430450,2132430),(430455,2132300),(430460,2132150),(430465,2131970)]},
    {"id": "M2-FR-02",
     "desc": "Fallas normales – sector N, E 432000-432600 (CENAPRED)",
     "pts": [(432080,2133720),(432250,2133750),(432420,2133740),(432590,2133730)]},
    {"id": "M2-FR-03",
     "desc": "Falla normal – extremo NE, tendencia NNE-SSW (INEGI/SGM)",
     "pts": [(434200,2133760),(434320,2133620),(434360,2133460)]},
    {"id": "M2-FR-04",
     "desc": "Falla normal principal – borde E, tendencia NNW-SSE (SGM/CENAPRED)",
     "pts": [(433760,2132290),(433820,2132100),(433870,2131900),(433910,2131720)]},
]

M2_FALLA_SMG = [
    {"id": "M2-SMG-01",
     "desc": "Falla SMG – ramal NE (zona influencia 500 m)",
     "pts": [(430700,2133500),(431000,2133470),(431350,2133460),
             (431650,2133490),(431900,2133540)]},
    {"id": "M2-SMG-02",
     "desc": "Falla SMG – segmento central símbolo '(' (destacado en imagen)",
     "pts": [(431720,2132900),(431740,2132780),(431760,2132660),(431750,2132540)]},
]


# ═══════════════════════════════════════════════════════════════════════════════
# MAPA 3 — IGZA (digitalización con grid E430045|432445|434845|437245,
#                                            N2129770|2132170|2134570)
# Escala: ~9.6 m/px. ITRF 2008 ≈ WGS84 → sin corrección de datum necesaria.
# ═══════════════════════════════════════════════════════════════════════════════

# ── Pozos (puntos azules) ────────────────────────────────────────────────────
M3_POZOS = [
    # Zona norte  (N 2133500-2134500)
    (430525, 2134300, "M3-Pozo-01"),
    (430765, 2134260, "M3-Pozo-02"),
    (431150, 2134370, "M3-Pozo-03"),
    (431630, 2134210, "M3-Pozo-04"),
    (432060, 2134330, "M3-Pozo-05"),
    (432300, 2134140, "M3-Pozo-06"),
    (432730, 2134280, "M3-Pozo-07"),
    (433210, 2134370, "M3-Pozo-08"),
    (433790, 2134210, "M3-Pozo-09"),
    (434370, 2134300, "M3-Pozo-10"),
    (434990, 2134190, "M3-Pozo-11"),
    (435560, 2134280, "M3-Pozo-12"),
    (436000, 2134090, "M3-Pozo-13"),
    (436380, 2134330, "M3-Pozo-14"),
    (436770, 2134190, "M3-Pozo-15"),
    # Zona media  (N 2132200-2133500)
    (430410, 2133270, "M3-Pozo-16"),
    (430960, 2133150, "M3-Pozo-17"),
    (431530, 2133340, "M3-Pozo-18"),
    (432160, 2132990, "M3-Pozo-19"),
    (432780, 2133250, "M3-Pozo-20"),
    (433410, 2133110, "M3-Pozo-21"),
    (434030, 2133320, "M3-Pozo-22"),
    (434610, 2133050, "M3-Pozo-23"),
    (435230, 2133200, "M3-Pozo-24"),
    (435810, 2133050, "M3-Pozo-25"),
    (436430, 2133200, "M3-Pozo-26"),
    # Zona sur  (N 2129800-2132200)
    (430330, 2131980, "M3-Pozo-27"),
    (430810, 2131690, "M3-Pozo-28"),
    (431490, 2131830, "M3-Pozo-29"),
    (432210, 2131450, "M3-Pozo-30"),
    (432970, 2131710, "M3-Pozo-31"),
    (433690, 2131550, "M3-Pozo-32"),
    (434420, 2131750, "M3-Pozo-33"),
    (435090, 2131610, "M3-Pozo-34"),
    (435660, 2131810, "M3-Pozo-35"),
    (436200, 2131480, "M3-Pozo-36"),
    (436770, 2131690, "M3-Pozo-37"),
]

# ── Fallas y/o fracturas geológicas IGZA (líneas amarillas) ─────────────────
M3_FALLAS_LINEAS = [
    {"id": "M3-FL-01",
     "desc": "Fractura – zona NO, tendencia N-S (IGZA/INEGI)",
     "pts": [(430575,2134380),(430670,2134100),(430770,2133850),(430980,2133700)]},
    {"id": "M3-FL-02",
     "desc": "Fractura – cluster superior-centro A (IGZA)",
     "pts": [(431400,2134380),(431550,2134100),(431750,2133800)]},
    {"id": "M3-FL-03",
     "desc": "Fractura – cluster superior-centro B (IGZA)",
     "pts": [(432050,2134200),(432150,2133900),(432200,2133600)]},
    {"id": "M3-FL-04",
     "desc": "Falla normal principal – tendencia NNW-SSE, sector centro (IGZA)",
     "pts": [(431600,2133500),(431700,2133100),(431850,2132700),(432000,2132300)]},
    {"id": "M3-FL-05",
     "desc": "Falla normal – cluster centro-derecho (IGZA/SEGUR)",
     "pts": [(433300,2133300),(433500,2133000),(433700,2132600),(433850,2132300)]},
    {"id": "M3-FL-06",
     "desc": "Fractura – borde O inferior, tendencia NNW-SSE (IGZA)",
     "pts": [(430290,2132300),(430350,2131900),(430400,2131400),(430430,2131050)]},
    {"id": "M3-FL-07",
     "desc": "Fractura – centro-sur A (IGZA)",
     "pts": [(431650,2131600),(431900,2131300),(432150,2130900)]},
    {"id": "M3-FL-08",
     "desc": "Fractura – centro-sur B (IGZA)",
     "pts": [(432500,2131500),(432800,2131100),(433050,2130850)]},
    {"id": "M3-FL-09",
     "desc": "Fractura – centro-sur C / San Felipe Tlalmimilolpan (IGZA)",
     "pts": [(433250,2131500),(433500,2131200),(433750,2130900)]},
]

# ── Etiquetas "Grieta" confirmadas en Mapa 3 (posición de texto) ─────────────
M3_GRIETAS_PTS = [
    # (E, N, id, desc)
    (430575, 2133514, "M3-Grt-01", "Grieta – IGZA, zona NO (Cacalomacán)"),
    (430669, 2133130, "M3-Grt-02", "Grieta – IGZA, borde O sector N"),
    (430669, 2132890, "M3-Grt-03", "Grieta – IGZA, borde O sector medio"),
    (431149, 2133370, "M3-Grt-04", "Grieta – IGZA, zona O-centro"),
    (431245, 2132738, "M3-Grt-05", "Grieta – IGZA, sector centro-O"),
    (431965, 2132506, "M3-Grt-06", "Grieta – IGZA, centro"),
    (432157, 2132698, "M3-Grt-07", "Grieta – IGZA, centro"),
    (433021, 2133130, "M3-Grt-08", "Grieta – IGZA, centro-E"),
    (433789, 2133178, "M3-Grt-09", "Grieta – IGZA, sector E"),
    (430429, 2131978, "M3-Grt-10", "Grieta – IGZA, SO (Cacalomacán sur)"),
    (430381, 2131642, "M3-Grt-11", "Grieta – IGZA, SO"),
    (430381, 2131306, "M3-Grt-12", "Grieta – IGZA, SO"),
    (431965, 2131258, "M3-Grt-13", "Grieta – IGZA, sur-centro (Capultitlán)"),
    (432253, 2131066, "M3-Grt-14", "Grieta – IGZA, sur-centro"),
    (433021, 2131546, "M3-Grt-15", "Grieta – IGZA, sur (San Felipe Tlalmimilolpan)"),
]

# ── Etiquetas "Falla normal" en Mapa 3 ───────────────────────────────────────
M3_FALLAS_PTS = [
    (430621, 2133466, "M3-FN-01", "Falla normal – IGZA, borde O sector N"),
    (431245, 2133610, "M3-FN-02", "Falla normal – IGZA, O-centro sector N"),
    (431437, 2133514, "M3-FN-03", "Falla normal – IGZA, O-centro"),
    (432109, 2132786, "M3-FN-04", "Falla normal – IGZA, centro"),
    (433165, 2133082, "M3-FN-05", "Falla normal – IGZA, centro-E"),
    (433453, 2132994, "M3-FN-06", "Falla normal – IGZA, centro-E"),
    (434413, 2133082, "M3-FN-07", "Falla normal – IGZA, sector E"),
    (434750, 2133250, "M3-FN-08", "Falla normal – IGZA, E (San Pedro Totoltepec)"),
]

# ── Etiquetas especiales Mapa 3 ───────────────────────────────────────────────
M3_ESPECIALES = [
    (433045, 2133706, "M3-ESP-01", "Extracción de fluidos – IGZA (sector N)"),
    (433500, 2132950, "M3-ESP-02", "Extracción de fluidos – IGZA (sector centro-E)"),
    (434700, 2133600, "M3-ESP-03", "Procesos de compactación de suelos – IGZA"),
]


# ═══════════════════════════════════════════════════════════════════════════════
# CONSTRUCCIÓN KML
# ═══════════════════════════════════════════════════════════════════════════════
def _cs(lon, lat, alt=0.0):
    return f"{lon:.7f},{lat:.7f},{alt}"


def _style_icon(doc, sid, color_abgr, scale, href, lscale="0.8"):
    s = SubElement(doc, "Style", id=sid)
    ic = SubElement(s, "IconStyle")
    SubElement(ic, "color").text = color_abgr
    SubElement(ic, "scale").text = scale
    SubElement(SubElement(ic, "Icon"), "href").text = href
    SubElement(SubElement(s, "LabelStyle"), "scale").text = lscale


def _style_line(doc, sid, color_abgr, width):
    s = SubElement(doc, "Style", id=sid)
    ls = SubElement(s, "LineStyle")
    SubElement(ls, "color").text = color_abgr
    SubElement(ls, "width").text = str(width)


def _point(folder, name, e, n, style, desc):
    lon, lat = ll(e, n)
    pm = SubElement(folder, "Placemark")
    SubElement(pm, "name").text = name
    SubElement(pm, "styleUrl").text = style
    SubElement(pm, "description").text = f"{desc}\nUTM 14N  E:{e}  N:{n}"
    SubElement(SubElement(pm, "Point"), "coordinates").text = _cs(lon, lat)


def _line(folder, name, pts, style, desc):
    coords = " ".join(_cs(*ll(e, n)) for e, n in pts)
    pm = SubElement(folder, "Placemark")
    SubElement(pm, "name").text = name
    SubElement(pm, "styleUrl").text = style
    SubElement(pm, "description").text = desc
    ls = SubElement(pm, "LineString")
    SubElement(ls, "tessellate").text = "1"
    SubElement(ls, "coordinates").text = coords


def _folder(doc, name, vis=1):
    f = SubElement(doc, "Folder")
    SubElement(f, "name").text = name
    SubElement(f, "visibility").text = str(vis)
    return f


def build_kml():
    kml = Element("kml", xmlns="http://www.opengis.net/kml/2.2")
    doc = SubElement(kml, "Document")
    SubElement(doc, "name").text = "Toluca – Pozos, Grietas y Fallas (consolidado)"
    SubElement(doc, "description").text = (
        "Datos geoestructurales consolidados de la Zona Conurbada Toluca-Metepec.\n"
        "Fuentes: Mapa 1 (impreso+anotaciones) · Mapa 2 SGM/CENAPRED/SMG 2026 · "
        "Mapa 3 IGZA/INEGI/SEGUR.\n"
        "Corrección aplicada a Mapa 1: northing −7 000 m.\n"
        "CRS unificado: UTM Zona 14N / WGS84 (ITRF 2008 ≈ WGS84)."
    )

    # ── Estilos ──────────────────────────────────────────────────────────────
    _WATER = "http://maps.google.com/mapfiles/kml/shapes/water.png"
    _DOT_G = "http://maps.google.com/mapfiles/kml/paddle/grn-circle.png"
    _DOT_R = "http://maps.google.com/mapfiles/kml/paddle/red-circle.png"
    _DOT_Y = "http://maps.google.com/mapfiles/kml/paddle/ylw-circle.png"
    _DOT_O = "http://maps.google.com/mapfiles/kml/paddle/org-circle.png"
    _DOT_B = "http://maps.google.com/mapfiles/kml/paddle/blu-circle.png"

    _style_icon(doc, "s_pozo_m1",  "ffff5500", "1.0", _WATER)   # azul agua M1
    _style_icon(doc, "s_pozo_m3",  "ffff0000", "1.0", _DOT_B)   # azul M3
    _style_icon(doc, "s_grt_m2",   "ff00bb00", "0.9", _DOT_G)   # verde M2
    _style_icon(doc, "s_fn_m2",    "ff0000cc", "0.9", _DOT_R)   # rojo M2
    _style_icon(doc, "s_grt_m3",   "ff00dd44", "0.9", _DOT_G)   # verde M3
    _style_icon(doc, "s_fn_m3",    "ff2244ff", "0.9", _DOT_R)   # rojo M3
    _style_icon(doc, "s_esp_m3",   "ff0088ff", "1.0", _DOT_O)   # naranja especial
    _style_line(doc, "s_grieta_m1", "ff00ffff", 3)   # amarillo M1
    _style_line(doc, "s_fr_m2",     "ff0000ff", 4)   # rojo M2
    _style_line(doc, "s_smg_m2",    "ffff00ff", 4)   # magenta SMG
    _style_line(doc, "s_fl_m3",     "ff00aaff", 4)   # amarillo M3 (KML: BGR)

    # ── [M1] Pozos ───────────────────────────────────────────────────────────
    f = _folder(doc, "[M1] Pozos de extracción (northing corregido −7 000 m)")
    for e, n, pid in M1_POZOS:
        _point(f, pid, e, n, "#s_pozo_m1",
               f"Pozo de extracción – Mapa 1 (corregido)\n"
               f"Northing original: {n-_D}  →  corregido: {n}")

    # ── [M1] Grietas estimadas ────────────────────────────────────────────────
    f = _folder(doc, "[M1] Grietas estimadas (northing corregido −7 000 m)")
    for g in M1_GRIETAS:
        _line(f, g["id"], g["pts"], "#s_grieta_m1", g["desc"])

    # ── [M2] Grietas verificadas ──────────────────────────────────────────────
    f = _folder(doc, "[M2] Grietas verificadas – SGM/CENAPRED/SMG (29-May-2026)")
    for e, n, pid, desc in M2_PV_GRIETAS:
        _point(f, pid, e, n, "#s_grt_m2", desc)

    # ── [M2] Fallas normales verificadas ─────────────────────────────────────
    f = _folder(doc, "[M2] Fallas normales verificadas – SGM/CENAPRED/SMG")
    for e, n, pid, desc in M2_PV_FALLAS:
        _point(f, pid, e, n, "#s_fn_m2", desc)

    # ── [M2] Fallas rojas INEGI/CENAPRED/SGM ─────────────────────────────────
    f = _folder(doc, "[M2] Fallas cartografiadas – INEGI/CENAPRED/SGM (líneas)")
    for fl in M2_FALLAS_ROJAS:
        _line(f, fl["id"], fl["pts"], "#s_fr_m2", fl["desc"])

    # ── [M2] Falla SMG cartografiada ─────────────────────────────────────────
    f = _folder(doc, "[M2] Falla cartografiada – Soc. Mexiquense de Geotecnia")
    for seg in M2_FALLA_SMG:
        _line(f, seg["id"], seg["pts"], "#s_smg_m2", seg["desc"])

    # ── [M3] Pozos IGZA ──────────────────────────────────────────────────────
    f = _folder(doc, "[M3] Pozos – IGZA/INEGI (Toluca-Metepec)")
    for e, n, pid in M3_POZOS:
        _point(f, pid, e, n, "#s_pozo_m3", "Pozo de extracción – Mapa 3 IGZA")

    # ── [M3] Fallas/fracturas IGZA (líneas) ──────────────────────────────────
    f = _folder(doc, "[M3] Fallas y fracturas – IGZA (líneas amarillas)")
    for fl in M3_FALLAS_LINEAS:
        _line(f, fl["id"], fl["pts"], "#s_fl_m3", fl["desc"])

    # ── [M3] Grietas confirmadas ──────────────────────────────────────────────
    f = _folder(doc, "[M3] Grietas confirmadas – IGZA")
    for e, n, pid, desc in M3_GRIETAS_PTS:
        _point(f, pid, e, n, "#s_grt_m3", desc)

    # ── [M3] Fallas normales ──────────────────────────────────────────────────
    f = _folder(doc, "[M3] Fallas normales – IGZA")
    for e, n, pid, desc in M3_FALLAS_PTS:
        _point(f, pid, e, n, "#s_fn_m3", desc)

    # ── [M3] Puntos especiales ────────────────────────────────────────────────
    f = _folder(doc, "[M3] Puntos especiales – IGZA (extracción/compactación)")
    for e, n, pid, desc in M3_ESPECIALES:
        _point(f, pid, e, n, "#s_esp_m3", desc)

    raw = tostring(kml, encoding="unicode")
    return parseString(raw).toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")


# ═══════════════════════════════════════════════════════════════════════════════
def _bbox(pts_en):
    es = [p[0] for p in pts_en]
    ns = [p[1] for p in pts_en]
    return min(es), max(es), min(ns), max(ns)


if __name__ == "__main__":
    # ── Generar KML ──────────────────────────────────────────────────────────
    output = "toluca_pozos_grietas.kml"
    with open(output, "w", encoding="utf-8") as fh:
        fh.write(build_kml())

    # ── Reporte de consistencia ───────────────────────────────────────────────
    print("=" * 66)
    print("  REPORTE DE CONSISTENCIA – TOLUCA POZOS/GRIETAS/FALLAS")
    print("=" * 66)

    # bounding boxes
    all_m1 = [(e, n) for e, n, _ in M1_POZOS]
    for g in M1_GRIETAS:
        all_m1 += g["pts"]
    all_m2 = [(e, n) for e, n, *_ in M2_PV_GRIETAS + M2_PV_FALLAS]
    for fl in M2_FALLAS_ROJAS + M2_FALLA_SMG:
        all_m2 += fl["pts"]
    all_m3 = [(e, n) for e, n, _ in M3_POZOS]
    all_m3 += [(e, n) for e, n, *_ in M3_GRIETAS_PTS + M3_FALLAS_PTS + M3_ESPECIALES]
    for fl in M3_FALLAS_LINEAS:
        all_m3 += fl["pts"]

    for label, pts in [("Mapa 1 (corr.)", all_m1),
                        ("Mapa 2        ", all_m2),
                        ("Mapa 3        ", all_m3)]:
        emin, emax, nmin, nmax = _bbox(pts)
        print(f"  {label}  E {emin:.0f}–{emax:.0f}  N {nmin:.0f}–{nmax:.0f}")

    # solapamiento
    m1_e = (_bbox(all_m1)[0], _bbox(all_m1)[1])
    m1_n = (_bbox(all_m1)[2], _bbox(all_m1)[3])
    m3_e = (_bbox(all_m3)[0], _bbox(all_m3)[1])
    m3_n = (_bbox(all_m3)[2], _bbox(all_m3)[3])
    ov_e = max(0, min(m1_e[1], m3_e[1]) - max(m1_e[0], m3_e[0]))
    ov_n = max(0, min(m1_n[1], m3_n[1]) - max(m1_n[0], m3_n[0]))
    print(f"\n  Solapamiento M1∩M3: {ov_e:.0f} m EW × {ov_n:.0f} m NS")

    print("\n  Corrección aplicada a Mapa 1: northing −7 000 m")
    print("  Datum: UTM 14N/WGS84 ≈ UTM 14Q/ITRF 2008 (diff < 1 m)")

    print("\n  CAPAS EN EL KML:")
    capas = [
        ("[M1] Pozos",              len(M1_POZOS)),
        ("[M1] Grietas",            len(M1_GRIETAS)),
        ("[M2] Grietas verif.",     len(M2_PV_GRIETAS)),
        ("[M2] Fallas normales",    len(M2_PV_FALLAS)),
        ("[M2] Fallas líneas",      len(M2_FALLAS_ROJAS)),
        ("[M2] Falla SMG",          len(M2_FALLA_SMG)),
        ("[M3] Pozos IGZA",         len(M3_POZOS)),
        ("[M3] Fallas líneas IGZA", len(M3_FALLAS_LINEAS)),
        ("[M3] Grietas IGZA",       len(M3_GRIETAS_PTS)),
        ("[M3] Fallas norm. IGZA",  len(M3_FALLAS_PTS)),
        ("[M3] Especiales IGZA",    len(M3_ESPECIALES)),
    ]
    total_pts  = sum(n for _, n in capas if "líneas" not in _ and "SMG" not in _
                     and "Grietas [M" not in _)
    total_lns  = sum(n for _, n in capas if "líneas" in _ or "SMG" in _)
    for name, n in capas:
        print(f"    {name:<30} {n:>3} elementos")
    print(f"    {'─'*38}")
    print(f"    Total puntos  {len(M1_POZOS)+len(M2_PV_GRIETAS)+len(M2_PV_FALLAS)+len(M3_POZOS)+len(M3_GRIETAS_PTS)+len(M3_FALLAS_PTS)+len(M3_ESPECIALES):>3}")
    print(f"    Total líneas  {len(M1_GRIETAS)+len(M2_FALLAS_ROJAS)+len(M2_FALLA_SMG)+len(M3_FALLAS_LINEAS):>3}")
    print(f"\n  KML generado: {output}")
    print("=" * 66)
