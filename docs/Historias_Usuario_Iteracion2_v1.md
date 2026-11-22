# Historias de usuario — Iteración 2: Gestión de usuarios y gestión de celdas

**Proyecto:** Parqueadero "Autos Colombia"
**Versión:** 1.2
**Fecha:** 2026-11-15
**Base:** Requerimientos de la iteración 2 v1.3 (aprobados el 2026-11-15) y DEC-013 a DEC-015.
**Estado:** **Aprobado** por el equipo del proyecto el 2026-11-15. Versión 1.2 por la solicitud de cambio CHG-003, aprobada el 2026-11-22.

| Versión | Cambios |
|---|---|
| 1 | Borrador inicial. |
| 1.1 | Respuestas a los 3 puntos de revisión: se rechazan las franjas que se cruzan; el encabezado muestra las horas del turno, sin nombre; nuevo escenario de registro en curso sin actividad (RN-35). |
| 1.2 | **CHG-003:** historias nuevas HU-033 a HU-036 (gestión de celdas por el administrador); HU-018 sin el escenario "Las celdas son fijas" y con las celdas inactivas. |

La numeración continúa la de la iteración 1 (HU-001 a HU-011).

## Resumen

| ID | Título | Actor | RF | Prioridad |
|---|---|---|---|---|
| HU-012 | Registrar un propietario | Operador | RF-101 | Must |
| HU-013 | Registrar un vehículo | Operador | RF-102 | Must |
| HU-014 | Buscar y consultar propietarios y vehículos | Operador | RF-108 | Must |
| HU-015 | Modificar, activar e inactivar propietarios y vehículos | Operador | RF-105 | Must |
| HU-016 | Solicitar un cambio de propietario | Operador | RF-109 | Must |
| HU-017 | Aprobar o rechazar un cambio de propietario | Administrador | RF-109 | Must |
| HU-018 | Consultar el mapa de celdas | Operador | RF-104 | Must |
| HU-019 | Editar operadores y restablecer contraseñas | Administrador | RF-106 | Must |
| HU-020 | Asignar horarios a los operadores | Administrador | RF-107 | Must |
| HU-021 | Trabajar solo dentro de mi turno | Operador | RF-107 | Must |
| HU-022 | Autorizar un ingreso fuera de turno | Administrador | RF-110 | Must |
| HU-023 | Consultar la bitácora de operaciones | Administrador | RF-111 | Must |
| HU-033 | Crear una celda | Administrador | RF-103 | Must |
| HU-034 | Consultar y cambiar el tipo de las celdas | Administrador | RF-103 | Must |
| HU-035 | Inactivar y reactivar una celda | Administrador | RF-103 | Must |
| HU-036 | Eliminar una celda que nunca se usó | Administrador | RF-103 | Must |

---

## HU-012 — Registrar un propietario

**Historia:** Como **operador**, quiero registrar a un nuevo cliente mensualista con sus datos de contacto, para poder asociarle sus vehículos y avisarle cuando su mensualidad venza.

**Requerimientos:** RF-101 · **Reglas:** RN-25, RN-30, RN-34, DEC-002 · **Prioridad:** Must

```gherkin
Escenario: Registro correcto
  Dado que el operador inició sesión
  Cuando registra a "Laura Méndez", cédula "1023456789", celular "3001234567", correo "laura@correo.co" y dirección "Calle 10 # 20-30"
  Entonces el propietario queda registrado y activo
  Y la bitácora muestra que el operador lo registró

Escenario: Cédula repetida
  Dado que ya existe un propietario con la cédula "1023456789"
  Cuando el operador intenta registrar otro con esa cédula
  Entonces el sistema lo rechaza con "Ya existe un propietario con esa cédula"

Escenario: Celular inválido
  Cuando el operador registra un celular "6012345678"
  Entonces el sistema lo rechaza con "El celular debe tener 10 dígitos y empezar por 3"

Escenario: Datos incompletos o correo inválido
  Cuando el operador deja vacío algún campo o escribe un correo sin formato válido
  Entonces el sistema no guarda e indica el campo con error
```

