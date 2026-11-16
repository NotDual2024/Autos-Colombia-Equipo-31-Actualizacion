# Informe de implementación — Iteración 2

**Autor:** Software Engineer · **Fecha:** 2026-11-15

**Funcionalidad:** Gestión de usuarios y celdas: propietarios, vehículos, cambio de propietario con solicitud e historial, mapa de celdas, gestión completa de operadores, horarios por franjas, autorizaciones fuera de turno, control de turno y bitácora de operaciones.

**Requerimientos relacionados:** RF-101, RF-102, RF-104 a RF-111 (RF-103 fuera de alcance) · HU-012 a HU-023 · RN-25 a RN-37 · DEC-013, DEC-014, DEC-015 · Modelo de datos v1.3 (DM-08 a DM-11) · Diseño iteración 2 (UC-16 a UC-29, M-13 a M-25).

## Archivos creados

- `src/apps/bitacora/` (módulo nuevo): modelo `RegistroOperacion`, servicios (`registrar`, `buscar`, `instantanea`, `diferencias`), vista con filtros, plantillas y migración `0001`.
- `src/apps/cuentas/turnos.py` (franjas, autorizaciones, fin de jornada) y `src/apps/cuentas/control_turno.py` (`BackendTurno`, `ControlTurnoMiddleware`, duración de la sesión).
- `src/apps/cuentas/context_processors.py`, `src/apps/usuarios_celdas/context_processors.py` (turno en el encabezado y contador de solicitudes).
- Vistas, formularios, URL y plantillas de `usuarios_celdas` (`/clientes/`): propietarios, vehículos, fichas, solicitudes y mapa de celdas.
- Plantillas de `cuentas`: editar operador, horario, autorizaciones.
- `src/static/js/turno.js` (aviso de fin de turno e inactividad en el navegador).
- Migraciones `cuentas 0002` y `usuarios_celdas 0002`.
- Pruebas: `usuarios_celdas/tests/test_hu012_018.py`, `cuentas/tests/test_hu019_022.py`, `demo/tests/test_modelo_datos_v13.py`.

## Archivos modificados

- `config/settings.py` y `config/urls.py`: módulo `bitacora`, backend de autenticación, middleware, procesadores de contexto, rutas `/clientes/` y `/bitacora/`, `handler403`.
- `templates/base.html`: menú por secciones (Operación, Clientes, Administración), turno en el encabezado y aviso de fin de turno.
- `static/css/estilos.css`: estilos de las nuevas pantallas y la regla `[hidden]` (ver problemas resueltos).
- `apps/demo`: horarios de los usuarios de demostración, historial de propiedad, solicitud pendiente y operaciones en la bitácora.
- Pruebas de la iteración 1 adaptadas: los operadores de prueba tienen horario de 24 horas y los teléfonos son celulares válidos (RN-30).

## Implementación realizada

| Paso | Resultado |
|---|---|
| 1. Modelo v1.3 | `HorarioOperador` definitivo, `AutorizacionFueraTurno`, `SolicitudCambioPropietario`, `HistorialPropiedad`, `RegistroOperacion`, celular con `CHECK GLOB`. Las restricciones coinciden con el DDL v1.3 aprobado. |
| 2. Bitácora | Cada operación de alta, modificación, cambio de estado, solicitud, aprobación, rechazo, horario y autorización deja un registro con usuario, fecha y diferencias. No se puede modificar desde la interfaz. |
| 3. Propietarios y vehículos | Registrar, modificar, activar e inactivar (sin borrado); búsqueda; fichas con vehículos, historial de propietarios y bitácora. Placa validada según el tipo. |
| 4. Cambio de propietario | Solicitud del operador → aprobación o rechazo del administrador (con observación obligatoria al rechazar). Al aprobar, el propietario anterior pasa al historial. Solo una solicitud pendiente por vehículo. |
| 5. Celdas | Mapa por zona, con ocupación y la placa de cada celda ocupada. Las celdas son fijas (RN-27). |
| 6. Operadores y horarios | Editar nombre, restablecer contraseña, activar y desactivar. Franjas por día, incluidas las nocturnas, sin cruces (RN-37). |
| 7. Control de turno | No se inicia sesión fuera del turno ni sin horario. Al terminar el turno se completa el registro en curso y luego se cierra la sesión, con 5 minutos de gracia (RN-35). El administrador puede autorizar el ingreso fuera de turno. |
| 8. Datos de demostración | `operador` con horario de 24 horas, `operador2` de lunes a viernes de 06:00 a 07:00, historial de BGT219, solicitud pendiente de JTR625 y operaciones en la bitácora. |

