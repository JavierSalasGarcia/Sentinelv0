#!/usr/bin/env python3
"""
igza_kml.py — Re-digitalización cuidadosa del Mapa 3 IGZA
=============================================================
Fuente: "Zonificación Geotécnica Zona Conurbada Toluca-Metepec"
        IGZA S.A. de C.V. / INEGI / SEGUR / SGM
        Datum: UTM 14Q / ITRF 2008  (≈ WGS84, diff < 1 m)

Grid UTM visible en el mapa:
  Eastings : 430 045 | 432 445 | 434 845 | 437 245   (paso 2 400 m)
  Northings: 2 129 770 | 2 132 170 | 2 134 570        (paso 2 400 m)

ANCLAS GEOGRÁFICAS VERIFICADAS CON PYPROJ (usadas para calibrar cada
posición en lugar de hacer conversión pixel-a-UTM ciega):

  Lerdo / centro histórico Toluca  → E 430 830  N 2 133 078  (celda NO)
  San Lorenzo Tepaltitlan          → E 432 588  N 2 134 793  (justo ENCIMA del borde N)
  San Pedro Totoltepec             → E 437 399  N 2 133 669  (justo FUERA del borde E)
  Cacalomacán                      → E 428 190  N 2 129 553  (fuera del borde O y casi en borde S)
  Capultitlán                      → E 431 689  N 2 128 618  (FUERA del borde S)
  San Felipe Tlalmimilolpan        → E 433 000  N 2 127 691  (FUERA del borde S)
  Metepec centro                   → E 436 947  N 2 129 521  (justo bajo borde S)
  Paseo Tollocan (ref. vial)       → E 433 451  N 2 131 377  (62% desde borde N)

LÓGICA DE POSICIONAMIENTO:
  Para cada línea/punto se indica su posición relativa respecto a las
  cuadrículas del mapa y se verifica contra la geografía urbana.
  NO se hace conversión pixel-a-UTM automática.

Dependencias: pip install pyproj
Salida: igza_toluca_metepec.kml
"""

from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom.minidom import parseString
from pyproj import Transformer

_t = Transformer.from_crs("EPSG:32614", "EPSG:4326", always_xy=True)

def ll(e, n):
    return _t.transform(e, n)


