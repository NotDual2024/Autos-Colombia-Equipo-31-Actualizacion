# Requerimientos — Iteración 2: Gestión de usuarios y gestión de celdas

**Proyecto:** Parqueadero "Autos Colombia"
**Versión:** 1.5
**Fecha:** 2026-11-15
**Base:** Anexo A de `Requerimientos_v2.md` (v2.11), modelo de datos v1.2 y RN-01 a RN-24 aprobadas.
**Estado:** **Aprobado** por el equipo del proyecto el 2026-11-15. Versión 1.5 por la solicitud de cambio CHG-003, aprobada el 2026-11-22.

| Versión | Cambios |
|---|---|
| 1 | Borrador inicial con las preguntas P-26 a P-32. |
| 1.1 | Incorpora las respuestas del equipo a P-26 a P-32. RF-103 queda fuera (las celdas son fijas). Se agregan RF-109 (cambio de propietario por solicitud), RF-110 (autorización fuera de turno) y RF-111 (bitácora de operaciones). Se proponen DEC-013 a DEC-015. Nuevas preguntas: P-33 a P-36. |
| 1.2 | Respuestas a P-33 a P-36: P-33 pasa a la iteración 3; se agregan RN-35 (cierre de sesión al terminar el turno) y RN-36 (sin horario no hay ingreso); se confirman los turnos nocturnos; el operador ve la bitácora solo en las fichas. Nuevas preguntas: P-37 y P-38. |
| 1.3 | P-37 y P-38 resueltas; DEC-013, DEC-014 y DEC-015 aprobadas. Sin preguntas abiertas. |
| 1.3 | **Aprobada** por el equipo el 2026-11-15. |
| 1.4 | Aclaraciones del equipo al revisar las historias (2026-11-15): RN-35 precisa la inactividad en un registro en curso; RN-37: las franjas del mismo día no pueden cruzarse; RF-107: el encabezado muestra las horas del turno, sin nombre. No cambia el alcance. |
| 1.5 | **CHG-003** (observación del profesor, aprobada el 2026-11-22): el administrador crea y administra las celdas. RF-103 pasa a *Must* como "Gestionar celdas"; RN-27 se reemplaza por RN-48 a RN-53; RF-104 muestra las celdas inactivas. |

Etiquetas de origen: **[E]** enunciado · **[U]** equipo · **[I]** inferido, por confirmar.

---

## 1. Respuestas del equipo (2026-11-15)

| Pregunta | Respuesta | Dónde quedó |
|---|---|---|
| P-26 Permisos | El **operador** registra, modifica, inactiva y activa propietarios y vehículos. El administrador hace todo. | Matriz de permisos (sección 3) |
| P-27 Horarios | Son **fijos**: el operador **no puede iniciar sesión fuera de su turno**, salvo que el administrador lo autorice desde su sesión. | RN-31, RN-32, RF-107, RF-110 |
| P-28 Celdas | Las celdas son **fijas**: no se agregan ni cambian de tipo. **Reemplazada por CHG-003 (2026-11-22):** el administrador crea y administra las celdas. | RF-103 (*Must*), RN-48 a RN-53 |
| P-29 Vehículos | Placa mal escrita: se **inactiva** y se crea un **registro nuevo**. Cambio de propietario: **petición al administrador**, y debe quedar el registro del propietario anterior. | RN-26, RN-33, RF-109 |
| P-30 Teléfono | **Celular colombiano.** | RN-30 |
| P-31 Operadores | El administrador puede editar el nombre y restablecer la contraseña ("control sobre todo el sistema"). | RF-106 |
| P-32 Trazabilidad | Se debe **mostrar qué operador hizo qué operación.** | RF-111, DEC-013 |

---

## 2. Reglas de negocio propuestas

