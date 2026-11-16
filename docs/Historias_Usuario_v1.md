# Historias de usuario — Iteración 1: Gestión de la entrada y salida de vehículos

**Proyecto:** Parqueadero "Autos Colombia"
**Versión:** 1
**Fecha:** 2026-11-15
**Base:** Requerimientos v2.4.1 (aprobados el 2026-11-15)
**Estado:** **Aprobado** por el equipo del proyecto el 2026-11-15 (HU-001 a HU-009). HU-010 y HU-011 se agregaron y aprobaron el mismo día.

## Criterios de redacción

- Cada historia sale de uno o más RF aprobados. No se agregan funcionalidades nuevas.
- RF-002 (verificar la mensualidad) y RF-003 (asignar la celda) no tienen historia propia: son pasos de la misma acción del operador que registra la entrada, así que van dentro de HU-001 como criterios de aceptación.
- Los criterios de aceptación usan el formato Dado / Cuando / Entonces y servirán como base para las pruebas funcionales del Ingeniero.
- Los mensajes de error entre comillas son textos propuestos. Se pueden ajustar sin cambiar la regla.

## Resumen

| ID | Título | Actor | RF | Prioridad |
|---|---|---|---|---|
| HU-001 | Registrar la entrada de un vehículo | Operador | RF-001, RF-002, RF-003 | Must |
| HU-002 | Registrar la salida de un vehículo | Operador | RF-004 | Must |
| HU-003 | Consultar ocupación y celdas | Operador | RF-005 | Must |
| HU-004 | Consultar el historial de movimientos | Administrador | RF-006 | Should |
| HU-005 | Registrar una novedad | Operador | RF-007 | Must |
| HU-006 | Consultar novedades | Administrador | RF-008 | Should |
| HU-007 | Ver vehículos dentro con mensualidad vencida | Operador | RF-009 | Must |
| HU-008 | Avisar automáticamente al propietario por correo | Administrador | RF-010 | Must |
| HU-009 | Controlar el plazo de 8 días y el contacto con autoridades | Administrador | RF-011 | Must |
| HU-010 | Crear y desactivar operadores | Administrador | RF-106 | Must |
| HU-011 | Enviar el correo de retiro desde un botón (simulado) | Operador | RF-012 | Should |

> Las historias de los RF donde actúan los dos roles se escriben desde el actor principal. El administrador puede hacer todo lo que hace el operador (sección 1 de los requerimientos).

---

## HU-001 — Registrar la entrada de un vehículo

**Historia:** Como **operador**, quiero registrar la entrada de un vehículo con su placa y la celda donde se estacionó, para controlar qué vehículos están dentro y qué celdas están ocupadas.

**Descripción:** El operador escribe la placa. El sistema verifica que el vehículo esté registrado, que tenga la mensualidad vigente y que no esté ya dentro. El operador indica la celda donde quedó el vehículo, que debe estar libre y ser del tipo correcto.

**Requerimientos:** RF-001, RF-002, RF-003
**Reglas:** RN-03, RN-04, RN-05, RN-08, RN-09, RN-10, RN-13
**Prioridad:** Must
**Dependencias:** necesita vehículos, celdas y pagos registrados. En la iteración 1 se cargan como datos de prueba.

**Criterios de aceptación**