## HU-013 — Registrar un vehículo

**Historia:** Como **operador**, quiero registrar un vehículo y asociarlo a su propietario, para que el sistema lo reconozca en la portería.

**Requerimientos:** RF-102 · **Reglas:** RN-02, RN-23, RN-25, RN-34 · **Prioridad:** Must

```gherkin
Escenario: Registro correcto
  Dado un propietario activo con cédula "1023456789"
  Cuando el operador registra la placa "jtr 625", tipo Carro, marca "Mazda", nombre "3", modelo 2021, color "Blanco" para ese propietario
  Entonces el vehículo queda registrado con la placa "JTR625" y activo
  Y aparece en la ficha del propietario

Escenario: Placa que no corresponde al tipo
  Cuando el operador registra la placa "ABC123" con tipo Moto
  Entonces el sistema lo rechaza con "La placa no corresponde al tipo de vehículo"

Escenario: Placa repetida
  Dado que existe un vehículo con placa "JTR625"
  Cuando el operador intenta registrar otro con esa placa
  Entonces el sistema lo rechaza con "Ya existe un vehículo con esa placa"

Escenario: Propietario inactivo
  Dado un propietario inactivo
  Cuando el operador intenta asociarle un vehículo nuevo
  Entonces el sistema lo rechaza con "El propietario está inactivo"

Escenario: Modelo fuera de rango
  Cuando el operador registra el modelo 1940
  Entonces el sistema lo rechaza indicando el rango permitido
```

## HU-014 — Buscar y consultar propietarios y vehículos

**Historia:** Como **operador**, quiero buscar un propietario por nombre o cédula, o un vehículo por placa, y ver su ficha, para atender consultas y corregir datos.

**Requerimientos:** RF-108 · **Reglas:** DEC-013, DEC-015 · **Prioridad:** Must

```gherkin
Escenario: Búsqueda por cédula, nombre o placa
  Dados propietarios y vehículos registrados
  Cuando el operador busca "1023456789", "Méndez" o "JTR625"
  Entonces ve los resultados que coinciden

Escenario: Ficha del propietario
  Cuando el operador abre la ficha de "Laura Méndez"
  Entonces ve sus datos, su estado (activo o inactivo) y la lista de sus vehículos
  Y para cada vehículo ve si está dentro o fuera y su estado

Escenario: Ficha del vehículo
  Cuando el operador abre la ficha de "JTR625"
  Entonces ve sus datos, su propietario actual, el historial de propietarios anteriores
  Y la bitácora de las operaciones sobre ese vehículo, con el usuario y la fecha de cada una

Escenario: Sin resultados
  Cuando el operador busca "ZZZ999"
  Entonces el sistema indica que no se encontraron resultados
```

## HU-015 — Modificar, activar e inactivar propietarios y vehículos

**Historia:** Como **operador**, quiero corregir datos y activar o inactivar propietarios y vehículos, para mantener la información al día sin borrar nada.

**Requerimientos:** RF-105 · **Reglas:** RN-07, RN-24, RN-26, RN-29, RN-34 · **Prioridad:** Must

```gherkin
Escenario: Modificar datos del propietario
  Cuando el operador cambia el celular de "Laura Méndez"
  Entonces el cambio se guarda
  Y la bitácora registra el valor anterior, el nuevo, el operador y la fecha

Escenario: La placa no se puede editar
  Cuando el operador abre la edición de un vehículo
  Entonces la placa se muestra pero no se puede modificar

Escenario: Placa mal escrita
  Dado un vehículo registrado con una placa equivocada
  Cuando el operador lo inactiva y registra uno nuevo con la placa correcta
  Entonces ambos registros quedan, el primero inactivo

Escenario: Inactivar un propietario con un vehículo dentro
  Dado un propietario con un vehículo dentro del parqueadero
  Cuando el operador lo inactiva
  Entonces el vehículo puede registrar su salida
  Pero no puede volver a entrar mientras el propietario siga inactivo

Escenario: Reactivar
  Dado un vehículo inactivo
  Cuando el operador lo activa
  Entonces puede volver a entrar si su mensualidad está vigente
```

