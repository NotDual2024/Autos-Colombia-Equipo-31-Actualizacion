# Requerimientos — Iteración 1: Gestión de la entrada y salida de vehículos

**Proyecto:** Parqueadero "Autos Colombia"
**Versión:** 2.10. Reemplaza a `Requerimientos_v1.md`, que se conserva como historial.
**Fecha:** 2026-11-15
**Estado:** **Aprobado** por el equipo del proyecto el 2026-11-15. Abarca las secciones 1 a 4 de la iteración 1. El anexo A sigue siendo solo una referencia y se detallará y aprobará en su iteración.

## Historial de versiones

| Versión | Fecha | Cambios |
|---|---|---|
| 1 | 2026-11-15 | Borrador inicial con RF de los tres módulos y RNF. |
| 2 | 2026-11-15 | El documento se centra en la iteración 1. Incorpora las respuestas del equipo (P-01 a P-05 y P-07 en parte). Agrega los RF-009 a RF-011 (mensualidad vencida con el vehículo dentro). Corrige RNF-002 según los roles definidos. Los RF de las iteraciones 2 y 3 pasan al anexo A, solo como referencia para el modelo de datos (DEC-001). |
| 2.1 | 2026-11-15 | Incorpora DEC-002 (aviso por correo automático) y las respuestas a P-10, P-11, P-12 y P-07. Reescribe RF-007, RF-010 y RF-011. Agrega RN-14, RN-15 y RN-16, y RNF-012 y RNF-013. Actualiza las preguntas pendientes. |
| 2.2 | 2026-11-15 | Confirma RN-13. Resuelve P-15 (un solo correo el día del vencimiento, con aviso de pago y de consecuencias) y P-16 (la presencia de cada vehículo se verifica al registrar una novedad). Ajusta RN-11, RF-009, RF-010, RF-011 y RF-007. |
| 2.3 | 2026-11-15 | Confirma RN-17. Resuelve P-17 con la alternativa A: las novedades no llevan adjuntos en esta versión (RN-18). Ya no hay preguntas que bloqueen la iteración 1. |
| 2.4 | 2026-11-15 | Resuelve P-14 (RF-003 y RF-005), P-06 (capacidad de 150 celdas de carro/camioneta y 50 de moto, operación 24 horas), P-08 (tarifas por tipo, RN-19) y P-09 (proyecto académico de ejecución local). Ajusta RNF-006, RNF-009, RNF-010 y RNF-011. |
| 2.4 | 2026-11-15 | **Aprobada** por el equipo. Sin cambios de contenido. |
| 2.4.1 | 2026-11-15 | Aclaraciones indicadas por el equipo al revisar las historias de usuario. RF-011: solo el administrador registra el contacto con las autoridades (antes decía "y Operador, si se aprueba"). El plazo se cumple cuando hoy ≥ vencimiento + 8 días. No cambia el alcance. |
| 2.5 | 2026-11-15 | **CHG-001, aprobado por el equipo:** se agrega RNF-014 (datos de demostración con un administrador y un operador de prueba), porque el profesor ejecutará el sistema en su máquina. Se agrega a RNF-010 que el sistema está pensado para estar activo 24/7. |
| 2.6 | 2026-11-15 | **DEC-011 (aprobada):** RF-106 se adelanta a la iteración 1 en su versión básica (sección 3, RF-106). **P-19 (aprobada):** se agrega RN-21. |
| 2.7 | 2026-11-15 | **DEC-007 (aprobada):** RF-010 pasa a ser simulado; se agrega RF-012 (botón "Enviar correo", simulado); RNF-012 baja a Could mientras no haya correo real. P-20 queda abierta para RF-012. |
| 2.8 | 2026-11-15 | **P-20 resuelta por el equipo:** se agrega RN-22 (reenvío con confirmación, máximo 2 reenvíos) y se completan los criterios de RF-012. |
| 2.9 | 2026-11-15 | Aclaración del equipo sobre RN-22: un solo reenvío (2 correos en total), no 2 reenvíos. |
| 2.10 | 2026-11-15 | Respuestas P-22 a P-25 (revisión del modelo de datos): nueva RN-23 (formato de placa); RN-22 aclara que los envíos fallidos no cuentan; RF-011 permite varios contactos por vencimiento; RF-101 y RF-102 detallan sus datos. |