```gherkin
Escenario: Entrada exitosa
  Dado un carro registrado con mensualidad vigente que no está dentro
  Y la celda C-010 de carro/camioneta está libre
  Cuando el operador registra la entrada de la placa en la celda C-010
  Entonces se guarda la entrada con la fecha y hora del servidor y el operador
  Y la celda C-010 queda ocupada

Escenario: Mensualidad no vigente
  Dado un vehículo registrado sin un pago que cubra la fecha actual
  Cuando el operador intenta registrar su entrada
  Entonces el sistema la rechaza con el mensaje "Mensualidad no vigente"

Escenario: Vehículo que salió con la mensualidad vencida intenta volver a entrar
  Dado un vehículo que salió con la mensualidad vencida y aún no ha pagado
  Cuando el operador intenta registrar su entrada
  Entonces el sistema la rechaza con el mensaje "Mensualidad no vigente"

Escenario: Vehículo ya dentro
  Dado un vehículo con una entrada abierta
  Cuando el operador intenta registrar otra entrada
  Entonces el sistema la rechaza con el mensaje "El vehículo ya se encuentra dentro"

Escenario: Placa no registrada
  Dada una placa que no existe en el sistema
  Cuando el operador intenta registrar su entrada
  Entonces el sistema la rechaza con el mensaje "Vehículo no registrado"

Escenario: Celda de tipo incorrecto
  Dada una moto con mensualidad vigente
  Cuando el operador intenta registrarla en una celda de carro/camioneta
  Entonces el sistema la rechaza con el mensaje "La celda no corresponde al tipo de vehículo"

Escenario: Celda ocupada
  Dada una celda ocupada por otro vehículo
  Cuando el operador intenta registrar una entrada en esa celda
  Entonces el sistema la rechaza con el mensaje "La celda está ocupada"

Escenario: Sin celdas disponibles
  Dado que todas las celdas de moto están ocupadas
  Cuando el operador intenta registrar la entrada de una moto
  Entonces el sistema la rechaza con el mensaje "No hay celdas disponibles para este tipo de vehículo"
```

---

## HU-002 — Registrar la salida de un vehículo

**Historia:** Como **operador**, quiero registrar la salida de un vehículo con su placa, para liberar su celda y dejar constancia de cuándo salió.

**Requerimientos:** RF-004
**Reglas:** RN-04, RN-05, RN-13
**Prioridad:** Must
**Dependencias:** HU-001

**Criterios de aceptación**

```gherkin
Escenario: Salida exitosa
  Dado un vehículo dentro en la celda C-010
  Cuando el operador registra su salida
  Entonces la entrada se cierra con la fecha y hora de salida y el operador
  Y la celda C-010 queda libre

Escenario: Salida con mensualidad vencida
  Dado un vehículo dentro cuya mensualidad ya venció
  Cuando el operador registra su salida
  Entonces el sistema la permite

Escenario: Estadía que cruza la medianoche
  Dado un vehículo que entró a las 23:30 de un día
  Cuando el operador registra su salida a las 06:00 del día siguiente
  Entonces la estadía queda registrada correctamente con ambas fechas

Escenario: Vehículo que no está dentro
  Dado un vehículo sin entrada abierta
  Cuando el operador intenta registrar su salida
  Entonces el sistema la rechaza con el mensaje "El vehículo no se encuentra dentro"
```

---

## HU-003 — Consultar ocupación y celdas

**Historia:** Como **operador**, quiero ver qué vehículos están dentro y consultar si una celda está ocupada, para saber dónde hay espacio y ubicar cada vehículo.

**Requerimientos:** RF-005
**Prioridad:** Must
**Dependencias:** HU-001, HU-002

**Criterios de aceptación**

```gherkin
Escenario: Lista de vehículos dentro
  Dados 3 vehículos con entrada abierta
  Cuando el operador consulta la ocupación
  Entonces ve exactamente esos 3 vehículos con placa, tipo, celda y hora de ingreso

Escenario: Filtro por tipo
  Dados vehículos dentro de tipo moto y carro
  Cuando el operador filtra por moto
  Entonces solo ve las motos

Escenario: Consultar una celda ocupada
  Dada la celda C-010 ocupada
  Cuando el operador la consulta
  Entonces ve la placa del vehículo y su hora de ingreso

Escenario: Consultar una celda libre
  Dada la celda M-005 libre
  Cuando el operador la consulta
  Entonces el sistema indica que está disponible
```

---

## HU-004 — Consultar el historial de movimientos

**Historia:** Como **administrador**, quiero consultar el historial de entradas y salidas por placa y por fechas, para revisar los movimientos ante cualquier reclamo o control.

