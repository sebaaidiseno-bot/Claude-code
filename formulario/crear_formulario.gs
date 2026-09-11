/**
 * Crea el Google Form para capturar los datos de las credenciales, con el
 * desplegable de empresa ya cargado y una planilla de respuestas enlazada.
 *
 * CÓMO USARLO (una sola vez):
 *   1. Entra a https://script.google.com  ->  Proyecto nuevo.
 *   2. Borra el contenido y pega TODO este archivo.
 *   3. Arriba, elige la función  crearFormulario  y presiona  Ejecutar.
 *   4. La primera vez te pedirá autorizar permisos (es tu propia cuenta).
 *   5. Al terminar, mira el menú  Ver > Registro (o "Ejecuciones"): ahí quedan
 *      el LINK PARA EDITAR el formulario, el LINK PARA COMPARTIR y el de la
 *      planilla de respuestas.
 *
 * OJO: la pregunta de "Fotografía" (subir archivo) NO se puede crear por código
 * (limitación de Google). El script te deja todo lo demás y al final te recuerda
 * agregarla a mano (son 3 clics; instrucciones abajo en agregarFotoManual()).
 */

// Opciones del desplegable de empresa. Deben coincidir EXACTO con empresas.json
// del proyecto de credenciales.
var EMPRESAS = [
  'Taller Antumalal',
  'Antumalal Autopartes',
  'Presto Car Service'
];

function crearFormulario() {
  var form = FormApp.create('Datos para credencial - Grupo Antumalal')
    .setDescription(
      'Completa tus datos para generar tu credencial con código QR de contacto. ' +
      'Los campos marcados son obligatorios.')
    .setCollectEmail(false)          // no pedimos el correo de la cuenta Google
    .setAllowResponseEdits(true)     // pueden corregir su respuesta
    .setProgressBar(false);

  // Nombre completo
  form.addTextItem()
    .setTitle('Nombre completo')
    .setHelpText('Tal como quieres que aparezca en la credencial. Ej: Ana Pérez Soto')
    .setRequired(true);

  // Cargo
  form.addTextItem()
    .setTitle('Cargo')
    .setHelpText('Ej: Gerenta Comercial, Jefe de Repuestos, Asesor de Servicio')
    .setRequired(true);

  // Teléfono
  form.addTextItem()
    .setTitle('Teléfono')
    .setHelpText('De preferencia con formato +56 9 1234 5678')
    .setRequired(true);

  // Correo (con validación de formato de email)
  var correo = form.addTextItem()
    .setTitle('Correo')
    .setHelpText('Correo de trabajo')
    .setRequired(true);
  correo.setValidation(
    FormApp.createTextValidation()
      .setHelpText('Ingresa un correo válido.')
      .requireTextIsEmail()
      .build());

  // Empresa (desplegable)
  form.addListItem()
    .setTitle('Empresa')
    .setHelpText('Selecciona la marca/sucursal a la que perteneces.')
    .setChoiceValues(EMPRESAS)
    .setRequired(true);

  // Enlazar una planilla de respuestas nueva
  var ss = SpreadsheetApp.create('Respuestas - Credenciales Grupo Antumalal');
  form.setDestination(FormApp.DestinationType.SPREADSHEET, ss.getId());

  Logger.log('==============================================');
  Logger.log('FORMULARIO CREADO');
  Logger.log('Editar formulario:  ' + form.getEditUrl());
  Logger.log('Compartir (llenar): ' + form.getPublishedUrl());
  Logger.log('Planilla respuestas: ' + ss.getUrl());
  Logger.log('==============================================');
  Logger.log('FALTA 1 PASO MANUAL: agrega la pregunta "Fotografía" (subir');
  Logger.log('archivo). Abre el formulario con el link de editar y sigue las');
  Logger.log('instrucciones de la función agregarFotoManual() de este script.');
}

/**
 * La pregunta de subir archivo NO se puede crear por código. Hazlo a mano:
 *
 *   1. Abre el formulario (link "Editar formulario" del registro).
 *   2. Botón (+) para agregar pregunta.
 *   3. Título: Fotografía
 *   4. Tipo de pregunta: "Subir archivo".
 *   5. Acepta el aviso (el que responde deberá iniciar sesión con Google).
 *   6. Número máximo de archivos: 1.  Tipos: solo imágenes (opcional).
 *   7. Marca la pregunta como obligatoria.
 *   8. Ayuda sugerida: "Foto de frente, fondo claro, buena luz."
 *
 * Si tu cuenta es de Workspace (grupoantumalal.cl) y quieres que respondan
 * personas fuera del dominio: Configuración (engranaje) > Respuestas >
 * desmarca "Restringir a usuarios de Grupo Antumalal".
 */
function agregarFotoManual() {
  // Función solo informativa (ver comentario de arriba).
}