## 0. Convenciones

### Origen de cada elemento

| Etiqueta | Significado |
|---|---|
| **[E]** | Está en el enunciado. |
| **[U]** | Lo indicó el equipo. |
| **[I]** | Lo infiere el arquitecto. Hay que confirmarlo. |
| **[S]** | Supuesto provisional. No es una decisión. |

### Identificadores por iteración

| Iteración | Rango | Estado |
|---|---|---|
| 1. Entrada y salida de vehículos (incluye novedades) | RF-001 a RF-099 | En análisis |
| 2. Gestión de usuarios y celdas | RF-101 a RF-199 | Solo identificados (anexo A) |
| 3. Gestión de pagos | RF-201 a RF-299 | Solo identificados (anexo A) |

### Prioridad (MoSCoW)

Must, Should, Could, Won't (por ahora).

---

## 1. Actores

| Actor | Descripción | Origen |
|---|---|---|
| Administrador | Tiene acceso a toda la información y a todas las funciones. Crea operadores y les asigna horario. | [U] |
| Operador | Registra entradas, salidas y novedades. Registra clientes, consulta vehículos y mensualidades y registra pagos. | [U] La parte de entradas, salidas y novedades es [I] |
| Propietario (cliente) | Dueño de uno o varios vehículos. No usa el sistema. Recibe un correo automático cuando la mensualidad vence con el vehículo dentro. | [U] DEC-002 |
| Servicio de correo | Sistema externo que entrega los correos al propietario. | DEC-002. El proveedor está pendiente. |

> En la iteración 1, los dos roles operan entradas, salidas y novedades. El administrador puede hacer todo lo que hace el operador.

---

## 2. Reglas de negocio

| ID | Regla | Origen |
|---|---|---|
| RN-01 | El servicio se presta solo por mensualidad. No hay cobro por horas. | [E][U] |
| RN-02 | Los tipos de vehículo admitidos son moto, carro y camioneta. | [U] |
| RN-03 | Solo puede **ingresar** un vehículo con la mensualidad pagada y vigente. | [U] |
| RN-04 | Un vehículo no puede tener más de una entrada abierta al mismo tiempo. | [I] |
| RN-05 | Una celda no puede estar ocupada por más de un vehículo al mismo tiempo. | [I] |
| RN-06 | Una novedad solo se registra si el hecho ocurrió dentro de las instalaciones. Queda con fecha, hora y usuario que la registró. | [U] |
| RN-07 | Los registros de entradas, salidas y novedades no se eliminan. | [I] |
| RN-08 | Hay dos tipos de celda: **moto** y **carro/camioneta**. Una moto solo ocupa una celda de moto. Un carro o una camioneta solo ocupan una celda de carro/camioneta. | [U] |
| RN-09 | El vehículo ocupa cualquier celda libre de su tipo. No hay celdas fijas por mensualidad. | [U] |
| RN-10 | La mensualidad se paga por vehículo. Un cliente con varios vehículos paga una mensualidad por cada uno, según la tarifa de cada vehículo (RN-19). | [U] |
| RN-11 | Si la mensualidad de un vehículo vence mientras está dentro, el sistema envía **un solo correo** al propietario **el día del vencimiento**. El correo le indica que debe pagar la mensualidad para mantener el vehículo en el parqueadero y que, si no lo hace, habrá consecuencias. No se envían recordatorios. | [U] DEC-002 (P-15 resuelta) |
| RN-12 | Si el vehículo sigue dentro **8 días después del vencimiento de la mensualidad**, se contacta a las autoridades para retirarlo. | [U] (P-12 resuelta) |
| RN-13 | La salida de un vehículo se permite aunque su mensualidad esté vencida. No podrá volver a ingresar mientras la mensualidad siga sin pagarse (RN-03). | [U] (confirmada) |
| RN-17 | Si el propietario paga la mensualidad dentro de los 8 días, el vehículo sale del proceso de retiro y puede seguir dentro. | [U] (confirmada) |
| RN-18 | Las novedades no llevan fotos ni archivos adjuntos en esta versión. La documentación se hace con el tipo, la descripción, la fecha y hora del hecho y los vehículos involucrados. | [U] (P-17, alternativa A). Los adjuntos quedan como Won't por ahora. |
| RN-19 | La tarifa mensual depende del tipo de vehículo: **carro o camioneta, 150 000 COP**; **moto, 80 000 COP**. | [U] (P-08). Se aplica en la iteración 3. |
| RN-20 | El parqueadero opera las 24 horas. Por ahora tiene **150 celdas de carro/camioneta** y **50 celdas de moto**. | [U] (P-06). Como el equipo dijo "por el momento", la cantidad de celdas se trata como un dato configurable y no como un valor fijo en el código [I]. |
| RN-21 | Si el servidor estuvo apagado el día del vencimiento, el correo pendiente se envía al encenderlo, siempre que el vehículo siga dentro y sin pagar. El plazo de RN-12 se sigue contando desde el vencimiento. | [U] (P-19) |
| RN-22 | Después del primer correo de un vencimiento (automático o manual), el botón "Enviar correo" sigue disponible, pero pide confirmación para reenviar. Se permite **un solo reenvío** por vencimiento, es decir, **2 correos en total**: el primero y un reenvío. Solo cuentan los envíos exitosos; un intento fallido se registra y se puede reintentar. | [U] (P-20, aclarado por el equipo el 2026-11-15) |
| RN-23 | La placa se guarda en mayúsculas y sin espacios. Formatos válidos: carro o camioneta `ABC123`; moto `ABC12D` o `ABC12` (antigua). El formato debe corresponder al tipo de vehículo. | [U] (P-22). La correspondencia entre formato y tipo es [I]. |
| RN-14 | Una novedad tiene un identificador propio y puede involucrar **uno o varios vehículos**. Un rayón entre dos vehículos es una sola novedad vinculada a los dos. | [U] (P-10 resuelta) |
| RN-15 | Una novedad es solo un registro documental. No tiene estado (abierta o cerrada) ni seguimiento. | [U] (P-07 resuelta en parte) |
| RN-16 | Una novedad se puede registrar mientras el vehículo está dentro o después de su salida. Siempre debe referirse a un hecho ocurrido dentro de las instalaciones. | [U] (P-11 resuelta) |