| ID | Regla | Origen |
|---|---|---|
| RN-25 | No se registran dos propietarios con la misma cédula ni dos vehículos con la misma placa. | [I] (ya lo garantiza el modelo) |
| RN-26 | La placa no se modifica. Si se registró mal, el vehículo se inactiva y se registra de nuevo con la placa correcta. | [U] P-29 |
| RN-27 (reemplazada) | *Reemplazada por CHG-003:* las celdas ya no son fijas (ver RN-48 a RN-53). | [U] P-28 |
| RN-48 | Solo el **administrador** crea, modifica, inactiva, reactiva y elimina celdas. El operador solo las consulta en el mapa. | [E] CHG-003, P-52 |
| RN-49 | **Código de celda:** único y con el formato de su tipo: `A-` y 3 dígitos para carro/camioneta (`A-001` a `A-999`) y `M-` y 2 dígitos para moto (`M-01` a `M-99`). Se escribe en mayúsculas; el sistema sugiere el siguiente código libre. El código no se modifica, salvo al cambiar el tipo de una celda que nunca se usó (RN-52): como el formato depende del tipo, recibe un código del tipo nuevo. | [E] CHG-003, P-53, P-55 |
| RN-50 | **Celda ocupada:** no se puede inactivar, cambiar de tipo ni eliminar mientras tenga un vehículo dentro. | [E] CHG-003 |
| RN-51 | **Celda inactiva** (por ejemplo, en mantenimiento): se inactiva con un motivo obligatorio; no se ofrece al registrar una entrada; en el mapa aparece marcada como inactiva. Se puede reactivar. | [U] P-54 |
| RN-52 | **Modificar y eliminar:** solo se cambia el tipo de una celda libre que nunca se ha usado. Solo se elimina una celda que nunca se ha usado; si ya tuvo estadías, se inactiva (RN-07). | [U] P-52, P-55 |
| RN-53 | Cada creación, modificación, inactivación, reactivación o eliminación de una celda queda en la **bitácora** (RN-34). No hay un número máximo de celdas fuera del límite del formato del código. | [U] P-56 |
| RN-29 | Al inactivar un propietario o un vehículo, si está dentro puede salir, pero no puede volver a entrar mientras siga inactivo (RN-24). | [I] |
| RN-30 | El teléfono del propietario es un celular colombiano: 10 dígitos que empiezan por 3 (por ejemplo, 3001234567). | [U] P-30 |
| RN-31 | Un operador solo puede iniciar sesión dentro de su turno. El administrador no tiene restricción de horario. | [U] P-27 |
| RN-32 | El administrador puede autorizar a un operador para ingresar fuera de su turno, **por el tiempo que el administrador defina** (desde, hasta). La autorización queda registrada con quién la dio y el motivo. | [U] P-27, P-34 |
| RN-33 | El cambio de propietario de un vehículo lo solicita un operador y lo aprueba o rechaza el administrador. Al aprobarse, el propietario anterior queda en el historial del vehículo con sus fechas. Los pagos siguen asociados al vehículo. | [U] P-29 |
| RN-35 | **Fin del turno con la sesión abierta:** (a) si el operador está realizando **cualquier registro** (propietario, vehículo, entrada, salida, novedad, etc.), el sistema **no** cierra la sesión mientras siga escribiendo, y la cierra cuando termine la operación (P-38). Si pasan **5 minutos sin que escriba nada**, se aplican los 5 minutos de aviso de (b); (b) si no, el sistema le avisa y le da **5 minutos** para cerrar sesión; pasado ese tiempo, la sesión se cierra automáticamente. Una autorización vigente (RN-32) evita el cierre. | [U] P-34 |
| RN-36 | Un operador **sin horario asignado no puede iniciar sesión**. Se admiten turnos **nocturnos** que cruzan la medianoche (por ejemplo, 22:00–06:00). | [U] P-35 |
| RN-37 | Las franjas de un mismo operador en un mismo día **no pueden cruzarse**. | [U] (revisión de HU-020) |
| RN-34 | Toda operación que crea, modifica, activa o inactiva datos queda registrada con el usuario, la fecha y hora, y qué cambió. | [U] P-32 |

---

## 3. Matriz de permisos (RNF-002)

| Operación | Operador | Administrador |
|---|:-:|:-:|
| Registrar, modificar, activar e inactivar propietarios y vehículos | ✔ | ✔ |
| Solicitar un cambio de propietario | ✔ | ✔ |
| Aprobar o rechazar un cambio de propietario | — | ✔ |
| Consultar propietarios, vehículos y el mapa de celdas | ✔ | ✔ |
| Crear, modificar, inactivar, reactivar y eliminar celdas (CHG-003) | — | ✔ |
| Gestionar operadores: crear, editar, restablecer contraseña, activar e inactivar | — | ✔ |
| Definir horarios y autorizar ingresos fuera de turno | — | ✔ |
| Consultar la bitácora de un vehículo o propietario (en su ficha) | ✔ | ✔ |
| Consultar la bitácora completa | — | ✔ |

---

## 4. Requerimientos funcionales

