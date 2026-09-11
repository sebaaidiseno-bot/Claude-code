# Formulario para capturar los datos

Objetivo: cada persona llena un formulario con su **nombre, cargo, teléfono,
correo**, **elige su empresa** de una lista y **sube su foto**. Las respuestas
caen en una planilla; de ahí sale el CSV que alimenta el generador de credenciales.

Tienes dos caminos. Elige uno.

---

## Opción A (recomendada): crearlo automático con el script

Te deja el formulario armado en 1 minuto, con el desplegable de empresa ya cargado.

1. Entra a **https://script.google.com** → **Proyecto nuevo**.
2. Borra lo que haya y pega el contenido de **`crear_formulario.gs`**.
3. Arriba selecciona la función **`crearFormulario`** y presiona **Ejecutar**.
4. Autoriza los permisos la primera vez (es tu propia cuenta de Google).
5. Abre **Registro de ejecución** (o menú *Ver → Registros*). Ahí quedan:
   - link para **editar** el formulario,
   - link para **compartir** (el que envías a la gente),
   - link de la **planilla de respuestas**.
6. **Paso manual (obligatorio):** agrega la pregunta **Fotografía** de tipo
   **"Subir archivo"** (el código no puede crearla). Pasos exactos en el
   comentario de la función `agregarFotoManual()` dentro del `.gs`.

## Opción B: crearlo a mano

1. En **https://forms.google.com** crea un formulario en blanco.
2. Título: *Datos para credencial - Grupo Antumalal*.
3. Agrega estas preguntas (los títulos deben ser EXACTOS, el generador los usa):

   | Pregunta        | Tipo                          | Obligatoria |
   |-----------------|-------------------------------|-------------|
   | Nombre completo | Respuesta corta               | Sí          |
   | Cargo           | Respuesta corta               | Sí          |
   | Teléfono        | Respuesta corta               | Sí          |
   | Correo          | Respuesta corta (validar email)| Sí         |
   | Empresa         | **Desplegable**               | Sí          |
   | Fotografía      | **Subir archivo** (1 imagen)  | Sí          |

4. En **Empresa**, agrega EXACTAMENTE estas 3 opciones:
   - `Taller Antumalal`
   - `Antumalal Autopartes`
   - `Presto Car Service`
5. En **Respuestas** (pestaña arriba) → ícono verde de **Sheets** para crear la
   planilla enlazada.

---

## Notas importantes

- **La foto (subir archivo)** obliga a que la persona inicie sesión con una
  cuenta Google. Las fotos se guardan solas en una carpeta de tu Drive y en la
  planilla aparece el **link** a cada foto.
- Si tu cuenta es **Workspace (grupoantumalal.cl)** y necesitas que respondan
  personas de fuera del dominio: engranaje de **Configuración → Respuestas →**
  desmarca *"Restringir a usuarios de Grupo Antumalal"*.
- **Las opciones de Empresa deben coincidir** con `empresas.json` del proyecto,
  porque así el generador sabe qué web/Instagram y (a futuro) qué plantilla usar.

## Obtener el CSV para generar

En la planilla de respuestas: **Archivo → Descargar → Valores separados por
comas (.csv)**. Ese archivo es el que se le pasa a `generar_qr.py` o
`generar_credenciales.py`.

## ¿Y la dirección / web / Instagram?

No se preguntan en el formulario: son fijas por marca y ya están en
`empresas.json` (web/Instagram cargadas; la dirección la completas tú cuando la
confirmes). Eso evita errores de tipeo y acorta el formulario.