**Cómo se relacionan RN-03 y RN-11/RN-12.** RN-03 controla el **ingreso**. Un vehículo que ya está dentro y cuya mensualidad vence no se bloquea dentro del sistema: entra en el proceso de retiro de RN-11 y RN-12.

---

## 3. Requerimientos funcionales — Iteración 1

### RF-001 — Registrar entrada de vehículo

| Campo | Detalle |
|---|---|
| Descripción | El sistema registra el ingreso de un vehículo. |
| Actor | Operador, Administrador |
| Entradas | Placa y celda elegida (RF-003). |
| Proceso | 1. Busca el vehículo por placa. 2. Verifica la mensualidad (RF-002). 3. Verifica que no tenga una entrada abierta. 4. Asigna la celda (RF-003). 5. Guarda la entrada con la fecha y hora del servidor y el usuario. 6. Marca la celda como ocupada. |
| Salidas | Confirmación con placa, tipo, celda y hora de ingreso. |
| Reglas | RN-03, RN-04, RN-05, RN-08, RN-09 |
| Prioridad | Must |
| Dependencias | RF-002, RF-003. Necesita datos de RF-102 (vehículos) y RF-103 (celdas). |
| Origen | [E] |

**Criterios de aceptación**

- Dado un vehículo registrado, con mensualidad vigente y sin entrada abierta, cuando el operador registra su entrada en una celda libre compatible, entonces se guarda la entrada con fecha, hora y usuario, y la celda queda ocupada.
- Dado un vehículo con una entrada abierta, cuando se intenta registrar otra entrada, entonces el sistema la rechaza con el mensaje "El vehículo ya se encuentra dentro".
- Dada una placa que no está registrada, cuando se intenta registrar la entrada, entonces el sistema la rechaza con el mensaje "Vehículo no registrado".

### RF-002 — Verificar vigencia de la mensualidad al ingresar

| Campo | Detalle |
|---|---|
| Descripción | Antes de autorizar una entrada, el sistema comprueba que el vehículo tenga una mensualidad pagada que cubra la fecha actual. |
| Actor | Sistema (lo dispara RF-001) |
| Reglas | RN-03, RN-10 |
| Prioridad | Must |
| Dependencias | Necesita datos de RF-201 (pagos). Para probarlo en la iteración 1 se cargan pagos de prueba. |
| Origen | [U] |