**Requerimientos:** RF-006
**Prioridad:** Should
**Dependencias:** HU-001, HU-002

**Criterios de aceptación**

```gherkin
Escenario: Historial por rango de fechas
  Dados movimientos registrados en varios días
  Cuando el administrador consulta un rango de fechas
  Entonces ve solo los movimientos cuyo ingreso cae en ese rango

Escenario: Historial por placa
  Dada una placa con varios movimientos
  Cuando el administrador filtra por esa placa
  Entonces ve todos sus movimientos con celda, ingreso, salida y operadores
```

---

## HU-005 — Registrar una novedad

**Historia:** Como **operador**, quiero registrar una novedad ocurrida dentro del parqueadero, vinculada a uno o varios vehículos, para dejar documentado lo que pasó.

**Descripción:** El operador indica las placas involucradas, el tipo de novedad, la fecha y hora en que ocurrió y una descripción. La novedad recibe un identificador propio. No tiene estado ni adjuntos.

**Requerimientos:** RF-007
**Reglas:** RN-06, RN-07, RN-14, RN-15, RN-16, RN-18
**Prioridad:** Must
**Dependencias:** HU-001

**Criterios de aceptación**

```gherkin
Escenario: Novedad de un vehículo dentro
  Dada una moto dentro del parqueadero
  Cuando el operador registra una novedad de tipo "caída" con descripción y hora del hecho
  Entonces se guarda con un identificador, la fecha de registro, el operador y el vínculo a la moto y su estadía

Escenario: Novedad con dos vehículos
  Dados dos carros que estaban dentro a la hora del hecho
  Cuando el operador registra un "rayón" con las dos placas
  Entonces existe una sola novedad vinculada a ambos vehículos

Escenario: Novedad registrada después de la salida
  Dado un vehículo que ya salió
  Y la hora del hecho cae dentro de su última estadía
  Cuando el operador registra la novedad
  Entonces el sistema la acepta

Escenario: Un vehículo no estaba dentro
  Dada una novedad con dos placas en la que solo una estaba dentro a la hora del hecho
  Cuando el operador intenta registrarla
  Entonces el sistema la rechaza completa e indica qué placa no estaba dentro

Escenario: Datos incompletos
  Dada una novedad sin descripción o sin vehículos
  Cuando el operador intenta guardarla
  Entonces el sistema la rechaza

Escenario: Novedad inmutable
  Dada una novedad registrada
  Entonces no existen opciones para cambiar su estado ni para borrarla
```

---

## HU-006 — Consultar novedades

**Historia:** Como **administrador**, quiero consultar las novedades por placa, tipo y fechas, para atender reclamos con la información documentada.

**Requerimientos:** RF-008
**Prioridad:** Should
**Dependencias:** HU-005

**Criterios de aceptación**

```gherkin
Escenario: Novedades de un vehículo
  Dada una placa con varias novedades
  Cuando el administrador consulta por esa placa
  Entonces ve todas sus novedades, de la más reciente a la más antigua

Escenario: Novedad con varios vehículos
  Dada una novedad vinculada a dos placas
  Cuando se consulta por cualquiera de las dos
  Entonces la novedad aparece y muestra ambos vehículos
```

---

## HU-007 — Ver vehículos dentro con mensualidad vencida

**Historia:** Como **operador**, quiero ver qué vehículos siguen dentro con la mensualidad vencida y cuántos días llevan así, para estar al tanto del proceso de retiro.

**Requerimientos:** RF-009
**Reglas:** RN-11, RN-12, RN-17
**Prioridad:** Must
**Dependencias:** HU-001; datos de pagos de prueba

**Criterios de aceptación**

