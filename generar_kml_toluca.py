#!/usr/bin/env python3
"""
Genera toluca_pozos_grietas.kml con:
  - Pozos de extracción de agua subterránea (puntos azules)
  - Grietas en el suelo (líneas amarillas)

Coordenadas digitalizadas manualmente desde imagen cartográfica
(mapa impreso de Toluca de Lerdo, Estado de México).
Sistema de referencia original: UTM Zona 14N / WGS84 (EPSG:32614).

Dependencias:
    pip install pyproj

Uso:
    python generar_kml_toluca.py
    # Salida: toluca_pozos_grietas.kml (abrir en Google Earth / QGIS)
"""

from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom.minidom import parseString
from pyproj import Transformer

# ── Transformador UTM Z14N → WGS84 ──────────────────────────────────────────
transformer = Transformer.from_crs("EPSG:32614", "EPSG:4326", always_xy=True)

def utm_to_lonlat(easting: float, northing: float) -> tuple[float, float]:
    """Devuelve (lon, lat) en grados decimales WGS84."""
    lon, lat = transformer.transform(easting, northing)
    return lon, lat


# ── POZOS DE EXTRACCIÓN (puntos azules) ─────────────────────────────────────
# Coordenadas UTM Zona 14N estimadas por digitalización visual de la imagen.
# Referencia visible en la imagen: E 431114 y E 433514 en la parte superior.
# El centro urbano de Toluca (borde inferior-izquierdo del mapa) se ubica
# alrededor de E 431 000, N 2 133 700.
pozos_utm = [
    # (easting, northing, id)
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

# ── GRIETAS EN EL SUELO (líneas amarillas) ──────────────────────────────────
# Cada grieta es una polilínea definida por ≥2 vértices UTM.
grietas_utm = [
    {
        "id": "Grieta-01",
        "descripcion": "Par de trazos en X – zona noreste (área de San Lorenzo)",
        "puntos": [
            (430050, 2141400), (430450, 2141800),
        ],
    },
    {
        "id": "Grieta-02",
        "descripcion": "Par de trazos en X – zona noreste (cruce)",
        "puntos": [
            (430050, 2141800), (430450, 2141400),
        ],
    },
    {
        "id": "Grieta-03",
        "descripcion": "Trazo diagonal – norte-centro",
        "puntos": [
            (431200, 2141000), (431450, 2141300),
        ],
    },
    {
        "id": "Grieta-04",
        "descripcion": "Trazo diagonal corto – norte-centro",
        "puntos": [
            (431600, 2140950), (431850, 2141200),
        ],
    },
    {
        "id": "Grieta-05",
        "descripcion": "Grieta principal NNO-SSE – sector central (Isidro Fabela / Pino Suárez)",
        "puntos": [
            (431900, 2139900),
            (431930, 2139500),
            (431960, 2139100),
            (431990, 2138700),
            (432020, 2138300),
            (432050, 2137900),
        ],
    },
    {
        "id": "Grieta-06",
        "descripcion": "Par en X – zona suroeste (límite urbano)",
        "puntos": [
            (429800, 2139100), (430200, 2139500),
        ],
    },
    {
        "id": "Grieta-07",
        "descripcion": "Par en X – zona suroeste (cruce)",
        "puntos": [
            (429800, 2139500), (430200, 2139100),
        ],
    },
    {
        "id": "Grieta-08",
        "descripcion": "Trazo corto – franja suroeste",
        "puntos": [
            (430050, 2138650), (430350, 2138900),
        ],
    },
    {
        "id": "Grieta-09",
        "descripcion": "Trazo diagonal – zona este",
        "puntos": [
            (433950, 2139800), (434350, 2140100),
        ],
    },
    {
        "id": "Grieta-10",
        "descripcion": "Trazo vertical – zona este",
        "puntos": [
            (434400, 2139300), (434500, 2139750),
        ],
    },
    {
        "id": "Grieta-11",
        "descripcion": "Trazo curvo – extremo sureste",
        "puntos": [
            (434550, 2137850),
            (434800, 2137600),
            (435100, 2137500),
        ],
    },
    {
        "id": "Grieta-12",
        "descripcion": "Trazo corto – zona norte (Alfredo del Mazo)",
        "puntos": [
            (433500, 2142100), (433700, 2141800),
        ],
    },
]


# ── CONSTRUCCIÓN DEL KML ─────────────────────────────────────────────────────
def _coord_str(lon: float, lat: float, alt: float = 0.0) -> str:
    return f"{lon:.7f},{lat:.7f},{alt}"


def build_kml() -> str:
    kml = Element("kml", xmlns="http://www.opengis.net/kml/2.2")
    doc = SubElement(kml, "Document")
    SubElement(doc, "name").text = "Toluca – Pozos y Grietas"
    SubElement(doc, "description").text = (
        "Pozos de extracción de agua subterránea y grietas en el suelo "
        "digitalizados desde cartografía impresa de Toluca de Lerdo, "
        "Estado de México. Coordenadas aproximadas; validar con levantamiento GPS."
    )

    # ── Estilos ──────────────────────────────────────────────────────────────
    # Estilo pozos
    sty_pozo = SubElement(doc, "Style", id="estilo_pozo")
    icon_sty = SubElement(sty_pozo, "IconStyle")
    SubElement(icon_sty, "color").text = "ffff0000"   # AABBGGRR → azul
    SubElement(icon_sty, "scale").text = "1.1"
    icon = SubElement(icon_sty, "Icon")
    SubElement(icon, "href").text = (
        "http://maps.google.com/mapfiles/kml/shapes/water.png"
    )
    lbl_sty = SubElement(sty_pozo, "LabelStyle")
    SubElement(lbl_sty, "scale").text = "0.8"

    # Estilo grietas
    sty_grieta = SubElement(doc, "Style", id="estilo_grieta")
    line_sty = SubElement(sty_grieta, "LineStyle")
    SubElement(line_sty, "color").text = "ff00ffff"   # AABBGGRR → amarillo
    SubElement(line_sty, "width").text = "3"

    # ── Carpeta pozos ────────────────────────────────────────────────────────
    folder_pozos = SubElement(doc, "Folder")
    SubElement(folder_pozos, "name").text = "Pozos de extracción"
    SubElement(folder_pozos, "visibility").text = "1"

    for east, north, pid in pozos_utm:
        lon, lat = utm_to_lonlat(east, north)
        pm = SubElement(folder_pozos, "Placemark")
        SubElement(pm, "name").text = pid
        SubElement(pm, "styleUrl").text = "#estilo_pozo"
        SubElement(pm, "description").text = (
            f"Pozo de extracción de agua subterránea\n"
            f"UTM 14N  E: {east}  N: {north}"
        )
        pt = SubElement(pm, "Point")
        SubElement(pt, "coordinates").text = _coord_str(lon, lat)

    # ── Carpeta grietas ──────────────────────────────────────────────────────
    folder_grietas = SubElement(doc, "Folder")
    SubElement(folder_grietas, "name").text = "Grietas en el suelo"
    SubElement(folder_grietas, "visibility").text = "1"

    for grieta in grietas_utm:
        coords_kml = " ".join(
            _coord_str(*utm_to_lonlat(e, n)) for e, n in grieta["puntos"]
        )
        pm = SubElement(folder_grietas, "Placemark")
        SubElement(pm, "name").text = grieta["id"]
        SubElement(pm, "styleUrl").text = "#estilo_grieta"
        SubElement(pm, "description").text = grieta["descripcion"]
        ls = SubElement(pm, "LineString")
        SubElement(ls, "tessellate").text = "1"
        SubElement(ls, "coordinates").text = coords_kml

    raw_xml = tostring(kml, encoding="unicode")
    pretty = parseString(raw_xml).toprettyxml(indent="  ", encoding="utf-8")
    # toprettyxml agrega <?xml …?> propio; lo dejamos tal cual
    return pretty.decode("utf-8")


if __name__ == "__main__":
    output = "toluca_pozos_grietas.kml"
    kml_text = build_kml()
    with open(output, "w", encoding="utf-8") as f:
        f.write(kml_text)

    print(f"KML generado: {output}")
    print(f"  Pozos de extracción : {len(pozos_utm)}")
    print(f"  Grietas en el suelo : {len(grietas_utm)}")
    print()
    print("Abre el archivo en Google Earth Pro o QGIS para visualizarlo.")
    print("NOTA: Las coordenadas son estimadas por digitalización manual")
    print("      de la imagen fotográfica. Se recomienda validar con GPS.")