**Criterios de aceptación**

- Dado un vehículo sin un pago que cubra la fecha actual, cuando se intenta registrar su entrada, entonces el sistema la rechaza con el mensaje "Mensualidad no vigente".
- Dado un cliente con dos vehículos y pago vigente solo para uno, cuando se intenta registrar la entrada del otro, entonces el sistema la rechaza (RN-10).

### RF-003 — Asignar celda libre compatible

| Campo | Detalle |
|---|---|
| Descripción | El vehículo puede estacionarse en cualquier celda disponible de su tipo. Al registrar la entrada, el operador indica en qué celda quedó. El sistema solo acepta celdas libres y compatibles con el tipo de vehículo. |
| Actor | Operador, Administrador |
| Reglas | RN-05, RN-08, RN-09 |
| Prioridad | Must |
| Origen | [U] (P-14) |

**Criterios de aceptación**

- Dada una moto, cuando se registra su entrada, entonces el sistema solo ofrece celdas de moto libres.
- Dado un carro o una camioneta, cuando se registra su entrada, entonces el sistema solo ofrece celdas de carro/camioneta libres.
- Dado que no hay celdas libres del tipo requerido, cuando se intenta registrar la entrada, entonces el sistema la rechaza con el mensaje "No hay celdas disponibles para este tipo de vehículo".

### RF-004 — Registrar salida de vehículo

| Campo | Detalle |
|---|---|
| Descripción | El sistema registra la salida de un vehículo que está dentro. |
| Actor | Operador, Administrador |
| Entradas | Placa. |
| Proceso | 1. Busca la entrada abierta. 2. Guarda la fecha y hora de salida y el usuario. 3. Libera la celda. 4. Si el vehículo estaba en proceso de retiro (RF-010), lo cierra. |
| Reglas | RN-04, RN-05, RN-13 |
| Prioridad | Must |
| Origen | [E] |

**Criterios de aceptación**

- Dado un vehículo dentro, cuando se registra su salida, entonces se cierra la entrada con fecha, hora y usuario, y la celda queda libre.
- Dado un vehículo dentro con la mensualidad vencida, cuando se registra su salida, entonces el sistema la permite (RN-13).
- Dado un vehículo que no está dentro, cuando se intenta registrar su salida, entonces el sistema la rechaza con el mensaje "El vehículo no se encuentra dentro".

### RF-005 — Consultar vehículos dentro del parqueadero

| Campo | Detalle |
|---|---|
| Descripción | El sistema lista los vehículos que están dentro en este momento, con tipo, celda y hora de ingreso. Se puede filtrar por tipo. También permite consultar una celda específica para saber si está ocupada y por qué vehículo. |
| Actor | Operador, Administrador |
| Prioridad | Must (la consulta de celda la pidió el equipo) |
| Origen | [I] la lista; [U] la consulta por celda (P-14) |

**Criterios de aceptación**

- Dados N vehículos con entrada abierta, cuando se consulta la ocupación, entonces se muestran exactamente esos N vehículos.
- Dada una celda ocupada, cuando el operador la consulta, entonces el sistema muestra la placa del vehículo y su hora de ingreso.
- Dada una celda libre, cuando el operador la consulta, entonces el sistema indica que está disponible.

### RF-006 — Consultar historial de entradas y salidas

| Campo | Detalle |
|---|---|
| Descripción | El sistema lista los movimientos, filtrando por placa y por rango de fechas. |
| Actor | Operador, Administrador |
| Prioridad | Should |
| Origen | [I] |

**Criterios de aceptación**

- Dado un rango de fechas, cuando se consulta el historial, entonces se muestran solo los movimientos cuyo ingreso cae en ese rango.

### RF-007 — Registrar novedad