## HU-016 — Solicitar un cambio de propietario

**Historia:** Como **operador**, quiero solicitar al administrador que un vehículo pase a otro propietario, para registrar una venta sin perder el historial.

**Requerimientos:** RF-109 · **Reglas:** RN-33, DEC-015 · **Prioridad:** Must

```gherkin
Escenario: Solicitud creada
  Dado el vehículo "JTR625" de "Laura Méndez" y el propietario registrado "Andrés Gómez"
  Cuando el operador solicita el cambio a "Andrés Gómez" con el motivo "Venta del vehículo"
  Entonces la solicitud queda pendiente
  Y el vehículo sigue a nombre de "Laura Méndez" hasta que el administrador la resuelva

Escenario: Solo una solicitud pendiente por vehículo
  Dada una solicitud pendiente para "JTR625"
  Cuando el operador intenta crear otra
  Entonces el sistema lo rechaza con "Ya hay una solicitud pendiente para este vehículo"

Escenario: El nuevo propietario debe ser distinto y estar activo
  Cuando el operador elige al mismo propietario actual o a uno inactivo
  Entonces el sistema rechaza la solicitud
```

## HU-017 — Aprobar o rechazar un cambio de propietario

**Historia:** Como **administrador**, quiero revisar las solicitudes de cambio de propietario y aprobarlas o rechazarlas, para controlar los cambios de información.

**Requerimientos:** RF-109 · **Reglas:** RN-33, DEC-015 · **Prioridad:** Must

```gherkin
Escenario: Aprobar
  Dada una solicitud pendiente de "JTR625" de "Laura Méndez" a "Andrés Gómez"
  Cuando el administrador la aprueba
  Entonces el vehículo pasa a "Andrés Gómez"
  Y el historial muestra que "Laura Méndez" fue propietaria desde su registro hasta hoy
  Y los pagos y estadías anteriores siguen asociados al vehículo

Escenario: Rechazar
  Cuando el administrador rechaza la solicitud con una observación
  Entonces el vehículo no cambia de propietario y la solicitud queda rechazada con la observación

Escenario: Solo el administrador resuelve
  Cuando un operador intenta aprobar una solicitud
  Entonces el sistema responde "acceso denegado"
```

## HU-018 — Consultar el mapa de celdas

**Historia:** Como **operador**, quiero ver todas las celdas de cada zona con su estado, para saber de un vistazo dónde hay espacio.

**Requerimientos:** RF-104 · **Reglas:** RN-08, RN-20, RN-51 · **Prioridad:** Must

```gherkin
Escenario: Mapa por zonas
  Cuando el operador abre el mapa de celdas
  Entonces ve la zona A (celdas de carro/camioneta) y la zona M (celdas de moto) con el inventario actual
  Y cada celda aparece como libre u ocupada, con la placa del vehículo si está ocupada
  Y ve los contadores de libres y ocupadas por zona

Escenario: Celdas inactivas en el mapa
  Dado que la celda "A-010" está inactiva por "Mantenimiento"
  Cuando el operador abre el mapa de la zona A
  Entonces "A-010" aparece marcada como inactiva y no cuenta como libre
```

## HU-019 — Editar operadores y restablecer contraseñas

**Historia:** Como **administrador**, quiero editar el nombre de un operador y restablecer su contraseña, para mantener sus cuentas al día.

**Requerimientos:** RF-106 · **Reglas:** RNF-001, RN-34 · **Prioridad:** Must

```gherkin
Escenario: Editar el nombre
  Cuando el administrador cambia el nombre de "operador2" a "Julián Andrés Torres"
  Entonces el cambio se guarda y queda en la bitácora

Escenario: Restablecer la contraseña
  Cuando el administrador asigna una contraseña nueva válida a "operador2"
  Entonces el operador inicia sesión con la nueva contraseña y la anterior deja de funcionar
  Y la bitácora registra el restablecimiento, sin guardar la contraseña

Escenario: Contraseña débil
  Cuando el administrador asigna "123"
  Entonces el sistema la rechaza indicando los requisitos
```

