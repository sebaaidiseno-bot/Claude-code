# Generador de QR de contacto (vCard) para credenciales

Genera un código QR por persona que, al escanearse, ofrece **"Agregar contacto"**
con nombre, cargo, empresa, teléfono, correo, dirección y página web. Sirve para
armar credenciales de los dos talleres.

El tipo de QR que buscas se llama **vCard** (a veces "QR de contacto" o "MECARD").
Este proyecto usa vCard 3.0, que es el más compatible con iPhone y Android.

---

## Flujo completo

```
Google Form  ->  Respuestas (Google Sheets)  ->  CSV  ->  generar_qr.py  ->  1 PNG por persona
```

1. Cada persona llena un **Google Form** (uno por taller).
2. Las respuestas caen solas en una **Google Sheet**.
3. Descargas la hoja como **CSV**.
4. Corres el script y obtienes un **PNG** (y opcional SVG) por persona.
5. Pegas cada QR en su credencial (Canva, Illustrator, Word, lo que uses).

> No necesitas Cloud Functions ni automatización compleja: un CSV + este script
> resuelve todo en segundos y lo puedes repetir cada vez que lleguen respuestas.

---

## 1) Cómo armar el Google Form

Un **solo formulario** basta. La persona solo llena sus datos y **elige su
empresa** de una lista; la dirección y la web/Instagram NO se preguntan: se
completan solas al generar el QR, según la empresa (ver paso 2).

Usa exactamente estos títulos de pregunta — el script los reconoce
automáticamente (no importan mayúsculas ni acentos):

| Pregunta (título)   | Tipo                        | Obligatoria |
|---------------------|-----------------------------|-------------|
| Nombre completo     | Respuesta corta             | Sí          |
| Cargo               | Respuesta corta             | Sí          |
| Teléfono            | Respuesta corta             | Sí          |
| Correo              | Respuesta corta             | Sí          |
| Empresa             | **Desplegable** (2 opciones)| Sí          |

En **Empresa**, agrega como opciones los nombres de las dos empresas. Deben
escribirse **igual** que las claves del archivo `empresas.json` (paso 2).

> Si prefieres, puedes hacer un formulario por taller; da lo mismo, porque la
> empresa igual se selecciona/identifica y el resto es automático.

### Obtener el CSV
En el formulario: pestaña **Respuestas** → ícono verde de Sheets → en la hoja,
**Archivo → Descargar → Valores separados por comas (.csv)**.

---

## 2) Configurar las empresas (una sola vez)

Edita **`empresas.json`** con los datos reales de cada empresa. La clave debe
coincidir **exactamente** con la opción de la lista "Empresa" del formulario.
Cada empresa lleva `direccion` y **una** de estas: `web` **o** `instagram`.

```json
{
  "Empresa A": {
    "direccion": "Av. Real 1234, Of. 56, Santiago",
    "web": "www.empresa-a.cl"
  },
  "Empresa B": {
    "direccion": "Calle Real 4321, Local 7, Santiago",
    "instagram": "@empresa_b"
  }
}
```

Así, la dirección y la web/Instagram quedan fijas por empresa: la persona nunca
las escribe y no hay errores de tipeo. Instagram acepta `@usuario`, `usuario` o
el link completo.

## 3) Instalar (una sola vez)

```bash
pip install -r requirements.txt
```

## 4) Generar los QR

```bash
# Básico: lee el CSV y crea un PNG por persona en ./qr_salida
python generar_qr.py respuestas.csv

# Elegir carpeta de salida (útil para separar los dos talleres)
python generar_qr.py respuestas_tallerA.csv --salida qr_taller_A
python generar_qr.py respuestas_tallerB.csv --salida qr_taller_B

# Usar otro archivo de empresas (por defecto usa empresas.json)
python generar_qr.py respuestas.csv --empresas empresas.json

# Generar también SVG vectorial (ideal para imprimir a cualquier tamaño)
python generar_qr.py respuestas.csv --svg

# Guardar además el .vcf de cada uno (para revisar el contenido)
python generar_qr.py respuestas.csv --guardar-vcf
```

El script muestra qué empresa detectó por cada persona. Si alguien seleccionó
una empresa que **no** está en `empresas.json`, lo avisa con `⚠` y usa lo que
venga en el CSV (o lo deja en blanco).

Cada archivo se nombra con el nombre de la persona, p. ej. `ana_perez_soto.png`.

---

## Prueba rápida

Ya viene un `datos_ejemplo.csv`. Para verlo funcionando:

```bash
python generar_qr.py datos_ejemplo.csv --salida qr_ejemplo --svg
```

Escanea el PNG resultante con la cámara del teléfono: debe ofrecer agregar el
contacto con todos los datos.

---

## Notas

- **Teléfonos:** si escriben 9 dígitos partiendo en 9 (celular chileno), el
  script agrega `+56` solo. Si ya viene con `+`, lo respeta. Recomienda a la
  gente escribir el número con `+56 9 ...` para máxima compatibilidad.
- **Nombre y apellido:** el QR muestra el nombre completo tal cual. Para el
  ordenamiento interno separa nombre/apellidos con una heurística simple; si
  necesitas control exacto, puedes agregar una columna `Apellidos` al formulario.
- **PNG vs SVG:** para imprimir credenciales, el SVG escala sin perder nitidez;
  el PNG sirve para pegar rápido en cualquier editor.
- **Corrección de errores:** los QR usan nivel M (tolera algo de suciedad o un
  logo pequeño al centro sin dejar de leerse).