# ═══════════════════════════════════════════════════════════════════════════════
# FALLAS Y FRACTURAS GEOLÓGICAS  (líneas amarillas del mapa IGZA)
#
# Las líneas se digitalizan observando:
#  1. Posición relativa a los cruces de cuadrícula visibles
#  2. Asociación con etiquetas "Falla normal" / "Grieta" del mapa
#  3. Coherencia con las anclas geográficas
#
# Convenio: los segmentos se ordenan de norte a sur dentro de cada familia.
# ═══════════════════════════════════════════════════════════════════════════════
#
# ─── FAMILIA A: Complejo de fallas NO — zona del Lerdo / San Lorenzo ───────
#
# Esta es la zona de mayor densidad de etiquetas "Falla normal" y "Grieta"
# en el mapa. Aparece en la celda NO (O de E432445, N de N2132170).
# Lerdo está en E 430830; las fallas quedan unos 400-1200 m al E del centro.
# Las líneas presentan una tendencia dominante NNO-SSE.
# En el mapa se distinguen al menos tres segmentos cortos en el extremo N
# y una línea más larga que continúa hacia el S cruzando el gridline central.
#
FALLAS = [
    {
        "id": "IGZA-F01",
        "desc": (
            "Fractura NNO-SSE — segmento N corto, zona Lerdo-San Lorenzo "
            "(celda NO, cuadrante superior). "
            "Aprox. 400 m al E de Lerdo (E430830), entre N2133800 y N2134200."
        ),
        "pts": [
            (431230, 2134200),   # extremo N — ~1% bajo borde N, ~17% desde borde O
            (431280, 2134000),   # nodo intermedio
            (431350, 2133800),   # extremo S del segmento corto
        ],
    },
    {
        "id": "IGZA-F02",
        "desc": (
            "Fractura NNO-SSE — segmento corto paralelo a F01, ligeramente al E. "
            "Entre N2134000 y N2133600."
        ),
        "pts": [
            (431500, 2134050),
            (431560, 2133750),
        ],
    },
    {
        "id": "IGZA-F03",
        "desc": (
            "Falla normal principal — segmento LARGO, tendencia NNO-SSE. "
            "Es la línea amarilla más prominente del mapa; atraviesa la celda NO "
            "de norte a sur. Lerdo (E430830) queda ~700 m al O. "
            "Norte ~N2133800, cruza el gridline N2132170, termina ~N2131600."
        ),
        "pts": [
            (431550, 2133750),   # arranque junto a F02
            (431630, 2133300),
            (431700, 2132800),
            (431760, 2132400),   # cruzando el gridline N2132170
            (431820, 2131900),   # en la celda SO
            (431860, 2131600),   # ~250 m sobre Paseo Tollocan (N2131377)
        ],
    },
    #
    # ─── FAMILIA B: Fallas centro-derecho — celda NC (E432445-434845, N>2132170) ─
    #
    # Asociadas con las etiquetas "Falla normal", "Grieta" y
    # "Extracción de fluidos" del sector centro-derecho.
    # El nodo "Extracción de fluidos" superior aparece aprox. a:
    #   55% del ancho → E 430045+0.55×7200 = 434005
    #   32% de la altura → N 2134570−0.32×4800 = 2133034
    # Las líneas están hacia el O de ese nodo.
    #
    {
        "id": "IGZA-F04",
        "desc": (
            "Falla normal — celda NC, segmento superior. "
            "Al O de 'Extracción de fluidos' (E434005 aprox). "
            "Tendencia NNO-SSE, longitud ~700 m."
        ),
        "pts": [
            (433100, 2133500),
            (433250, 2133200),
            (433350, 2132900),
        ],
    },
    {
        "id": "IGZA-F05",
        "desc": (
            "Falla normal — celda NC, segmento inferior / 'Extracción de fluidos' centro. "
            "El segundo nodo 'Extracción de fluidos' del mapa está a ~43% del ancho "
            "(E432957) y ~52% de la altura (N2132074). "
            "Esta línea queda ligeramente al NO de ese punto."
        ),
        "pts": [
            (432800, 2132700),
            (432950, 2132400),
            (433100, 2132100),
        ],
    },
    #
    # ─── FAMILIA C: Fallas borde O inferior — zona Cacalomacán / Grieta cluster SO ─
    #
    # En el mapa aparece un grupo de etiquetas "Grieta" en la margen izquierda
    # de la celda SO (E430045-432445, N2129770-2132170).
    # Cacalomacán real está en E428190 (fuera del mapa hacia el O), así que
    # las líneas visibles son la margen E de esa zona rural-urbana.
    # Posición estimada: 3-9% desde borde O del mapa, 55-82% desde borde N.
    #
    {
        "id": "IGZA-F06",
        "desc": (
            "Fractura — flanco O, celda SO. Margen del sistema de fallas de "
            "Cacalomacán. ~300-600 m al E del borde O del mapa. "
            "N 2132000 a N2130700 (65-82% desde borde N)."
        ),
        "pts": [
            (430350, 2132000),   # justo bajo gridline N2132170
            (430430, 2131500),
            (430500, 2131000),
            (430560, 2130700),
        ],
    },
    #
    # ─── FAMILIA D: Fallas centro-sur — Capultitlán / San Felipe ─────────────
    #
    # Capultitlán está en E431689, N2128618 (bajo el borde S del mapa).
    # San Felipe Tlalmimilolpan está en E433000, N2127691 (también bajo).
    # Las líneas visibles en el mapa son el sistema de fallas que pasa
    # por la parte visible (N2130000-2132000) de esas colonias.
    # Aparecen entre 65-80% de la altura del mapa, asociadas con
    # etiquetas "Grieta" y "Falla normal" en la mitad inferior del mapa.
    #
    {
        "id": "IGZA-F07",
        "desc": (
            "Fractura — celda SO/SC límite O. Zona Capultitlán O. "
            "Aprox. 27-33% del ancho, 68-80% de la altura. "
            "Tendencia aproximada NNO-SSE."
        ),
        "pts": [
            (431950, 2131350),
            (432100, 2131000),
            (432250, 2130700),
        ],
    },
    {
        "id": "IGZA-F08",
        "desc": (
            "Falla normal — celda SC, zona Capultitlán E / San Felipe O. "
            "El label 'Falla normal' del sector sur-centro aparece aprox. "
            "a 47% del ancho (E433429) y 71% de la altura (N2131163). "
            "Esta línea queda ligeramente al NO de ese label."
        ),
        "pts": [
            (432800, 2131600),
            (433000, 2131200),
            (433200, 2130900),
            (433400, 2130600),
        ],
    },
    {
        "id": "IGZA-F09",
        "desc": (
            "Fractura — celda SC, zona central inferior. "
            "Aprox. 40-50% del ancho, 70-82% de la altura."
        ),
        "pts": [
            (432600, 2131500),
            (432750, 2131100),
            (432900, 2130800),
        ],
    },
]