## HU-020 — Asignar horarios a los operadores

**Historia:** Como **administrador**, quiero asignar a cada operador sus franjas de trabajo por día, para controlar cuándo puede usar el sistema.

**Requerimientos:** RF-107 · **Reglas:** RN-31, RN-36, DEC-014 · **Prioridad:** Must

```gherkin
Escenario: Franja diurna
  Cuando el administrador asigna a "operador" el lunes de 06:00 a 14:00
  Entonces la franja queda guardada y aparece en el horario del operador

Escenario: Turno nocturno
  Cuando el administrador asigna el viernes de 22:00 a 06:00
  Entonces la franja se acepta y cubre hasta las 06:00 del sábado

Escenario: Varias franjas el mismo día
  Cuando el administrador asigna el martes de 06:00 a 10:00 y de 16:00 a 20:00
  Entonces ambas franjas quedan guardadas

Escenario: Franjas que se solapan
  Cuando el administrador asigna dos franjas del mismo día que se solapan
  Entonces el sistema lo rechaza con "La franja se cruza con otra del mismo día"

Escenario: Eliminar una franja
  Cuando el administrador quita una franja
  Entonces deja de aplicarse y la bitácora lo registra
```

> **Nota:** quitar una franja **no** borra datos de operación (RN-07 se refiere a entradas, salidas, novedades y registros); el horario es configuración. La bitácora conserva el cambio.

## HU-021 — Trabajar solo dentro de mi turno

**Historia:** Como **operador**, quiero que el sistema me deje trabajar durante mi turno y me avise cuando termine, para no perder un registro a medias.

**Requerimientos:** RF-107 · **Reglas:** RN-31, RN-35, RN-36 · **Prioridad:** Must

```gherkin
Escenario: Ingreso dentro del turno
  Dado que el turno del operador es hoy de 06:00 a 14:00
  Cuando inicia sesión a las 08:00
  Entonces ingresa y el encabezado muestra "Operador · Turno 06:00 – 14:00"

Escenario: Ingreso fuera del turno
  Cuando inicia sesión a las 15:00 sin autorización vigente
  Entonces el sistema lo rechaza con "Estás fuera de tu turno. Solicita autorización al administrador"

Escenario: Operador sin horario
  Dado un operador sin franjas asignadas
  Cuando intenta iniciar sesión
  Entonces el sistema lo rechaza indicando que no tiene horario asignado

Escenario: Fin del turno sin un registro en curso
  Dado que el turno termina a las 14:00 y el operador está en una consulta
  Cuando son las 14:00
  Entonces ve el aviso "Tu turno terminó. La sesión se cerrará a las 14:05"
  Y a las 14:05 la sesión se cierra automáticamente

Escenario: Fin del turno con un registro en curso y actividad
  Dado que a las 14:03 el operador está llenando el registro de un propietario
  Y sigue escribiendo
  Cuando pasan las 14:05
  Entonces la sesión no se cierra
  Y cuando guarda o cancela el registro, la sesión se cierra

Escenario: Registro en curso sin actividad
  Dado que terminó el turno y el operador tiene un registro empezado
  Cuando pasan 5 minutos sin que escriba nada
  Entonces el sistema muestra el aviso "La sesión se cerrará en 5 minutos"
  Y si en esos 5 minutos no escribe nada, la sesión se cierra automáticamente
  Pero si vuelve a escribir, el aviso desaparece y puede terminar el registro

Escenario: El administrador no tiene restricción de horario
  Cuando el administrador inicia sesión a cualquier hora
  Entonces ingresa
```

## HU-022 — Autorizar un ingreso fuera de turno

**Historia:** Como **administrador**, quiero autorizar a un operador a trabajar fuera de su turno por un tiempo definido, para cubrir ausencias o turnos extra.

**Requerimientos:** RF-110 · **Reglas:** RN-32, RN-35, DEC-014 · **Prioridad:** Must

