#!/usr/bin/env python3
"""
Generador de códigos QR de contacto (vCard) a partir de una planilla CSV.

Flujo pensado:
  1. Cada persona llena un Google Form.
  2. Descargas las respuestas como CSV (Sheets -> Archivo -> Descargar -> CSV).
  3. Ejecutas este script apuntando al CSV.
  4. Obtienes un PNG (y opcionalmente SVG) por persona en la carpeta de salida.
     Cada QR, al escanearse, ofrece "Agregar contacto" con todos los datos.

Uso:
  python generar_qr.py respuestas.csv
  python generar_qr.py respuestas.csv --salida qr_taller_A --svg
  python generar_qr.py --help

El script detecta las columnas por el NOMBRE de la pregunta del formulario,
sin importar mayúsculas, acentos ni el orden. Sirve para los dos talleres:
uno con "Página web" y otro con "Página de lista"; ambas caen en el campo URL.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import unicodedata
from pathlib import Path

try:
    import qrcode
    from qrcode.image.svg import SvgImage
except ImportError:
    sys.exit(
        "Falta la librería 'qrcode'. Instálala con:\n"
        "    pip install -r requirements.txt\n"
        "  (o)  pip install 'qrcode[pil]'"
    )


# ---------------------------------------------------------------------------
# Detección flexible de columnas
# ---------------------------------------------------------------------------

def normalizar(texto: str) -> str:
    """minúsculas, sin acentos, sin signos, espacios colapsados."""
    if texto is None:
        return ""
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = texto.lower()
    texto = re.sub(r"[^a-z0-9]+", " ", texto)
    return texto.strip()


# Para cada campo lógico, lista de posibles nombres de columna (normalizados).
ALIAS = {
    "nombre":    ["nombre completo", "nombre y apellido", "nombre", "nombres"],
    "cargo":     ["cargo", "puesto", "titulo", "profesion", "rol"],
    "telefono":  ["telefono", "celular", "fono", "numero", "numero de telefono",
                  "telefono celular", "telefono de contacto", "movil"],
    "telefono2": ["telefono 2", "telefono fijo", "segundo telefono", "otro telefono",
                  "anexo", "fijo"],
    "correo":    ["correo", "email", "correo electronico", "e mail", "mail"],
    "direccion": ["direccion", "domicilio", "ubicacion", "direccion oficina"],
    "empresa":   ["empresa", "nombre de la empresa", "compania", "organizacion",
                  "razon social"],
    "url":       ["pagina web", "sitio web", "web", "url", "pagina de lista",
                  "pagina", "sitio", "lista", "link", "enlace"],
}


def construir_mapa(headers: list[str]) -> dict[str, str]:
    """Devuelve {campo_logico: header_real} según ALIAS."""
    norm_headers = {normalizar(h): h for h in headers}
    mapa: dict[str, str] = {}
    for campo, alias in ALIAS.items():
        for a in alias:
            if a in norm_headers:
                mapa[campo] = norm_headers[a]
                break
        else:
            # coincidencia parcial (por si el título trae texto extra)
            for nh, original in norm_headers.items():
                if any(a in nh for a in alias):
                    mapa[campo] = original
                    break
    return mapa


# ---------------------------------------------------------------------------
# Configuración de empresas (dirección + web/Instagram fijos por empresa)
# ---------------------------------------------------------------------------

def cargar_empresas(ruta: Path | None) -> dict[str, dict]:
    """Devuelve {nombre_normalizado: {nombre, direccion, url}}."""
    if ruta is None or not ruta.exists():
        return {}
    with ruta.open(encoding="utf-8") as f:
        crudo = json.load(f)

    empresas: dict[str, dict] = {}
    for clave, datos in crudo.items():
        if clave.startswith("_") or not isinstance(datos, dict):
            continue  # entradas de ayuda / comentarios
        url = ""
        if datos.get("web"):
            url = normalizar_url(datos["web"])
        elif datos.get("instagram"):
            url = instagram_a_url(datos["instagram"])
        empresas[normalizar(clave)] = {
            "nombre": (datos.get("empresa") or clave).strip(),
            "direccion": (datos.get("direccion") or "").strip(),
            "url": url,
        }
    return empresas


# ---------------------------------------------------------------------------
# Construcción de la vCard
# ---------------------------------------------------------------------------

def separar_nombre(nombre_completo: str) -> tuple[str, str]:
    """('Nombre(s)', 'Apellido(s)') de forma simple."""
    partes = nombre_completo.split()
    if len(partes) <= 1:
        return nombre_completo.strip(), ""
    # Heurística Chile: primer token = nombre, resto = apellidos.
    if len(partes) == 2:
        return partes[0], partes[1]
    return " ".join(partes[:2]), " ".join(partes[2:])


def escapar(valor: str) -> str:
    """Escapa caracteres especiales de vCard 3.0."""
    return (
        valor.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\n", "\\n")
    )


def normalizar_url(url: str) -> str:
    url = url.strip()
    if url and not re.match(r"^https?://", url, re.I):
        url = "https://" + url
    return url


def instagram_a_url(valor: str) -> str:
    """'@handle' o 'handle' o un link -> https://www.instagram.com/handle"""
    valor = valor.strip()
    if not valor:
        return ""
    if "instagram.com" in valor.lower():
        return normalizar_url(valor)
    handle = valor.lstrip("@").strip("/")
    return f"https://www.instagram.com/{handle}"