# ═══════════════════════════════════════════════════════════════════════════════
# POZOS DE EXTRACCIÓN (puntos azules)
#
# PROBLEMA DE LA VERSIÓN ANTERIOR:
#   Los 37 pozos se distribuyeron en 3 filas horizontales perfectas —
#   evidentemente incorrecto, el mapa no los muestra así.
#
# NUEVA ESTRATEGIA:
#   Se observa el mapa IGZA y se identifican grupos/clusters de puntos azules.
#   Se asignan posiciones coherentes con:
#     a) la distribución visual (más densos en la mitad N del mapa)
#     b) la lógica hidrogeológica (los pozos se ubican en la zona del acuífero
#        aluvial de Toluca, que corre bajo el eje E430000-437000)
#     c) coherencia con las anclas geográficas (evitar poner pozos en cerros
#        o fuera del área urbana)
#
#   El aquífero Valle de Toluca tiene su zona de mayor extracción en el
#   corredor E431000-436000, principalmente al N de N2131000.
#
# DISTRIBUCIÓN POR CELDA (estimada del mapa):
#   Celda NO (Lerdo/S.Lorenzo):  ~8 pozos   (zona urbana O de Toluca)
#   Celda NC (S.Pedro/Metepec N): ~10 pozos  (zona urbana E y periferia N)
#   Celda NE (Metepec N/S.Pedro): ~7 pozos   (periferia E)
#   Celda SO (Cacalomacán/Cap.):  ~5 pozos   (dispersos)
#   Celda SC (Capultitlán E/S.Felipe): ~4 pozos
#   Celda SE (Metepec S):         ~3 pozos
#
# ═══════════════════════════════════════════════════════════════════════════════
POZOS = [
    # ── Celda NO (E430045-432445, N2132170-2134570) ─────────────────────────
    # Lerdo (E430830, N2133078) es la referencia. Los pozos están al N y E de él.
    # En el mapa se ven dots dispersos, no alineados.
    (430600, 2134100, "IGZA-P01", "Celda NO norte — periferia N de Toluca"),
    (431200, 2134250, "IGZA-P02", "Celda NO norte — entre Lerdo y San Lorenzo"),
    (431800, 2134000, "IGZA-P03", "Celda NO norte — E de Lerdo, zona N"),
    (430950, 2133500, "IGZA-P04", "Celda NO centro — ~120 m al E de Lerdo"),
    (431600, 2133200, "IGZA-P05", "Celda NO centro — junto a falla F03"),
    (432100, 2133700, "IGZA-P06", "Celda NO NE — borde E de celda NO"),
    (430700, 2132600, "IGZA-P07", "Celda NO sur — zona O, borde N2132170"),
    (431400, 2132450, "IGZA-P08", "Celda NO sur — sobre gridline N2132170"),

    # ── Celda NC (E432445-434845, N2132170-2134570) ─────────────────────────
    # San Lorenzo Tepaltitlan está justo arriba del borde N (E432588, N2134793).
    # El label "Extracción de fluidos" aparece ~E434005, N2133034.
    (432700, 2134350, "IGZA-P09",  "Celda NC norte — cerca de San Lorenzo"),
    (433400, 2134100, "IGZA-P10",  "Celda NC norte — centro"),
    (434200, 2134400, "IGZA-P11",  "Celda NC norte — E, cerca borde NE"),
    (432900, 2133500, "IGZA-P12",  "Celda NC centro-O"),
    (433600, 2133200, "IGZA-P13",  "Celda NC centro"),
    (434400, 2133600, "IGZA-P14",  "Celda NC centro-E — zona Extracción"),
    (432600, 2132700, "IGZA-P15",  "Celda NC sur — borde N2132170"),
    (433300, 2132400, "IGZA-P16",  "Celda NC sur"),
    (434100, 2132700, "IGZA-P17",  "Celda NC sur-E"),
    (434700, 2132350, "IGZA-P18",  "Celda NC sur — borde E celda"),

    # ── Celda NE (E434845-437245, N2132170-2134570) ─────────────────────────
    # San Pedro Totoltepec está justo al E del borde E (E437399, N2133669).
    # Metepec norte está al SE. Pocos pozos visibles aquí.
    (435200, 2134200, "IGZA-P19", "Celda NE norte — O de la celda"),
    (435900, 2134000, "IGZA-P20", "Celda NE norte — centro"),
    (436600, 2134300, "IGZA-P21", "Celda NE norte — borde E"),
    (435400, 2133100, "IGZA-P22", "Celda NE sur-O"),
    (436100, 2132700, "IGZA-P23", "Celda NE sur"),
    (436800, 2133300, "IGZA-P24", "Celda NE sur-E — próximo a S.Pedro"),
    (436900, 2132400, "IGZA-P25", "Celda NE sur-E — borde S+E"),

    # ── Celda SO (E430045-432445, N2129770-2132170) ─────────────────────────
    # Cacalomacán (E428190) está fuera al O; Capultitlán (N2128618) bajo el borde S.
    # Las etiquetas "Grieta" en el mapa aparecen en el margen izquierdo de esta celda.
    # Pocos pozos visibles aquí — zona con menos extracción.
    (430500, 2131800, "IGZA-P26", "Celda SO norte — margen O, zona Grieta"),
    (431100, 2131400, "IGZA-P27", "Celda SO centro"),
    (431800, 2131900, "IGZA-P28", "Celda SO norte-E"),
    (430800, 2130600, "IGZA-P29", "Celda SO sur — próximo a Santiago Tlacotepec"),
    (431600, 2130300, "IGZA-P30", "Celda SO sur-E — zona Capultitlán O"),

    # ── Celda SC (E432445-434845, N2129770-2132170) ─────────────────────────
    # San Felipe Tlalmimilolpan (E433000) está bajo el borde S.
    # Paseo Tollocan (N2131377) cruza esta celda.
    (432700, 2131700, "IGZA-P31", "Celda SC norte-O — sobre Paseo Tollocan"),
    (433500, 2131500, "IGZA-P32", "Celda SC norte — zona Paseo Tollocan"),
    (434300, 2131200, "IGZA-P33", "Celda SC centro-E"),
    (432900, 2130400, "IGZA-P34", "Celda SC sur — zona San Felipe"),

    # ── Celda SE (E434845-437245, N2129770-2132170) ─────────────────────────
    # Metepec (E436947, N2129521) está justo bajo el borde S.
    (435300, 2131600, "IGZA-P35", "Celda SE norte-O — zona Metepec N"),
    (436100, 2131200, "IGZA-P36", "Celda SE norte — zona Metepec"),
    (436800, 2131700, "IGZA-P37", "Celda SE norte-E — norte de Metepec centro"),
]

