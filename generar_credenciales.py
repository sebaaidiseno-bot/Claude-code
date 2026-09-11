#!/usr/bin/env python3
"""
Generador de credenciales sobre TU plantilla exportada.

Toma el diseño que exportaste desde Illustrator/Photoshop (una imagen PNG por
marca, a tamaño final) y le superpone, por cada persona del CSV:
  - su foto (ya editada por ti),
  - nombre, cargo, teléfono/correo,
  - el QR de contacto (vCard) para "Agregar contacto".

NO dibuja el diseño: usa tu plantilla tal cual como fondo. Las posiciones de la
foto, los textos y el QR se definen en 'plantillas.json' con coordenadas en
fracción (0 a 1) del tamaño de la imagen, así funciona con cualquier resolución.

Flujo:
  1. La gente sube su foto en el Google Form.
  2. Editas las fotos y las guardas en ./fotos nombradas por persona:
        ana_perez_soto.jpg   (minúsculas, sin acentos, guion bajo)
     Si no encuentra la foto, el script te dice el nombre exacto que espera.
  3. Exportas tu plantilla por marca a ./plantillas (PNG a tamaño final).
  4. Ajustas posiciones en plantillas.json (o usa las de ejemplo).
  5. Ejecutas:
        python generar_credenciales.py respuestas.csv
  6. Salen los PNG en ./credenciales  (y un PDF con todas si usas --pdf).

Requiere: pip install -r requirements.txt
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont, ImageOps
except ImportError:
    sys.exit("Falta Pillow. Instala con: pip install -r requirements.txt")

from generar_qr import (
    cargar_empresas,
    construir_mapa,
    crear_vcard,
    nombre_archivo,
    normalizar,
    normalizar_tel,
    qr_pil,
)

# Rutas típicas de fuentes en Linux (DejaVu viene casi siempre instalada).
FUENTES_REGULAR = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
]
FUENTES_BOLD = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]


# ---------------------------------------------------------------------------
# Fuentes
# ---------------------------------------------------------------------------

def _primera_existente(rutas: list[str], override: str | None) -> str | None:
    if override and Path(override).exists():
        return override
    for r in rutas:
        if Path(r).exists():
            return r
    return None


def cargar_fuente(tam_px: int, bold: bool, cfg_fuentes: dict):
    ruta = _primera_existente(
        FUENTES_BOLD if bold else FUENTES_REGULAR,
        cfg_fuentes.get("bold" if bold else "regular"),
    )
    if ruta:
        return ImageFont.truetype(ruta, tam_px)
    return ImageFont.load_default()


def ancho_texto(draw, texto, fuente):
    izq, arr, der, aba = draw.textbbox((0, 0), texto, font=fuente)
    return der - izq, aba - arr


# ---------------------------------------------------------------------------
# Composición
# ---------------------------------------------------------------------------

def pegar_foto(base: Image.Image, foto: Image.Image, box: dict) -> None:
    W, H = base.size
    w = int(box["w"] * W)
    h = int(box["h"] * H)
    cx = int(box["x"] * W)
    cy = int(box["y"] * H)
    x0, y0 = cx - w // 2, cy - h // 2

    foto = ImageOps.exif_transpose(foto).convert("RGBA")
    foto = ImageOps.fit(foto, (w, h), method=Image.LANCZOS)

    if box.get("forma") == "circulo":
        mascara = Image.new("L", (w, h), 0)
        ImageDraw.Draw(mascara).ellipse((0, 0, w, h), fill=255)
        base.paste(foto, (x0, y0), mascara)
    else:
        radio = int(box.get("radio", 0) * min(w, h))
        if radio > 0:
            mascara = Image.new("L", (w, h), 0)
            ImageDraw.Draw(mascara).rounded_rectangle((0, 0, w, h), radio, fill=255)
            base.paste(foto, (x0, y0), mascara)
        else:
            base.paste(foto, (x0, y0), foto)


def dibujar_placeholder_foto(base: Image.Image, box: dict, iniciales: str) -> None:
    """Recuadro gris con iniciales cuando falta la foto (para no frenar el lote)."""
    W, H = base.size
    w, h = int(box["w"] * W), int(box["h"] * H)
    cx, cy = int(box["x"] * W), int(box["y"] * H)
    x0, y0 = cx - w // 2, cy - h // 2
    d = ImageDraw.Draw(base)
    if box.get("forma") == "circulo":
        d.ellipse((x0, y0, x0 + w, y0 + h), fill=(200, 200, 200))
    else:
        d.rounded_rectangle((x0, y0, x0 + w, y0 + h),
                            int(box.get("radio", 0) * min(w, h)), fill=(200, 200, 200))
    f = cargar_fuente(int(h * 0.4), True, {})
    tw, th = ancho_texto(d, iniciales, f)
    d.text((cx - tw / 2, cy - th / 2), iniciales, fill=(120, 120, 120), font=f)


def dibujar_texto(base: Image.Image, texto: str, cfg: dict, cfg_fuentes: dict) -> None:
    if not texto:
        return
    W, H = base.size
    d = ImageDraw.Draw(base)
    bold = bool(cfg.get("bold"))
    tam = max(8, int(cfg.get("tam", 0.04) * H))
    color = cfg.get("color", "#FFFFFF")
    align = cfg.get("align", "center")
    # Ancho máximo permitido (fracción del ancho de la imagen).
    max_w = cfg.get("max_w", 0.9) * W

    fuente = cargar_fuente(tam, bold, cfg_fuentes)
    tw, _ = ancho_texto(d, texto, fuente)
    while tw > max_w and tam > 8:  # auto-reduce si no cabe
        tam -= 2
        fuente = cargar_fuente(tam, bold, cfg_fuentes)
        tw, _ = ancho_texto(d, texto, fuente)

    cx, cy = cfg.get("x", 0.5) * W, cfg.get("y", 0.5) * H
    if align == "left":
        x = cx
    elif align == "right":
        x = cx - tw
    else:
        x = cx - tw / 2
    _, th = ancho_texto(d, texto, fuente)
    d.text((x, cy - th / 2), texto, fill=color, font=fuente)


def pegar_qr(base: Image.Image, contenido: str, cfg: dict) -> None:
    W, _ = base.size
    lado = int(cfg.get("tam", 0.25) * W)
    qr = qr_pil(contenido, box_size=10, border=1).convert("RGBA")
    qr = qr.resize((lado, lado), Image.NEAREST)
    if cfg.get("fondo_blanco", True):
        pad = int(lado * 0.06)
        placa = Image.new("RGBA", (lado + 2 * pad, lado + 2 * pad), (255, 255, 255, 255))
        placa.paste(qr, (pad, pad))
        qr = placa
    qw, qh = qr.size
    cx, cy = int(cfg.get("x", 0.5) * W), int(cfg.get("y", 0.85) * base.size[1])
    base.paste(qr, (cx - qw // 2, cy - qh // 2), qr)


def iniciales(nombre: str) -> str:
    partes = [p for p in nombre.split() if p]
    return "".join(p[0].upper() for p in partes[:2]) or "?"


def componer(persona: dict, plantilla: dict, cfg_fuentes: dict,
             carpeta_fotos: Path) -> Image.Image:
    fondo = Image.open(plantilla["fondo"]).convert("RGBA")

    # Foto
    box_foto = plantilla.get("foto")
    if box_foto:
        slug = nombre_archivo(persona["nombre"], "foto")
        ruta_foto = None
        for ext in (".jpg", ".jpeg", ".png", ".webp"):
            cand = carpeta_fotos / f"{slug}{ext}"
            if cand.exists():
                ruta_foto = cand
                break
        if ruta_foto:
            pegar_foto(fondo, Image.open(ruta_foto), box_foto)
        else:
            dibujar_placeholder_foto(fondo, box_foto, iniciales(persona["nombre"]))
            persona["_sin_foto"] = True

    # Textos
    valores = {
        "nombre": persona.get("nombre", ""),
        "cargo": persona.get("cargo", ""),
        "empresa": persona.get("empresa", ""),
        "telefono": normalizar_tel(persona.get("telefono", "")),
        "correo": persona.get("correo", ""),
        "web": persona.get("url", ""),
    }
    for campo, cfg in plantilla.get("textos", {}).items():
        dibujar_texto(fondo, valores.get(campo, ""), cfg, cfg_fuentes)

    # QR de contacto
    if plantilla.get("qr"):
        pegar_qr(fondo, crear_vcard(persona), plantilla["qr"])

    return fondo.convert("RGB")


# ---------------------------------------------------------------------------
# Programa principal
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(
        description="Genera credenciales superponiendo datos sobre tu plantilla.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("csv", help="CSV de respuestas del formulario.")
    ap.add_argument("-s", "--salida", default="credenciales", help="Carpeta de salida.")
    ap.add_argument("-e", "--empresas", default="empresas.json")
    ap.add_argument("-p", "--plantillas", default="plantillas.json")
    ap.add_argument("--fotos", default="fotos", help="Carpeta con las fotos editadas.")
    ap.add_argument("--pdf", action="store_true", help="Además, un PDF con todas.")
    args = ap.parse_args()

    ruta_csv = Path(args.csv)
    if not ruta_csv.exists():
        print(f"No se encontró el CSV: {ruta_csv}", file=sys.stderr)
        return 1

    with open(args.plantillas, encoding="utf-8") as f:
        plantillas_raw = json.load(f)
    cfg_fuentes = plantillas_raw.get("_fuentes", {})
    plantillas = {normalizar(k): v for k, v in plantillas_raw.items()
                  if not k.startswith("_") and isinstance(v, dict)}

    empresas = cargar_empresas(Path(args.empresas))
    carpeta_fotos = Path(args.fotos)
    salida = Path(args.salida)
    salida.mkdir(parents=True, exist_ok=True)

    with ruta_csv.open(newline="", encoding="utf-8-sig") as f:
        lector = csv.DictReader(f)
        if not lector.fieldnames:
            print("El CSV está vacío.", file=sys.stderr)
            return 1
        mapa = construir_mapa(lector.fieldnames)
        if "nombre" not in mapa:
            print(f"No encuentro la columna de nombre. Encabezados: {lector.fieldnames}",
                  file=sys.stderr)
            return 1

        hechas, faltan_foto, sin_plantilla = 0, [], set()
        imagenes, usados = [], set()

        for i, fila in enumerate(lector, start=1):
            persona = {c: (fila.get(h) or "").strip() for c, h in mapa.items()}
            if not persona.get("nombre"):
                continue

            clave_emp = normalizar(persona.get("empresa", ""))
            if clave_emp in empresas:
                cfg = empresas[clave_emp]
                persona["empresa"] = cfg["nombre"]
                if cfg["direccion"]:
                    persona["direccion"] = cfg["direccion"]
                if cfg["url"]:
                    persona["url"] = cfg["url"]

            plantilla = plantillas.get(clave_emp)
            if not plantilla:
                sin_plantilla.add(persona.get("empresa", "(vacía)"))
                continue
            if not Path(plantilla["fondo"]).exists():
                print(f"  ✗ Falta la plantilla de fondo: {plantilla['fondo']}",
                      file=sys.stderr)
                continue

            img = componer(persona, plantilla, cfg_fuentes, carpeta_fotos)

            base = nombre_archivo(persona["nombre"], f"credencial_{i}")
            if base in usados:
                base = f"{base}_{i}"
            usados.add(base)
            ruta = salida / f"{base}.png"
            img.save(ruta, dpi=(300, 300))
            if persona.get("_sin_foto"):
                faltan_foto.append(persona["nombre"])
            imagenes.append(img)
            print(f"  ✔ {persona['nombre']:<28s} [{persona.get('empresa','')}]"
                  f" -> {ruta.name}")
            hechas += 1

    if args.pdf and imagenes:
        pdf = salida / "credenciales.pdf"
        imagenes[0].save(pdf, save_all=True, append_images=imagenes[1:],
                         resolution=300.0)
        print(f"\nPDF: {pdf}")

    print(f"\nListo: {hechas} credencial(es) en '{salida}/'")
    if faltan_foto:
        print(f"⚠ Sin foto ({len(faltan_foto)}), quedaron con recuadro de iniciales: "
              + ", ".join(faltan_foto))
    if sin_plantilla:
        print("⚠ Sin plantilla en plantillas.json para: " + ", ".join(sin_plantilla))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