| Campo | Detalle |
|---|---|
| Descripción | El sistema registra, como documentación, un hecho ocurrido dentro de las instalaciones que involucra a uno o más vehículos. Ejemplos: una moto que se cayó, un vehículo que rayó a otro. |
| Actor | Operador, Administrador |
| Entradas | Una o varias placas involucradas, tipo de novedad (accidente, rayón, caída, daño, otro), fecha y hora en que ocurrió, y descripción. |
| Proceso | 1. Asigna un identificador único a la novedad. 2. Para **cada** placa, comprueba que el vehículo estaba dentro en la fecha y hora indicadas, es decir, que esa fecha cae dentro de una de sus estadías. Si alguno de los vehículos no estaba dentro, rechaza la novedad completa. 3. Vincula la novedad con cada vehículo y su estadía. 4. Guarda la fecha y hora de registro (del servidor) y el usuario. |
| Salidas | Confirmación con el identificador de la novedad y los vehículos vinculados. |
| Reglas | RN-06, RN-07, RN-14, RN-15, RN-16, RN-18 |
| Prioridad | Must |
| Origen | [E][U] |

**Criterios de aceptación**

- Dado un vehículo dentro, cuando se registra una novedad con tipo, fecha de ocurrencia y descripción, entonces se guarda con un identificador, la fecha de registro, el usuario y el vínculo al vehículo y su estadía.
- Dado un rayón entre dos vehículos, cuando se registra la novedad con las dos placas, entonces existe **una sola** novedad vinculada a los dos vehículos.
- Dado un vehículo que ya salió, cuando se registra una novedad cuya fecha de ocurrencia cae dentro de su última estadía, entonces el sistema la acepta.
- Dada una fecha de ocurrencia en la que el vehículo no estaba dentro, cuando se intenta registrar la novedad, entonces el sistema la rechaza.
- Dada una novedad con dos placas en la que solo una estaba dentro a la hora del hecho, cuando se intenta registrar, entonces el sistema la rechaza completa e indica qué placa no estaba dentro.
- Dada una novedad sin descripción o sin vehículos, cuando se intenta guardar, entonces el sistema la rechaza.
- Dada una novedad registrada, entonces no existen operaciones para cambiar su estado ni para borrarla (RN-07, RN-15).

### RF-008 — Consultar novedades

| Campo | Detalle |
|---|---|
| Descripción | El sistema lista las novedades, filtrando por placa, tipo y rango de fechas. Se muestran de la más reciente a la más antigua. |
| Actor | Operador, Administrador |
| Prioridad | Should |
| Origen | [I] |

**Criterios de aceptación**

- Dada una placa con novedades registradas, cuando se consultan sus novedades, entonces se muestran todas, de la más reciente a la más antigua.

### RF-009 — Identificar vehículos dentro con mensualidad vencida

| Campo | Detalle |
|---|---|
| Descripción | El sistema lista los vehículos que están dentro y cuya mensualidad ya venció. Muestra los días transcurridos y el estado del proceso de retiro. |
| Actor | Operador, Administrador |
| Reglas | RN-11, RN-12 |
| Prioridad | Must |
| Origen | [U] |

**Criterios de aceptación**

- Dado un vehículo dentro cuya mensualidad venció ayer, cuando se consulta la lista, entonces aparece con 1 día transcurrido.
- Dado un vehículo dentro con la mensualidad vigente, cuando se consulta la lista, entonces no aparece.
- Dado un vehículo de la lista cuyo propietario paga la mensualidad, cuando se vuelve a consultar, entonces ya no aparece (RN-17).

### RF-010 — Enviar correo automático de retiro al propietario (simulado, DEC-007)

| Campo | Detalle |
|---|---|
| Descripción | El sistema detecta los vehículos dentro con la mensualidad vencida y **simula** el envío automático de un correo al propietario (DEC-007): no sale ningún correo real, pero el mensaje completo y el envío quedan registrados y visibles en la aplicación. |
| Actor | Sistema (proceso programado con APScheduler, DEC-008). El servicio de correo es simulado. |
| Entradas | Vehículos de RF-009 y correo del propietario. |
| Proceso | 1. El proceso se ejecuta al iniciar el servidor y cada hora (DEC-008). 2. Por cada vehículo dentro con la mensualidad vencida y sin correo registrado para ese vencimiento, simula el envío (también los que quedaron pendientes con el servidor apagado, RN-21). 3. Registra el envío con la fecha y hora, el destinatario, el vehículo, el texto, el origen (automático) y el resultado ("enviado (simulado)" o "fallido"). |
| Contenido del correo | Placa, fecha de vencimiento, aviso de que debe pagar la mensualidad para mantener el vehículo y advertencia de que, si no paga, habrá consecuencias (contacto con las autoridades a los 8 días, RN-12). El texto exacto se acordará con el equipo. |
| Reglas | RN-11, RN-12 |
| Prioridad | Must |
| Dependencias | RF-009, DEC-002, RF-101 (correo del propietario) |
| Origen | [U] DEC-002 |