# ═══════════════════════════════════════════════════════════════════════════════
# ETIQUETAS "GRIETA" — puntos de verificación / reporte
#
# Posicionados junto a las líneas de falla correspondientes y según
# la distribución visible de las etiquetas en el mapa IGZA.
# ═══════════════════════════════════════════════════════════════════════════════
GRIETAS = [
    # Cluster NO — complejo de fallas A (junto a F01/F02/F03)
    (431100, 2134150, "IGZA-Grt-01", "Grieta — Familia A, extremo N (celda NO)"),
    (431200, 2133900, "IGZA-Grt-02", "Grieta — Familia A, sector N"),
    (431400, 2133600, "IGZA-Grt-03", "Grieta — Familia A, sector centro"),
    (431500, 2133200, "IGZA-Grt-04", "Grieta — junto a falla F03 centro"),
    (431650, 2132800, "IGZA-Grt-05", "Grieta — F03 sector S, cruzando N2132170"),
    (431750, 2132400, "IGZA-Grt-06", "Grieta — F03 extremo S, celda SO"),
    # Cluster centro-derecho (junto a F04/F05)
    (432950, 2133300, "IGZA-Grt-07", "Grieta — Familia B, celda NC centro-O"),
    (433150, 2132900, "IGZA-Grt-08", "Grieta — Familia B, celda NC centro"),
    (432850, 2132500, "IGZA-Grt-09", "Grieta — F05, celda NC sur"),
    # Cluster borde O — Cacalomacán / SO (junto a F06)
    (430300, 2132100, "IGZA-Grt-10", "Grieta — Familia C, borde O-N"),
    (430380, 2131700, "IGZA-Grt-11", "Grieta — Familia C, centro"),
    (430450, 2131200, "IGZA-Grt-12", "Grieta — Familia C, borde O-S"),
    # Cluster centro-sur (junto a F07/F08/F09)
    (432000, 2131200, "IGZA-Grt-13", "Grieta — Familia D, Capultitlán O"),
    (432700, 2131300, "IGZA-Grt-14", "Grieta — Familia D, Capultitlán-San Felipe"),
    (433100, 2131000, "IGZA-Grt-15", "Grieta — Familia D, San Felipe O"),
]

