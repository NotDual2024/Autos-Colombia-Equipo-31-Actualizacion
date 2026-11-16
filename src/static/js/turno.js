/* Vigilante de sesión del operador (RN-35, Diseño iteración 2, sección 5).
 * - Al terminar la jornada sin un registro empezado: aviso y 5 minutos para cerrar sesión.
 * - Con un registro empezado: no se cierra mientras el operador escriba. Si pasan 5 minutos
 *   sin escribir, aparece el aviso y empieza otra cuenta de 5 minutos.
 * El servidor (ControlTurnoMiddleware) es la barrera definitiva aunque este script no corra.
 */
(function () {
  var cuerpo = document.body;
  var finTexto = cuerpo.getAttribute('data-fin-jornada');
  if (!finTexto) { return; }
  var fin = new Date(finTexto).getTime();
  var MINUTOS_5 = 5 * 60 * 1000;
  if (fin - Date.now() > 24 * 3600 * 1000) { return; } // jornada muy larga: no hace falta vigilar hoy

  var registroEmpezado = false;
  var ultimaEscritura = Date.now();
  var cierreProgramado = null;

  document.querySelectorAll('form.formulario-registro, form[method="post"]').forEach(function (form) {
    form.addEventListener('input', function () {
      registroEmpezado = true;
      ultimaEscritura = Date.now();
      ocultarAviso();
    });
  });
  document.querySelectorAll('[data-cancelar]').forEach(function (enlace) {
    enlace.addEventListener('click', function () { registroEmpezado = false; });
  });

  var aviso = document.getElementById('aviso-turno');
  var texto = document.getElementById('aviso-turno-texto');

  function mostrarAviso(hasta) {
    cierreProgramado = hasta;
    if (aviso) { aviso.hidden = false; }
  }
  function ocultarAviso() {
    cierreProgramado = null;
    if (aviso) { aviso.hidden = true; }
  }
  function cerrarSesion() {
    var form = document.getElementById('form-cerrar-sesion');
    if (form) {
      var motivo = document.createElement('input');
      motivo.type = 'hidden'; motivo.name = 'next'; motivo.value = form.getAttribute('data-login') + '?motivo=inactividad';
      form.appendChild(motivo);
      form.submit();
    }
  }
  function formato(ms) {
    var s = Math.max(0, Math.round(ms / 1000));
    return Math.floor(s / 60) + ':' + ('0' + (s % 60)).slice(-2);
  }

  setInterval(function () {
    var ahora = Date.now();
    if (ahora < fin) { return; }
    if (cierreProgramado === null) {
      if (!registroEmpezado) {
        mostrarAviso(Math.max(fin + MINUTOS_5, ahora));
      } else if (ahora - ultimaEscritura >= MINUTOS_5) {
        mostrarAviso(ahora + MINUTOS_5);
      }
    }
    if (cierreProgramado !== null) {
      var restante = cierreProgramado - ahora;
      if (texto) {
        texto.textContent = registroEmpezado
          ? 'No has escrito nada en 5 minutos. La sesión se cerrará en ' + formato(restante) + '.'
          : 'Tu turno terminó. La sesión se cerrará en ' + formato(restante) + '.';
      }
      if (restante <= 0) { cerrarSesion(); }
    }
  }, 1000);
})();