**Criterios de aceptación**

- Dado un vehículo dentro cuya mensualidad vence hoy, cuando se ejecuta el proceso programado, entonces se simula el envío del correo al propietario y queda registrado como "enviado (simulado)" con origen "automático".
- Dado un vehículo al que ya se le envió el correo por ese vencimiento, cuando el proceso vuelve a ejecutarse, entonces no se envía otro correo (sin recordatorios).
- Dado un fallo del servicio de correo simulado (forzado en las pruebas), cuando se intenta el envío, entonces queda registrado como "fallido" y aparece en RF-009 para que el personal lo vea (RNF-013).
- Dado un vehículo que salió antes de ejecutarse el proceso, entonces no se le envía correo.

### RF-011 — Alertar vencimiento del plazo de retiro

| Campo | Detalle |
|---|---|
| Descripción | El sistema destaca los vehículos que siguen dentro 8 días o más después del vencimiento de su mensualidad. Permite registrar que se contactó a las autoridades (fecha, usuario y observación). |
| Actor | Administrador (exclusivo; confirmado por el equipo el 2026-11-15) |
| Reglas | RN-12 |
| Prioridad | Must |
| Origen | [U] |

**Criterios de aceptación**

- Dado un vehículo que sigue dentro y cuya mensualidad venció hace 8 días o más, cuando se consulta la lista, entonces aparece marcado como "Plazo vencido – contactar autoridades".
- Dado ese vehículo, cuando se registra el contacto con las autoridades, entonces queda guardado con fecha, usuario y observación.
- Dado un vehículo con un contacto ya registrado, cuando el administrador registra otro (seguimiento), entonces también queda guardado (P-25).

### RF-012 — Enviar correo de retiro manualmente (simulado)

| Campo | Detalle |
|---|---|
| Descripción | En la lista de RF-009, cada vehículo tiene un botón **"Enviar correo"** para que el operador o el administrador simulen el envío del correo de RF-010 en ese momento. Sirve para la demostración. |
| Actor | Operador, Administrador |
| Entradas | Vehículo seleccionado en la lista de RF-009. |
| Proceso | 1. Arma el mismo mensaje de RF-010. 2. Simula el envío (no sale ningún correo). 3. Registra el envío con origen "manual", el usuario, la fecha y hora, el destinatario y el texto. 4. Muestra "Correo enviado (simulación)" con el contenido del mensaje. |
| Reglas | RN-11, RN-22 |
| Prioridad | Should |
| Dependencias | RF-009, RF-010 |
| Origen | [U] DEC-007 |

**Criterios de aceptación**

- Dado un vehículo de la lista RF-009, cuando el operador pulsa "Enviar correo", entonces el sistema muestra "Correo enviado (simulación)" con el texto del mensaje y registra el envío con origen "manual" y el usuario.
- Dado cualquier envío simulado, entonces no se contacta ningún servidor de correo real.
- Dado un vehículo al que ya se le registró un correo por ese vencimiento, cuando se pulsa el botón, entonces el sistema pregunta "Ya se envió un correo para este vencimiento. ¿Desea reenviarlo?" y solo lo reenvía si el usuario confirma.
- Dado un vehículo que ya tiene 1 reenvío para ese vencimiento, cuando se pulsa el botón, entonces el sistema no lo reenvía e informa "El correo de este vencimiento ya se reenvió una vez".

### RF-106 — Gestionar operadores (versión básica, adelantada a la iteración 1 por DEC-011)

| Campo | Detalle |
|---|---|
| Descripción | El administrador crea cuentas de operador y puede desactivarlas o reactivarlas. Un operador desactivado no puede iniciar sesión. Las cuentas no se borran (RN-07). |
| Actor | Administrador (exclusivo) |
| Entradas | Nombre completo, nombre de usuario y contraseña inicial. |
| Proceso | 1. Valida que el nombre de usuario no exista. 2. Guarda la contraseña con hash (RNF-001). 3. Crea el usuario con rol Operador y estado activo. |
| Salidas | Confirmación y lista de operadores con su estado. |
| Reglas | RN-07, RNF-001, RNF-002 |
| Prioridad | Must |
| Fuera de alcance en la iteración 1 | Horarios de operador (RF-107), edición de otros datos y recuperación de contraseña. |
| Origen | [U] DEC-011 |