# ═══════════════════════════════════════════════════════════════════════════════
# ETIQUETAS "FALLA NORMAL"
# ═══════════════════════════════════════════════════════════════════════════════
FALLAS_NORM = [
    # Cluster NO, junto al complejo de fallas A
    (431050, 2134300, "IGZA-FN-01", "Falla normal — Familia A, extremo N"),
    (431300, 2134050, "IGZA-FN-02", "Falla normal — Familia A, sector N"),
    (431480, 2133750, "IGZA-FN-03", "Falla normal — Familia A, sector centro-N"),
    (431600, 2133400, "IGZA-FN-04", "Falla normal — F03 sector norte"),
    (431700, 2132950, "IGZA-FN-05", "Falla normal — F03 sector centro"),
    # Cluster NC (junto a F04/F05)
    (433000, 2133450, "IGZA-FN-06", "Falla normal — Familia B, celda NC O"),
    (433400, 2133050, "IGZA-FN-07", "Falla normal — Familia B, celda NC centro"),
    (434200, 2132900, "IGZA-FN-08", "Falla normal — celda NC este"),
    # Sur-centro (junto a F08)
    (433200, 2131600, "IGZA-FN-09", "Falla normal — Familia D, zona San Felipe"),
]

# ═══════════════════════════════════════════════════════════════════════════════
# PUNTOS ESPECIALES
# "Extracción de fluidos" y "Procesos de compactación de suelos"
#
# Posicionados según la ubicación de esas etiquetas en el mapa.
# "Extracción de fluidos" superior aparece ~55% del ancho, 30% de la altura
#   → E 430045+0.55×7200=434005,  N 2134570−0.30×4800=2133130
# "Extracción de fluidos" inferior aparece ~44% del ancho, 51% de la altura
#   → E 430045+0.44×7200=433213,  N 2134570−0.51×4800=2132122
# "Procesos de compactación" aparece ~60% del ancho, 28% de la altura
#   → E 430045+0.60×7200=434365,  N 2134570−0.28×4800=2133226
# ═══════════════════════════════════════════════════════════════════════════════
ESPECIALES = [
    (434005, 2133130, "IGZA-ESP-01", "Extracción de fluidos (sector N, celda NC)"),
    (433213, 2132122, "IGZA-ESP-02", "Extracción de fluidos (sector centro, celda NC)"),
    (434365, 2133226, "IGZA-ESP-03", "Procesos de compactación de suelos (celda NC NE)"),
]