```gherkin
Escenario: Autorización vigente
  Cuando el administrador autoriza a "operador2" hoy de 15:00 a 19:00 con el motivo "Cubre ausencia"
  Entonces "operador2" puede iniciar sesión entre las 15:00 y las 19:00
  Y la bitácora registra quién autorizó, el motivo y la vigencia

Escenario: Autorización vencida
  Dado que la autorización terminó a las 19:00
  Cuando "operador2" intenta iniciar sesión a las 19:30 fuera de su turno
  Entonces el sistema lo rechaza

Escenario: La autorización termina con la sesión abierta
  Cuando termina la vigencia de la autorización
  Entonces se aplica la misma regla de cierre que al terminar un turno (RN-35)

Escenario: Solo el administrador autoriza
  Cuando un operador intenta crear una autorización
  Entonces el sistema responde "acceso denegado"
```

## HU-023 — Consultar la bitácora de operaciones

**Historia:** Como **administrador**, quiero consultar qué operador hizo cada operación, para auditar el uso del sistema.

**Requerimientos:** RF-111 · **Reglas:** RN-34, DEC-013 · **Prioridad:** Must

```gherkin
Escenario: Bitácora completa con filtros
  Cuando el administrador filtra la bitácora por el usuario "operador" y la fecha de hoy
  Entonces ve cada operación con la fecha y hora, el usuario, la acción, la entidad y el detalle de los cambios

Escenario: Operaciones incluidas
  Entonces la bitácora incluye registrar, modificar, activar e inactivar propietarios y vehículos
  Y solicitudes y resoluciones de cambio de propietario, cambios de operadores, horarios y autorizaciones

Escenario: El operador solo ve la bitácora en las fichas
  Cuando un operador intenta abrir la bitácora completa
  Entonces el sistema responde "acceso denegado"
  Pero en la ficha de un vehículo o propietario ve las operaciones sobre ese registro
```

---

## HU-033 — Crear una celda

**Historia:** Como **administrador**, quiero crear celdas nuevas indicando su tipo, para ampliar el inventario del parqueadero.

**Requerimientos:** RF-103 · **Reglas:** RN-48, RN-49, RN-53 · **Prioridad:** Must

```gherkin
Escenario: Crear una celda con el código sugerido
  Dado que la última celda de carro/camioneta es "A-150"
  Cuando el administrador elige el tipo carro/camioneta
  Entonces el sistema sugiere el código "A-151"
  Y al guardar, la celda "A-151" queda activa y libre
  Y la bitácora muestra que el administrador la creó

Escenario: Código repetido
  Dado que ya existe la celda "M-05"
  Cuando el administrador intenta crear otra celda "m-05"
  Entonces el sistema la rechaza con "Ya existe una celda con el código M-05"

Escenario: Código con formato inválido
  Cuando el administrador crea una celda de moto con el código "A-200" o "M-5"
  Entonces el sistema la rechaza con "El código de una celda de moto debe tener el formato M-01 a M-99"

Escenario: Solo el administrador
  Cuando un operador intenta abrir la gestión de celdas
  Entonces el sistema responde "acceso denegado"
```

## HU-034 — Consultar y cambiar el tipo de las celdas

**Historia:** Como **administrador**, quiero ver todas las celdas con su estado y corregir el tipo de una celda nueva, para mantener el inventario al día.

**Requerimientos:** RF-103 · **Reglas:** RN-49, RN-50, RN-52, RN-53 · **Prioridad:** Must

```gherkin
Escenario: Lista de celdas
  Cuando el administrador abre "Celdas"
  Entonces ve cada celda con su código, tipo y estado (libre, ocupada con la placa, o inactiva con el motivo)
  Y puede filtrar por tipo y estado y buscar por código

Escenario: Cambiar el tipo de una celda nueva
  Dado que la celda "A-151" nunca se ha usado y está libre
  Cuando el administrador la cambia a moto
  Entonces el sistema le pide un código de moto, por ejemplo "M-51"
  Y la celda queda como "M-51" de moto
  Y la bitácora registra el tipo y el código anteriores y los nuevos

Escenario: Celda ocupada
  Dado que la celda "A-003" tiene un vehículo dentro
  Cuando el administrador intenta cambiar su tipo
  Entonces el sistema lo rechaza con "La celda está ocupada"

Escenario: Celda con historial
  Dado que la celda "A-004" ya tuvo estadías
  Cuando el administrador intenta cambiar su tipo
  Entonces el sistema lo rechaza con "La celda ya se usó; inactívala y crea una nueva"
```