### RF-101 — Registrar propietario
- **Actor:** Operador, Administrador.
- **Entradas:** nombre completo, cédula, celular, correo y dirección. Todos obligatorios.
- **Validaciones:** cédula de 5 a 10 dígitos y sin repetirse (RN-25); celular según RN-30; correo válido.
- **Prioridad:** Must.
- **Criterios:**
  - Registro correcto: el propietario queda activo y la bitácora muestra quién lo registró.
  - Cédula repetida → "Ya existe un propietario con esa cédula".
  - Celular inválido → "El celular debe tener 10 dígitos y empezar por 3".

### RF-102 — Registrar vehículo
- **Actor:** Operador, Administrador.
- **Entradas:** placa, tipo, marca, nombre (línea), modelo (año), color y propietario, que se elige buscando por cédula o nombre.
- **Validaciones:** formato de placa acorde al tipo (RN-23); placa única (RN-25); modelo entre 1950 y el año siguiente al actual; propietario activo.
- **Prioridad:** Must.
- **Nota:** para entrar, el vehículo necesita además una mensualidad pagada (RN-03). Los pagos se registran en la iteración 3.

### RF-103 — Gestionar celdas (CHG-003)
- **Actor:** Administrador.
- **Descripción:** crear una celda (tipo y código, con el siguiente código sugerido), cambiar su tipo, inactivarla con motivo, reactivarla y, si nunca se usó, eliminarla. Ver la lista de celdas con su estado (libre, ocupada o inactiva), filtrar por tipo y estado, y buscar por código.
- **Validaciones:** código único y con el formato de su tipo (RN-49); una celda ocupada no se inactiva, no cambia de tipo ni se elimina (RN-50); solo se cambia el tipo o se elimina una celda que nunca se usó (RN-52).
- **Reglas:** RN-48 a RN-53.
- **Prioridad:** Must.
- **Historial:** en la versión 1.1 quedó como *Won't* porque las celdas eran fijas (P-28). La solicitud de cambio CHG-003 lo incorporó después de la observación del profesor.

### RF-104 — Mapa de celdas
- **Actor:** Operador, Administrador.
- **Descripción:** todas las celdas por zona (A: carro/camioneta, M: moto), con su estado (libre, ocupada con la placa, o inactiva) y contadores. El inventario es el que defina el administrador (RF-103).
- **Prioridad:** Must.

### RF-105 — Modificar, activar e inactivar propietarios y vehículos
- **Actor:** Operador, Administrador.
- **Descripción:** corregir datos y cambiar el estado activo/inactivo. Nunca se borra (RN-07).
- **Restricciones:** la placa no se edita (RN-26); el propietario no se cambia aquí (RF-109).
- **Reactivación tras el pago:** pasa a la iteración 3 (P-33). En la iteración 2, la activación e inactivación son manuales.
- **Prioridad:** Must.

### RF-106 — Gestionar operadores (completar)
- **Actor:** Administrador.
- **Agrega a HU-010:** editar el nombre y restablecer la contraseña.
- **Prioridad:** Must.

### RF-107 — Horarios de operador
- **Actor:** Administrador.
- **Descripción:** define el turno de cada operador. Al iniciar sesión, el sistema verifica que la hora actual esté dentro del turno (RN-31); si no lo está: "Estás fuera de tu turno. Solicita autorización al administrador". El encabezado muestra las horas del turno, por ejemplo "Operador · Turno 06:00 – 14:00" (sin nombre de turno).
- **Turnos:** franjas por día de la semana; pueden cruzar la medianoche (RN-36). Sin horario no hay ingreso (RN-36). Al terminar el turno se aplica RN-35. Puede haber **varias franjas el mismo día**, si el administrador las asigna (P-37).
- **Prioridad:** Must.

### RF-108 — Consultar propietarios y vehículos
- **Actor:** Operador, Administrador.
- **Descripción:** buscar por nombre, cédula o placa. La ficha del propietario muestra sus vehículos, si están dentro o fuera y su estado. La ficha del vehículo muestra el **historial de propietarios** (RN-33) y la bitácora de cambios (RF-111).
- **Prioridad:** Must.

### RF-109 — Solicitar y aprobar un cambio de propietario (nuevo)
- **Actor:** Operador (solicita) y Administrador (aprueba o rechaza).
- **Flujo:**
  1. El operador elige el vehículo y el nuevo propietario, que debe estar registrado, y escribe el motivo.
  2. La solicitud queda **pendiente**.
  3. El administrador la ve en una bandeja y la aprueba o rechaza con una observación.
  4. Si la aprueba, el vehículo pasa al nuevo propietario y el anterior queda en el historial con las fechas.
