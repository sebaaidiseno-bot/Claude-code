# Credenciales con QR de contacto (vCard)

Genera **credenciales listas para imprimir** para las personas de los talleres.
Cada credencial lleva la foto, los datos y un **QR de contacto (vCard)** que, al
escanearse, ofrece **"Agregar contacto"** con nombre, cargo, empresa, teléfono,
correo y web/Instagram.

Hay dos herramientas:

1. **`generar_qr.py`** — solo los códigos QR (PNG/SVG), por si quieres montarlos tú.
2. **`generar_credenciales.py`** — la credencial completa **superpuesta sobre tu
   plantilla** de Illustrator/Photoshop (foto + datos + QR).

---

## Flujo completo

```
Google Form  ->  Respuestas (Sheets)  ->  CSV
Fotos subidas en el Form  ->  las editas  ->  carpeta ./fotos
Tu plantilla (Illustrator/PS)  ->  exportas a PNG  ->  carpeta ./plantillas
                         |
                         v
             python generar_credenciales.py respuestas.csv
                         |
                         v
              ./credenciales  (un PNG por persona + PDF opcional)
```

---

## 1) Google Form

Un solo formulario. La persona llena sus datos, **elige su empresa** de una lista
y **sube su foto**. Usa exactamente estos títulos (no importan mayúsculas/acentos):

| Pregunta (título) | Tipo                          | Obligatoria |
|-------------------|-------------------------------|-------------|
| Nombre completo   | Respuesta corta               | Sí          |
| Cargo             | Respuesta corta               | Sí          |
| Teléfono          | Respuesta corta               | Sí          |
| Correo            | Respuesta corta               | Sí          |
| Empresa           | **Desplegable** (3 opciones)  | Sí          |
| Fotografía        | **Subir archivo** (1 imagen)  | Sí          |

Opciones de **Empresa** (escríbelas igual que en `empresas.json`):
`Taller Antumalal`, `Antumalal Autopartes`, `Presto Car Service`.

- **Subir archivo** obliga a la persona a iniciar sesión con cuenta Google; las
  fotos caen en una carpeta de tu Drive y en el CSV queda el **link** a cada una.
- La foto **no** va dentro del QR (lo haría ilegible): va en el diseño.
- Pide "foto de frente, fondo claro".

**CSV:** en Respuestas → ícono de Sheets → *Archivo → Descargar → CSV*.

## 2) Empresas (`empresas.json`)

Datos fijos por marca (la persona no los escribe). Cada marca lleva su web o
Instagram; la **dirección está vacía** — complétala con la dirección oficial
cuando la confirmes (si queda vacía, el QR no incluye dirección).

```json
{
  "Taller Antumalal":     { "direccion": "", "web": "agenda.grupoantumalal.cl" },
  "Antumalal Autopartes": { "direccion": "", "web": "antumalal.net" },
  "Presto Car Service":   { "direccion": "", "instagram": "@prestocarservice" }
}
```

## 3) Instalar (una vez)

```bash
pip install -r requirements.txt
```

## 4) Tu plantilla (`plantillas/`)

Exporta tu diseño **por marca** a PNG a tamaño final (ideal 10×15 cm a 300 DPI =
1181×1772 px), dejando el espacio vacío donde irán foto, textos y QR. Nómbralas:

```
plantillas/taller_antumalal.png
plantillas/antumalal_autopartes.png
plantillas/presto_car_service.png
```

¿Aún no tienes el diseño? Crea fondos de prueba para ver el layout:

```bash
python crear_plantilla_ejemplo.py
```

Las **posiciones** de foto, textos y QR se ajustan en `plantillas.json`. Las
coordenadas van en fracción de 0 a 1 (x,y = centro del elemento), así calzan con
cualquier resolución. Cambia los números hasta que encajen con tu arte.

## 5) Fotos (`fotos/`)

Guarda las fotos ya editadas nombradas por persona, en minúsculas y sin acentos:

```
Ana Pérez Soto  ->  fotos/ana_perez_soto.jpg
```

Si falta una foto, la credencial se genera igual con un recuadro de iniciales y
el script te avisa a quién le falta.

## 6) Generar

```bash
python generar_credenciales.py respuestas.csv            # PNG por persona
python generar_credenciales.py respuestas.csv --pdf      # + un PDF con todas
python generar_credenciales.py respuestas.csv -s salida_tallerA
```

Salen en `./credenciales`. El script muestra cada persona, avisa fotos faltantes
y empresas sin plantilla.

---

## Solo los QR (opcional)

Si prefieres montar las credenciales tú, genera únicamente los QR:

```bash
python generar_qr.py respuestas.csv --salida qr --svg
```

---

## Prueba rápida (sin datos reales)

```bash
python crear_plantilla_ejemplo.py                        # fondos de prueba
python generar_credenciales.py datos_ejemplo.csv --pdf   # 3 credenciales demo
```

## Notas

- **Teléfonos:** si vienen con 9 dígitos partiendo en 9 (celular chileno) se les
  agrega `+56`. Si traen `+`, se respeta.
- **Nombre en el archivo de foto:** se arma con minúsculas, sin acentos y guion
  bajo. Si el script no encuentra una foto, imprime el nombre exacto que espera.
- **Tamaño/print:** los PNG salen a 300 DPI; el PDF (`--pdf`) queda listo para
  imprenta.