## Pruebas ejecutadas (resultados reales)

`python manage.py test apps` → **Ran 154 tests … OK** · `makemigrations --check` → sin cambios pendientes.

| Prueba | Resultado |
|---|---|
| Unitarias (franjas que cruzan la medianoche, cruces en la semana circular, fin de jornada encadenado, diferencias de la bitácora) | Aprobadas |
| Integración (servicios + base de datos; restricciones del DDL v1.3 a través del ORM) | Aprobadas |
| Funcionales (escenarios Dado/Cuando/Entonces de HU-012 a HU-023 y permisos por rol, con el cliente de pruebas) | Aprobadas |
| Regresión (las 100 pruebas de la iteración 1 siguen pasando) | Aprobadas: 154/154 en total |
| Verificación manual en el navegador | Ver la tabla siguiente |

Verificación manual (servidor local, 15/11/2026, domingo 22:15):

| Caso | Resultado |
|---|---|
| `operador2` intenta ingresar fuera de su turno | Mensaje "Estás fuera de tu turno. Solicita autorización al administrador." |
| `operador` (24 h) | Ingresa; el encabezado muestra el turno; propietarios, vehículos y la ficha de JTR625 con su solicitud pendiente y la bitácora |
| Mapa de celdas | 8 celdas de carro/camioneta y 3 de moto ocupadas, coherentes con los vehículos dentro |
| Administrador: solicitud de JTR625 | Aprobada; la ficha muestra a Andrés Gómez como propietario y a Laura Méndez en el historial; el contador de solicitudes desaparece |
| Bitácora | Muestra la aprobación, la solicitud y la modificación del teléfono, con usuario y diferencias |
| Operadores y autorizaciones | Lista con horarios; se autorizó a `operador2` hasta las 23:45 y pudo ingresar ("Autorizado hasta 23:45") |

Después de la verificación se recargaron los datos de demostración (`cargar_datos_demo --reiniciar`), así que la base vuelve a su estado inicial.

## Problemas encontrados y resueltos

- **Dependencia circular bitacora ↔ cuentas:** se corrigió en el diseño (DM-08, aprobado). La bitácora solo depende de `core` y usa `settings.AUTH_USER_MODEL`.
- **Cierre de sesión en cada petición:** la primera versión del control de turno usaba `user_can_authenticate`, que Django también consulta en cada petición. Esto habría cerrado la sesión sin respetar RN-35. Ahora el backend solo actúa en `authenticate`.
- **Mapa con todas las celdas ocupadas:** el filtro por la relación inversa también tomaba celdas sin estadías. Se añadió `estadias__isnull=False`.
- **Pruebas de la iteración 1 sin horario:** con RN-36, los operadores de prueba ya no podían ingresar. Se les asigna un horario de 24 horas en la base de pruebas.
- **Aviso de fin de turno visible siempre:** la clase `.alerta` (`display:flex`) anulaba el atributo `hidden`. Se añadió la regla `[hidden]{display:none !important}`.

## Limitaciones conocidas

- **`turno.js`** (aviso en el navegador y cierre por inactividad de 5 minutos) se probó solo de forma manual. No hay pruebas automatizadas de JavaScript. La barrera definitiva es el middleware del servidor, que sí tiene pruebas.
- **RNF-006** (menos de 2 s): no se midió formalmente.
- **P-33** (motivo de inactivación y reactivación automática al registrar el pago) queda para la iteración 3, como acordó el equipo.
- El cierre de sesión se aplica en la siguiente petición del operador. Si el navegador está cerrado, la sesión vence por su duración máxima (12 horas).

## Estado final

**Completado y verificado**, salvo las limitaciones anteriores. Falta el commit de la iteración 2.