def normalizar_tel(tel: str) -> str:
    """Limpia el teléfono y le pone +56 si parece chileno sin prefijo."""
    tel = tel.strip()
    if not tel:
        return ""
    # deja solo dígitos y un + inicial
    signo = "+" if tel.lstrip().startswith("+") else ""
    digitos = re.sub(r"\D", "", tel)
    if signo:
        return "+" + digitos
    # 9 dígitos (celular chileno) -> +56
    if len(digitos) == 9 and digitos.startswith("9"):
        return "+56" + digitos
    return digitos


def crear_vcard(datos: dict[str, str]) -> str:
    nombre = datos.get("nombre", "").strip()
    nombres, apellidos = separar_nombre(nombre)

    lineas = ["BEGIN:VCARD", "VERSION:3.0"]
    lineas.append(f"N:{escapar(apellidos)};{escapar(nombres)};;;")
    lineas.append(f"FN:{escapar(nombre)}")

    if datos.get("empresa"):
        lineas.append(f"ORG:{escapar(datos['empresa'].strip())}")
    if datos.get("cargo"):
        lineas.append(f"TITLE:{escapar(datos['cargo'].strip())}")

    tel = normalizar_tel(datos.get("telefono", ""))
    if tel:
        lineas.append(f"TEL;TYPE=CELL,VOICE:{tel}")
    tel2 = normalizar_tel(datos.get("telefono2", ""))
    if tel2:
        lineas.append(f"TEL;TYPE=WORK,VOICE:{tel2}")

    if datos.get("correo"):
        lineas.append(f"EMAIL;TYPE=INTERNET,WORK:{datos['correo'].strip()}")

    if datos.get("direccion"):
        # calle va en el 3er componente de ADR
        lineas.append(f"ADR;TYPE=WORK:;;{escapar(datos['direccion'].strip())};;;;")

    if datos.get("url"):
        lineas.append(f"URL:{escapar(normalizar_url(datos['url']))}")

    lineas.append("END:VCARD")
    return "\r\n".join(lineas)


# ---------------------------------------------------------------------------
# Nombre de archivo seguro
# ---------------------------------------------------------------------------

def nombre_archivo(texto: str, respaldo: str) -> str:
    base = normalizar(texto).replace(" ", "_")
    base = re.sub(r"[^a-z0-9_]", "", base)
    return base or respaldo


# ---------------------------------------------------------------------------
# Generación de QR
# ---------------------------------------------------------------------------

def qr_pil(contenido: str, box_size: int = 10, border: int = 4):
    """Devuelve el QR como imagen PIL (para guardar o componer en credenciales)."""
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=box_size,
        border=border,
    )
    qr.add_data(contenido)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    # qrcode devuelve un envoltorio; get_image() entrega el PIL.Image real.
    return img.get_image() if hasattr(img, "get_image") else img