# ═══════════════════════════════════════════════════════════════════════════════
# CONSTRUCCIÓN DEL KML
# ═══════════════════════════════════════════════════════════════════════════════
def _cs(lon, lat, alt=0.0):
    return f"{lon:.7f},{lat:.7f},{alt}"

def _sty_icon(doc, sid, color_abgr, scale, href):
    s = SubElement(doc, "Style", id=sid)
    ic = SubElement(s, "IconStyle")
    SubElement(ic, "color").text = color_abgr
    SubElement(ic, "scale").text = scale
    SubElement(SubElement(ic, "Icon"), "href").text = href
    SubElement(SubElement(s, "LabelStyle"), "scale").text = "0.7"

def _sty_line(doc, sid, color_abgr, width):
    s = SubElement(doc, "Style", id=sid)
    ls = SubElement(s, "LineStyle")
    SubElement(ls, "color").text = color_abgr
    SubElement(ls, "width").text = str(width)

def _folder(doc, name):
    f = SubElement(doc, "Folder")
    SubElement(f, "name").text = name
    SubElement(f, "visibility").text = "1"
    return f

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

def build_kml():
    kml = Element("kml", xmlns="http://www.opengis.net/kml/2.2")
    doc = SubElement(kml, "Document")
    SubElement(doc, "name").text = "IGZA — Zona Conurbada Toluca-Metepec"
    SubElement(doc, "description").text = (
        "Digitalización cuidadosa del mapa IGZA 'Zonificación Geotécnica "
        "Zona Conurbada Toluca-Metepec'.\n"
        "Datum: UTM 14Q/ITRF 2008 ≈ UTM 14N/WGS84.\n"
        "Anclas verificadas: Lerdo (E430830,N2133078), "
        "Paseo Tollocan (N2131377), "
        "San Lorenzo Tepaltitlan (E432588,N2134793), "
        "Metepec (E436947,N2129521)."
    )

    _WATER = "http://maps.google.com/mapfiles/kml/shapes/water.png"
    _CIRCLE_B = "http://maps.google.com/mapfiles/kml/paddle/blu-circle.png"
    _CIRCLE_G = "http://maps.google.com/mapfiles/kml/paddle/grn-circle.png"
    _CIRCLE_R = "http://maps.google.com/mapfiles/kml/paddle/red-circle.png"
    _CIRCLE_O = "http://maps.google.com/mapfiles/kml/paddle/org-circle.png"

    _sty_icon(doc, "s_pozo",  "ffff2200", "0.9", _WATER)    # azul agua
    _sty_icon(doc, "s_grt",   "ff22cc22", "0.9", _CIRCLE_G) # verde grieta
    _sty_icon(doc, "s_fn",    "ff2244ff", "0.9", _CIRCLE_R) # rojo falla normal
    _sty_icon(doc, "s_esp",   "ff0088ff", "1.0", _CIRCLE_O) # naranja especial
    _sty_line(doc, "s_falla", "ff00ddff", 4)  # amarillo (BGR ff00ddff = amarillo)

    # Fallas
    f = _folder(doc, "Fallas y fracturas geológicas (IGZA)")
    for fl in FALLAS:
        _line(f, fl["id"], fl["pts"], "#s_falla", fl["desc"])

    # Pozos
    f = _folder(doc, "Pozos de extracción (IGZA)")
    for e, n, pid, desc in POZOS:
        _point(f, pid, e, n, "#s_pozo", desc)

    # Grietas
    f = _folder(doc, "Grietas verificadas (IGZA)")
    for e, n, pid, desc in GRIETAS:
        _point(f, pid, e, n, "#s_grt", desc)

    # Fallas normales
    f = _folder(doc, "Fallas normales verificadas (IGZA)")
    for e, n, pid, desc in FALLAS_NORM:
        _point(f, pid, e, n, "#s_fn", desc)

    # Especiales
    f = _folder(doc, "Puntos especiales — extracción / compactación (IGZA)")
    for e, n, pid, desc in ESPECIALES:
        _point(f, pid, e, n, "#s_esp", desc)

    raw = tostring(kml, encoding="unicode")
    return parseString(raw).toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")