```gherkin
Escenario: Vehículo vencido aparece
  Dado un vehículo dentro cuya mensualidad venció hace 1 día
  Cuando el operador consulta la lista
  Entonces aparece con 1 día transcurrido y el estado del correo enviado

Escenario: Vehículo al día no aparece
  Dado un vehículo dentro con la mensualidad vigente
  Cuando el operador consulta la lista
  Entonces no aparece

Escenario: El propietario paga
  Dado un vehículo de la lista
  Cuando se registra el pago de su mensualidad
  Entonces deja de aparecer en la lista
```

---

## HU-008 — Avisar automáticamente al propietario por correo

**Historia:** Como **administrador**, quiero que el sistema envíe automáticamente un correo al propietario el día en que vence la mensualidad de un vehículo que está dentro, para que pague o retire el vehículo sin depender de que el personal lo recuerde.

**Requerimientos:** RF-010
**Reglas:** RN-11, RN-12
**Decisión:** DEC-002
**Prioridad:** Must
**Dependencias:** HU-007; correo del propietario en los datos de prueba; decisión de arquitectura sobre el servicio de correo y el proceso programado.

**Criterios de aceptación**

```gherkin
Escenario: Envío el día del vencimiento
  Dado un vehículo dentro cuya mensualidad vence hoy
  Cuando se ejecuta el proceso diario
  Entonces se envía un correo al propietario con la placa, la fecha de vencimiento, el aviso de pago y la advertencia de consecuencias
  Y el envío queda registrado como "enviado"

Escenario: Un solo correo
  Dado un vehículo al que ya se le envió el correo por este vencimiento
  Cuando el proceso diario vuelve a ejecutarse
  Entonces no se envía otro correo

Escenario: Fallo del servicio de correo
  Dado que el servicio de correo no responde
  Cuando se intenta el envío
  Entonces el envío queda registrado como "fallido" y es visible en la lista de HU-007
  Y el registro de entradas y salidas sigue funcionando

Escenario: Vehículo que ya salió
  Dado un vehículo que salió antes de ejecutarse el proceso
  Cuando se ejecuta el proceso diario
  Entonces no se le envía correo
```

---

## HU-009 — Controlar el plazo de 8 días y el contacto con autoridades

**Historia:** Como **administrador**, quiero ver qué vehículos siguen dentro 8 días o más después del vencimiento y registrar cuándo contacté a las autoridades, para cumplir el procedimiento de retiro y dejar constancia.

**Requerimientos:** RF-011
**Reglas:** RN-12, RN-17
**Prioridad:** Must
**Dependencias:** HU-007

**Criterios de aceptación**

```gherkin
Escenario: Plazo vencido
  Dado un vehículo dentro cuya mensualidad venció el día 1
  Cuando el administrador consulta la lista el día 9
  Entonces aparece marcado como "Plazo vencido – contactar autoridades"

Escenario: Antes del plazo
  Dado un vehículo dentro cuya mensualidad venció el día 1
  Cuando el administrador consulta la lista el día 8
  Entonces no aparece marcado como plazo vencido

Escenario: El operador no puede registrar el contacto
  Dado un vehículo con el plazo vencido
  Cuando un operador intenta registrar el contacto con las autoridades
  Entonces el sistema lo rechaza con "acceso denegado"

Escenario: Registrar contacto con autoridades
  Dado un vehículo con el plazo vencido
  Cuando el administrador registra el contacto con las autoridades y una observación
  Entonces queda guardado con fecha, usuario y observación
```

---

## HU-010 — Crear y desactivar operadores

> La historia se agrega por DEC-011. **Aprobada** por el equipo el 2026-11-15.

**Historia:** Como **administrador**, quiero crear cuentas de operador y desactivarlas cuando ya no trabajen, para controlar quién puede usar el sistema.

**Requerimientos:** RF-106 (versión básica)
**Reglas:** RN-07, RNF-001, RNF-002
**Prioridad:** Must
**Dependencias:** inicio de sesión y roles (RNF-001, RNF-002)

**Criterios de aceptación**