def generar_qr_png(contenido: str, ruta: Path) -> None:
    qr_pil(contenido).save(ruta)


def generar_qr_svg(contenido: str, ruta: Path) -> None:
    img = qrcode.make(contenido, image_factory=SvgImage, border=4)
    img.save(ruta)


# ---------------------------------------------------------------------------
# Programa principal
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Genera un QR de contacto (vCard) por cada fila del CSV.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("csv", help="Ruta al CSV de respuestas del formulario.")
    parser.add_argument(
        "-s", "--salida", default="qr_salida",
        help="Carpeta donde guardar los QR (por defecto: qr_salida).",
    )
    parser.add_argument(
        "-e", "--empresas", default="empresas.json",
        help="JSON con dirección y web/Instagram por empresa (por defecto: empresas.json).",
    )
    parser.add_argument(
        "--svg", action="store_true",
        help="Generar también un SVG vectorial (además del PNG).",
    )
    parser.add_argument(
        "--guardar-vcf", action="store_true",
        help="Guardar también el archivo .vcf de cada persona (para revisar).",
    )
    args = parser.parse_args()

    ruta_csv = Path(args.csv)
    if not ruta_csv.exists():
        print(f"No se encontró el archivo: {ruta_csv}", file=sys.stderr)
        return 1

    salida = Path(args.salida)
    salida.mkdir(parents=True, exist_ok=True)

    empresas = cargar_empresas(Path(args.empresas))
    if empresas:
        print("Empresas configuradas:", ", ".join(e["nombre"] for e in empresas.values()))
        print()

    with ruta_csv.open(newline="", encoding="utf-8-sig") as f:
        lector = csv.DictReader(f)
        if not lector.fieldnames:
            print("El CSV está vacío o no tiene encabezados.", file=sys.stderr)
            return 1

        mapa = construir_mapa(lector.fieldnames)
        if "nombre" not in mapa:
            print(
                "No pude identificar la columna del NOMBRE.\n"
                f"Encabezados detectados: {lector.fieldnames}\n"
                "Asegúrate de que la pregunta se llame algo como 'Nombre completo'.",
                file=sys.stderr,
            )
            return 1

        print("Columnas detectadas:")
        for campo, header in mapa.items():
            print(f"  {campo:10s} <- {header!r}")
        print()

        generados = 0
        usados: set[str] = set()
        for i, fila in enumerate(lector, start=1):
            datos = {campo: (fila.get(header) or "").strip()
                     for campo, header in mapa.items()}
            if not datos.get("nombre"):
                print(f"  (fila {i}: sin nombre, se omite)")
                continue

            # Completar dirección y web/Instagram desde la config de la empresa.
            nota = ""
            clave_emp = normalizar(datos.get("empresa", ""))
            if clave_emp and clave_emp in empresas:
                cfg = empresas[clave_emp]
                datos["empresa"] = cfg["nombre"]  # nombre "oficial" y consistente
                if cfg["direccion"]:
                    datos["direccion"] = cfg["direccion"]
                if cfg["url"]:
                    datos["url"] = cfg["url"]
            elif clave_emp and empresas:
                nota = "  ⚠ empresa no está en empresas.json (uso los datos del CSV si hay)"

            vcard = crear_vcard(datos)

            base = nombre_archivo(datos["nombre"], f"contacto_{i}")
            if base in usados:
                base = f"{base}_{i}"
            usados.add(base)

            png = salida / f"{base}.png"
            generar_qr_png(vcard, png)
            extra = ""

            if args.svg:
                generar_qr_svg(vcard, salida / f"{base}.svg")
                extra += " +svg"
            if args.guardar_vcf:
                (salida / f"{base}.vcf").write_text(vcard, encoding="utf-8")
                extra += " +vcf"

            print(f"  ✔ {datos['nombre']:<30s} -> {png.name}{extra}{nota}")
            generados += 1

    print(f"\nListo: {generados} código(s) QR en '{salida}/'")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