## HU-035 — Inactivar y reactivar una celda

**Historia:** Como **administrador**, quiero sacar de servicio una celda (por ejemplo, por mantenimiento) y volver a habilitarla, para que no se asigne mientras no se pueda usar.

**Requerimientos:** RF-103, RF-104 · **Reglas:** RN-50, RN-51, RN-53 · **Prioridad:** Must

```gherkin
Escenario: Inactivar con motivo
  Dado que la celda "A-010" está libre
  Cuando el administrador la inactiva con el motivo "Mantenimiento"
  Entonces la celda queda inactiva con ese motivo
  Y al registrar una entrada, "A-010" no se ofrece

Escenario: Motivo obligatorio
  Cuando el administrador intenta inactivar una celda sin motivo
  Entonces el sistema no guarda e indica el campo con error

Escenario: Celda ocupada
  Dado que la celda "A-003" tiene un vehículo dentro
  Cuando el administrador intenta inactivarla
  Entonces el sistema lo rechaza con "La celda está ocupada"

Escenario: Reactivar
  Dado que la celda "A-010" está inactiva
  Cuando el administrador la reactiva
  Entonces vuelve a estar disponible para las entradas
```

## HU-036 — Eliminar una celda que nunca se usó

**Historia:** Como **administrador**, quiero eliminar una celda creada por error, sin perder el historial de las celdas que sí se usaron.

**Requerimientos:** RF-103 · **Reglas:** RN-07, RN-52, RN-53 · **Prioridad:** Must

```gherkin
Escenario: Eliminar una celda sin historial
  Dado que la celda "A-151" nunca se ha usado
  Cuando el administrador la elimina y confirma
  Entonces la celda deja de existir
  Y la bitácora registra la eliminación

Escenario: Celda con historial
  Dado que la celda "A-004" ya tuvo estadías
  Cuando el administrador intenta eliminarla
  Entonces el sistema lo rechaza con "La celda tiene historial; solo se puede inactivar"
```

---

## Matriz de trazabilidad RF → HU (iteración 2)

| RF | HU |
|---|---|
| RF-101 Registrar propietario | HU-012 |
| RF-102 Registrar vehículo | HU-013 |
| RF-103 Gestionar celdas (CHG-003) | HU-033 a HU-036 |
| RF-104 Mapa de celdas | HU-018, HU-035 |
| RF-105 Modificar, activar e inactivar | HU-015 |
| RF-106 Gestionar operadores (completar) | HU-019 |
| RF-107 Horarios de operador | HU-020, HU-021 |
| RF-108 Consultar propietarios y vehículos | HU-014 |
| RF-109 Cambio de propietario | HU-016, HU-017 |
| RF-110 Autorización fuera de turno | HU-022 |
| RF-111 Bitácora | HU-023 |

Los 11 RF de la iteración 2 tienen al menos una historia. RF-103 se incorporó con la solicitud de cambio CHG-003.

## Puntos revisados (2026-11-15)

1. **HU-020:** confirmado por el equipo: las franjas del mismo día que se cruzan **se rechazan**.
2. **HU-021:** confirmado por el equipo: **no** se muestra un nombre de turno, solo **las horas** que debe trabajar (por ejemplo, "Turno 06:00 – 14:00").
3. **HU-021:** aclarado por el equipo: con un registro en curso, la sesión sigue abierta mientras el operador escriba. Si pasan **5 minutos sin que escriba nada**, empiezan **otros 5 minutos** de aviso, y después la sesión se cierra (RN-35, requerimientos v1.4).