**Criterios de aceptación**

- Dado el administrador, cuando crea un operador con un nombre de usuario nuevo, entonces el operador puede iniciar sesión con esas credenciales.
- Dado un nombre de usuario que ya existe, cuando el administrador intenta crear el operador, entonces el sistema lo rechaza con el mensaje "El nombre de usuario ya existe".
- Dado un operador desactivado, cuando intenta iniciar sesión, entonces el sistema se lo impide.
- Dado un operador con sesión iniciada, cuando intenta crear otro operador, entonces el sistema responde "acceso denegado".

---

## 4. Requerimientos no funcionales

Valen para todo el sistema y se verifican en cada iteración. Las cifras marcadas como **propuesta** son sugerencias del arquitecto.

| ID | Categoría | Descripción | Métrica o condición verificable | Prioridad |
|---|---|---|---|---|
| RNF-001 | Seguridad | Solo usuarios autenticados acceden al sistema. Las contraseñas se guardan con hash (bcrypt o Argon2). | Ninguna operación funciona sin sesión. No hay contraseñas en texto plano. | Must |
| RNF-002 | Seguridad | Acceso por rol. El **administrador** accede a todo. El **operador** no puede gestionar usuarios del sistema ni horarios. Las demás restricciones del operador se definen en la iteración 2. | Una operación restringida devuelve "acceso denegado" al operador. | Must |
| RNF-003 | Integridad | La entrada y la salida actualizan el movimiento y el estado de la celda en una sola transacción. RN-04 y RN-05 se cumplen aunque haya registros simultáneos. | En una prueba con dos registros simultáneos de la misma placa o celda, solo uno queda guardado. | Must |
| RNF-004 | Trazabilidad | Cada entrada, salida, novedad, notificación y pago guarda el usuario y la fecha y hora del servidor. No hay borrado (RN-07). | El 100 % de esos registros tiene usuario y fecha. | Must |
| RNF-005 | Usabilidad | Registrar una entrada o salida se hace con la placa y como máximo dos acciones. | **Propuesta:** máximo 2 acciones después de escribir la placa. | Should |
| RNF-006 | Rendimiento | Las operaciones responden con rapidez. | **Propuesta:** menos de 2 s por operación en el equipo local, con las 200 celdas ocupadas y al menos un año de historial de prueba. | Should |
| RNF-007 | Privacidad | Los datos personales de los propietarios se tratan según la Ley 1581 de 2012. | Solo los roles autorizados ven los datos personales. | Must |
| RNF-008 | Mantenibilidad | El código se organiza por módulos. Hay pruebas automatizadas de las reglas de negocio. | Cada RN implementada tiene al menos una prueba. | Must |
| RNF-009 | Recuperación | Copias de seguridad de la base de datos. | Como es un proyecto académico de ejecución local (P-09), basta con documentar cómo exportar y restaurar la base de datos. | Could |
| RNF-010 | Disponibilidad | El parqueadero opera 24 horas (RN-20) y el sistema está pensado para mantenerse activo 24/7. No impone restricciones de horario a las operaciones. Las estadías que cruzan la medianoche o varios días se registran y calculan correctamente. | Pruebas con entradas y salidas en días distintos y alrededor de la medianoche. | Must |
| RNF-011 | Portabilidad | El sistema corre en un equipo local (P-09). La instalación y la ejecución están documentadas en el README. | Una persona del equipo instala y ejecuta el sistema en otro equipo siguiendo solo el README. La plataforma (web local o escritorio) se define en arquitectura. | Must |
| RNF-012 | Seguridad | Si en el futuro se conecta un servicio de correo real, sus credenciales no van en el código ni en el repositorio (variables de entorno o un archivo excluido de Git). En esta versión el correo es simulado (DEC-007) y no hay credenciales. | Una revisión del repositorio no encuentra credenciales. | Could (Must cuando haya correo real) |
| RNF-013 | Fiabilidad | Un fallo del servicio de correo no detiene el sistema ni impide registrar entradas y salidas. El fallo queda registrado y visible. | En una prueba con el servicio de correo caído, las entradas y salidas siguen funcionando y el envío queda como "fallido". | Must |
| RNF-014 | Portabilidad / demostración | Un comando (`python manage.py cargar_datos_demo`) carga datos de demostración: un **administrador de prueba** y un **operador de prueba**, propietarios, vehículos de los tres tipos, las 200 celdas (RN-20) y pagos con fechas relativas al día de ejecución (vigentes, uno que vence hoy y uno vencido hace más de 8 días). Las credenciales de prueba se documentan en el README y son solo para la demostración. | En una instalación nueva, después de ejecutar el comando, se pueden recorrer todos los escenarios de HU-001 a HU-009 sin cargar datos a mano. | Must |