- **Reglas:** RN-33. Solo puede haber una solicitud pendiente por vehículo [I].
- **Prioridad:** Must.

### RF-110 — Autorizar ingreso fuera de turno (nuevo)
- **Actor:** Administrador.
- **Descripción:** desde su sesión, el administrador autoriza a un operador a ingresar fuera de su turno, con un motivo y una vigencia que él define (desde y hasta). Mientras esté vigente, el operador puede iniciar sesión y no se le cierra la sesión por fin de turno (RN-32, RN-35). Queda en la bitácora.
- **Prioridad:** Must.

### RF-111 — Bitácora de operaciones (nuevo)
- **Actor:** Administrador (bitácora completa) y Operador (solo la de un vehículo o propietario, en su ficha; P-36).
- **Descripción:** registro automático de cada operación (registrar, modificar, activar, inactivar, solicitar o aprobar un cambio de propietario, crear o editar operadores, horarios, autorizaciones). Muestra quién, cuándo, qué entidad y qué cambió. Se puede filtrar por usuario, fecha y tipo de operación.
- **Reglas:** RN-34.
- **Prioridad:** Must.
- **Implementación:** bitácora de operaciones (DEC-013, aprobada).

---

## 5. Decisiones (aprobadas el 2026-11-15)

### DEC-013 — Cómo registrar "qué operador hizo qué operación" (P-32)
- **A. Columnas en cada tabla** (`creado_por`, `modificado_por`, fechas): simple, pero solo guarda la **última** modificación.
- **B. Bitácora de operaciones** (una tabla: usuario, fecha y hora, acción, entidad, identificador, detalle de los cambios): guarda **todas** las operaciones y permite mostrarlas por vehículo, propietario o usuario.
- **Recomendación: B.** Es lo que pide la respuesta del equipo ("qué operador hizo qué operación"). También permite mostrar las entradas, salidas y novedades, que ya guardan su usuario.
- **Impacto:** una tabla nueva en el modelo de datos (v1.3).

### DEC-014 — Modelo de horarios y autorizaciones (P-27)
- **A. Franjas por día de la semana** (la tabla provisional actual, `HorarioOperador`): cada operador tiene una o más franjas por día (inicio y fin), y se permite cruzar la medianoche (inicio > fin, por ejemplo 22:00–06:00). Se agrega una tabla de autorizaciones fuera de turno: operador, autorizado por, motivo, desde, hasta.
- **B. Turnos con nombre** (Mañana, Tarde, Noche, con horas fijas) asignados a cada operador.
- **Recomendación: A.** Ya está en el modelo, es más flexible y permite mostrar un nombre de turno calculado (mañana, tarde o noche) en el encabezado.
- **Impacto:** se confirma `HorarioOperador`, que deja de ser provisional, y se agrega la tabla de autorizaciones.

### DEC-015 — Cambio de propietario con historial (P-29)
- **A. Solicitud + historial:** tabla `SolicitudCambioPropietario` (vehículo, propietario actual, propietario nuevo, motivo, solicitado por, estado, resuelto por, observación, fechas) y tabla `HistorialPropiedad` (vehículo, propietario, desde, hasta).
- **B. Solo historial**, sin solicitud: el administrador hace el cambio directamente.
- **Recomendación: A.** Cumple "petición al administrador" y conserva al propietario anterior.
- **Impacto:** dos tablas nuevas (modelo v1.3).

---

## 6. Preguntas

**Resueltas el 2026-11-15:**
- **P-33:** se deja para la iteración 3. Allí se definirá el motivo de inactivación y la reactivación automática al pagar.
- **P-34:** RN-32 y RN-35.
- **P-35:** se admiten turnos nocturnos; sin horario no hay ingreso (RN-36).
- **P-36:** se aprueba la propuesta. El operador ve la bitácora solo en la ficha de un vehículo o propietario.

- **P-37:** sí, puede haber varias franjas el mismo día si el administrador las asigna.
- **P-38:** la regla vale para cualquier registro en curso; el sistema no cierra la sesión hasta que termine la operación.

**Decisiones:** DEC-013, DEC-014 y DEC-015 aprobadas el 2026-11-15 (ver `Registro_Decisiones.md`).

No quedan preguntas abiertas en los requerimientos de la iteración 2.