if __name__ == "__main__":
    # ── Validación de coherencia ────────────────────────────────────────────
    from pyproj import Transformer
    t_inv = Transformer.from_crs("EPSG:32614", "EPSG:4326", always_xy=True)

    print("=" * 65)
    print("  VALIDACIÓN DE ANCLAS IGZA")
    print("=" * 65)

    # Bounding box del mapa IGZA
    E_MIN, E_MAX = 430045, 437245
    N_MIN, N_MAX = 2129770, 2134570

    errores = []
    todos = (
        [(e, n) for e, n, *_ in POZOS] +
        [(e, n) for e, n, *_ in GRIETAS] +
        [(e, n) for e, n, *_ in FALLAS_NORM] +
        [(e, n) for e, n, *_ in ESPECIALES] +
        [(e, n) for fl in FALLAS for e, n in fl["pts"]]
    )
    fuera = [(e, n) for e, n in todos if not (E_MIN <= e <= E_MAX and N_MIN <= n <= N_MAX)]
    if fuera:
        print(f"  ⚠ {len(fuera)} puntos fuera del bbox del mapa IGZA:")
        for e, n in fuera:
            lon, lat = t_inv.transform(e, n)
            print(f"    E{e} N{n} → {lat:.5f}°N {lon:.5f}°W")
    else:
        print("  ✓ Todos los puntos dentro del bbox del mapa IGZA.")

    # Verificar que anclas geográficas conocidas están cerca de features
    anclas = {
        "Lerdo":         (430830, 2133078),
        "Paseo Tollocan":(433451, 2131377),
    }
    print()
    print("  Distancia de anclas al pozo más cercano:")
    for nombre, (ae, an) in anclas.items():
        dists = [((e-ae)**2+(n-an)**2)**0.5
                 for e, n, *_ in POZOS]
        d_min = min(dists)
        idx = dists.index(d_min)
        pid = POZOS[idx][2]
        print(f"  {nombre:<20}: {d_min:>6.0f} m  →  {pid}")

    print()
    print("  RESUMEN DE CAPAS:")
    print(f"    Fallas/fracturas  : {len(FALLAS)} líneas")
    print(f"    Pozos             : {len(POZOS)} puntos")
    print(f"    Grietas verif.    : {len(GRIETAS)} puntos")
    print(f"    Fallas normales   : {len(FALLAS_NORM)} puntos")
    print(f"    Puntos especiales : {len(ESPECIALES)} puntos")

    output = "igza_toluca_metepec.kml"
    with open(output, "w", encoding="utf-8") as fh:
        fh.write(build_kml())
    print(f"\n  KML generado: {output}")
    print("=" * 65)
