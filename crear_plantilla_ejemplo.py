#!/usr/bin/env python3
"""
Crea plantillas de EJEMPLO (fondos de prueba) para cada marca, solo para ver
cómo queda el layout ANTES de que subas tu diseño real de Illustrator/Photoshop.

Genera un PNG por marca en ./plantillas con un encabezado, el color de la marca
y un pie. Reemplaza estos PNG por tus exportaciones reales (mismo nombre de
archivo) cuando las tengas.

Uso:
    python crear_plantilla_ejemplo.py
"""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from generar_credenciales import cargar_fuente

# 10 x 15 cm a 300 DPI, vertical.
ANCHO, ALTO = 1181, 1772


def hex_a_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def main() -> None:
    marcas = {}
    if Path("marcas.json").exists():
        marcas = {k: v for k, v in json.load(open("marcas.json", encoding="utf-8")).items()
                  if not k.startswith("_")}

    Path("plantillas").mkdir(exist_ok=True)

    # nombre de archivo esperado por marca (igual que en plantillas.json)
    archivos = {
        "Taller Antumalal": "taller_antumalal.png",
        "Antumalal Autopartes": "antumalal_autopartes.png",
        "Presto Car Service": "presto_car_service.png",
    }

    for marca, archivo in archivos.items():
        color = hex_a_rgb(marcas.get(marca, {}).get("color", "#334155"))
        img = Image.new("RGB", (ANCHO, ALTO), color)
        d = ImageDraw.Draw(img)

        # Banda superior más oscura + nombre de la marca
        d.rectangle((0, 0, ANCHO, int(ALTO * 0.16)),
                    fill=tuple(int(c * 0.6) for c in color))
        f_tit = cargar_fuente(int(ALTO * 0.045), True, {})
        tb = d.textbbox((0, 0), marca, font=f_tit)
        d.text(((ANCHO - (tb[2] - tb[0])) / 2, int(ALTO * 0.055)), marca,
               fill="#FFFFFF", font=f_tit)

        # Aviso de que es plantilla de ejemplo
        f_avi = cargar_fuente(int(ALTO * 0.018), False, {})
        aviso = "PLANTILLA DE EJEMPLO — reemplázala por tu diseño real"
        ab = d.textbbox((0, 0), aviso, font=f_avi)
        d.text(((ANCHO - (ab[2] - ab[0])) / 2, int(ALTO * 0.965)), aviso,
               fill="#FFFFFF", font=f_avi)

        ruta = Path("plantillas") / archivo
        img.save(ruta, dpi=(300, 300))
        print(f"  ✔ {ruta}")

    print("\nListo. Estos son fondos de PRUEBA. Cuando tengas tu diseño real,")
    print("expórtalo con el MISMO nombre de archivo y sobreescribe estos.")


if __name__ == "__main__":
    main()