```gherkin
Escenario: Crear operador
  Dado que el administrador inició sesión
  Cuando crea un operador con nombre, usuario "operador2" y contraseña
  Entonces el operador aparece activo en la lista
  Y puede iniciar sesión con esas credenciales

Escenario: Usuario repetido
  Dado que ya existe el usuario "operador2"
  Cuando el administrador intenta crear otro con el mismo usuario
  Entonces el sistema lo rechaza con "El nombre de usuario ya existe"

Escenario: Desactivar operador
  Dado un operador activo
  Cuando el administrador lo desactiva
  Entonces el operador no puede iniciar sesión
  Y su cuenta y sus registros anteriores se conservan

Escenario: Un operador no puede crear operadores
  Dado que un operador inició sesión
  Cuando intenta acceder a la creación de operadores
  Entonces el sistema responde "acceso denegado"
```

---

## HU-011 — Enviar el correo de retiro desde un botón (simulado)

> La historia se agrega por DEC-007. **Aprobada** por el equipo el 2026-11-15, con el criterio de reenvío resuelto en P-20 (un solo reenvío, aclarado el mismo día).

**Historia:** Como **operador**, quiero un botón para enviar el correo de retiro a un propietario con la mensualidad vencida, para avisarle en el momento y mostrar el funcionamiento en la demostración.

**Requerimientos:** RF-012 (y RF-010, simulado)
**Prioridad:** Should
**Dependencias:** HU-007

**Criterios de aceptación**

```gherkin
Escenario: Envío manual simulado
  Dado un vehículo en la lista de mensualidades vencidas
  Cuando el operador pulsa "Enviar correo"
  Entonces el sistema muestra "Correo enviado (simulación)" con el texto del mensaje
  Y registra el envío con origen "manual", el operador y la fecha y hora
  Y no se contacta ningún servidor de correo real

Escenario: Reenvío con confirmación
  Dado un vehículo al que ya se le registró el correo de este vencimiento
  Cuando el operador pulsa "Enviar correo"
  Entonces el sistema pregunta "Ya se envió un correo para este vencimiento. ¿Desea reenviarlo?"
  Y si el operador confirma, se registra un reenvío simulado

Escenario: Solo un reenvío
  Dado un vehículo al que ya se le reenvió una vez el correo de este vencimiento
  Cuando el operador pulsa "Enviar correo"
  Entonces el sistema no lo reenvía e informa "El correo de este vencimiento ya se reenvió una vez"
```

**Nota sobre HU-008 (aprobada):** con DEC-007, el "envío" automático de HU-008 también es simulado. Los escenarios de HU-008 no cambian; "se envía un correo" significa "se registra y se muestra un envío simulado".

---

## Matriz de trazabilidad RF → HU

| RF | HU |
|---|---|
| RF-001 Registrar entrada | HU-001 |
| RF-002 Verificar mensualidad | HU-001 |
| RF-003 Asignar celda | HU-001 |
| RF-004 Registrar salida | HU-002 |
| RF-005 Consultar vehículos dentro y celdas | HU-003 |
| RF-006 Historial de movimientos | HU-004 |
| RF-007 Registrar novedad | HU-005 |
| RF-008 Consultar novedades | HU-006 |
| RF-009 Vehículos dentro con mensualidad vencida | HU-007 |
| RF-010 Correo automático | HU-008 |
| RF-011 Plazo de 8 días y autoridades | HU-009 |
| RF-106 Gestionar operadores (básico, DEC-011) | HU-010 |
| RF-012 Botón "Enviar correo" (simulado, DEC-007) | HU-011 |

Los 11 RF de la iteración 1 tienen al menos una historia, y todas las historias salen de RF aprobados.

## Puntos revisados (2026-11-15)

1. **Plazo de 8 días.** Confirmado por el equipo: el vehículo se marca cuando hoy ≥ fecha de vencimiento + 8 días. Ejemplo: si vence el día 1, se marca el día 9.
2. **Contacto con autoridades.** Confirmado por el equipo: solo el **administrador** lo registra.