---

## 5. Validación del borrador

- **Contradicción resuelta:** en v1, RNF-002 decía que el operador no gestiona pagos. El equipo indicó que sí registra pagos, así que RNF-002 se corrigió.
- **Posible tensión entre RN-03 y RN-11:** se resolvió separando el control de ingreso (RN-03) del proceso de retiro (RN-11 y RN-12). Hay que confirmarlo.
- **Dependencias externas:** RF-002, RF-009, RF-010 y RF-011 usan datos de pagos (iteración 3). En la iteración 1 se probarán con pagos de prueba cargados directamente en la base de datos.
- **Consecuencias de DEC-002 en la arquitectura:** hay que elegir un servicio de correo (SMTP propio o un proveedor) y definir cómo se ejecuta el proceso programado de RF-010. Se presentarán como decisiones de arquitectura. En las pruebas se usará un servidor de correo simulado; no se enviarán correos reales.
- **Funcionalidad nueva detectada:** los horarios de operador se documentan en la iteración 2 (RF-107, anexo A).

## 6. Preguntas pendientes

**Resueltas en v2.1:** P-10 (RN-14), P-11 (RN-16), P-12 (RN-12), P-07 en lo que toca al estado (RN-15), y DEC-002 (correo automático).
**Resueltas en v2.2:** RN-13 (confirmada), P-15 (RN-11) y P-16 (RF-007).
**Resueltas en v2.3:** RN-17 (confirmada) y P-17 (RN-18).

**Resueltas en v2.4:** P-14 (RF-003, RF-005), P-06 (RN-20), P-08 (RN-19) y P-09 (RNF-009, RNF-011).

No quedan preguntas abiertas en los requerimientos de la iteración 1.

---

## Anexo A — Requerimientos de otras iteraciones (solo referencia para el modelo de datos)

No se detallan ni se aprueban en esta iteración.

### Iteración 2 — Gestión de usuarios y celdas

| ID | Nombre | Descripción breve | Origen |
|---|---|---|---|
| RF-101 | Registrar propietario | Nombre completo, cédula (CC), teléfono, **correo electrónico obligatorio** (DEC-002) y dirección. Lo hace el operador. | [E][U] |
| RF-102 | Registrar vehículo | Placa (RN-23), tipo, marca, nombre (línea), modelo (año), color y propietario. Un propietario puede tener varios vehículos. | [E][U] |
| RF-103 | Registrar celdas | Código y tipo (moto o carro/camioneta). Capacidad inicial: 150 de carro/camioneta y 50 de moto (RN-20). | [E][U] |
| RF-104 | Consultar estado de celdas | Libres y ocupadas, por tipo. | [E] |
| RF-105 | Modificar propietarios, vehículos y celdas | Actualizar datos y activar o inactivar. | [I] |
| RF-106 | Gestionar operadores | **Versión básica adelantada a la iteración 1 (DEC-011, ver sección 3).** En la iteración 2 se completa si hace falta. | [U] |
| RF-107 | Asignar horario a operadores | El administrador define el horario de cada operador. | [U] |

### Iteración 3 — Gestión de pagos

| ID | Nombre | Descripción breve | Origen |
|---|---|---|---|
| RF-201 | Registrar pago de mensualidad | Por vehículo: periodo cubierto, valor y fecha. Lo hace el operador. | [E][U] |
| RF-202 | Consultar vigencia de la mensualidad | Si un vehículo está al día. | [U] |
| RF-203 | Consultar historial de pagos | Por vehículo o por propietario. | [I] |
| RF-204 | Gestionar tarifas | Valor de la mensualidad por tipo de vehículo: carro/camioneta 150 000 COP, moto 80 000 COP (RN-19). | [U] |
