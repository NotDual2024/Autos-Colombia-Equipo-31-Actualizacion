# Requerimientos — Parqueadero "Autos Colombia"

**Versión:** 1 (borrador)
**Fecha:** 2026-11-15
**Estado:** Pendiente de aprobación. Ningún requerimiento de este documento está aprobado.

## 0. Convenciones

### Origen de cada elemento

| Etiqueta | Significado |
|---|---|
| **[E]** | Está en el enunciado. |
| **[U]** | Lo indicó el equipo en la conversación. |
| **[I]** | Lo infiere el arquitecto. Hay que confirmarlo. |
| **[S]** | Supuesto provisional. No es una decisión. |

### Identificadores

Los identificadores van por módulo para que no cambien cuando se agreguen requerimientos:

| Módulo | Rango RF | Nivel de detalle en esta versión |
|---|---|---|
| 1. Entrada y salida de vehículos (incluye novedades) | RF-001 a RF-099 | Completo |
| 2. Gestión de usuarios y celdas | RF-101 a RF-199 | Solo identificados (se detallan en su iteración) |
| 3. Gestión de pagos | RF-201 a RF-299 | Solo identificados (se detallan en su iteración) |

Los RF de los módulos 2 y 3 se identifican desde ahora porque DEC-001 pide diseñar el modelo de datos completo desde el inicio.

### Prioridad (MoSCoW)

- **Must:** sin esto el sistema no cumple su propósito.
- **Should:** es importante, pero el sistema puede operar sin él de forma temporal.
- **Could:** es deseable si alcanza el tiempo.
- **Won't (por ahora):** queda fuera de esta versión.

---

## 1. Actores

| Actor | Descripción | Origen |
|---|---|---|
| Operador | Persona en la portería que registra entradas, salidas y novedades. | [S] Pendiente P-01 |
| Administrador | Gestiona clientes, vehículos, celdas, pagos y usuarios del sistema. | [S] Pendiente P-01 |
| Cliente (mensualista) | Dueño del vehículo que paga la mensualidad. No usa el sistema directamente. | [S] Pendiente P-01 |

---

## 2. Reglas de negocio

| ID | Regla | Origen |
|---|---|---|
| RN-01 | El servicio se presta solo por mensualidad. No hay cobro por horas ni por fracción. | [E][U] |
| RN-02 | Los tipos de vehículo admitidos son moto, carro y camioneta. | [U] |
| RN-03 | Solo pueden estar dentro del parqueadero los vehículos que tienen la mensualidad pagada y vigente. | [U] |
| RN-04 | Un vehículo no puede tener más de una entrada abierta (sin salida) al mismo tiempo. | [I] |
| RN-05 | Una celda no puede estar ocupada por más de un vehículo al mismo tiempo. | [I] |
| RN-06 | Una novedad se asocia siempre a un vehículo concreto y queda con fecha, hora y el usuario que la registró. | [E][U][I] |
| RN-07 | Los registros de entradas, salidas y novedades no se eliminan. | [I] Recomendado para trazabilidad |
| RN-08 | Compatibilidad entre celda y tipo de vehículo. | Pendiente P-03 |
| RN-09 | Asignación de celda: fija por mensualidad o libre al ingresar. | Pendiente P-02 |

---

## 3. Requerimientos funcionales

### 3.1. Módulo 1 — Entrada y salida de vehículos

#### RF-001 — Registrar entrada de vehículo

| Campo | Detalle |
|---|---|
| Descripción | El sistema registra el ingreso de un vehículo al parqueadero. |
| Actor | Operador |
| Entradas | Placa del vehículo. La celda solo se pide si la asignación es libre (P-02). |
| Proceso | 1. Busca el vehículo por placa. 2. Comprueba que tenga mensualidad vigente (RF-002). 3. Comprueba que no tenga una entrada abierta. 4. Determina la celda (RF-003). 5. Registra la entrada con la fecha y hora del sistema y el operador. 6. Marca la celda como ocupada. |
| Salidas | Confirmación con placa, celda y hora de ingreso. |
| Reglas | RN-03, RN-04, RN-05, RN-08, RN-09 |
| Prioridad | Must |
| Dependencias | RF-002, RF-003, RF-102 (registro de vehículos) |
| Origen | [E] |

**Criterios de aceptación**

- Dado un vehículo registrado, con mensualidad vigente y sin entrada abierta, cuando el operador registra su placa, entonces el sistema guarda la entrada con fecha, hora y operador, y la celda queda ocupada.
- Dado un vehículo que ya tiene una entrada abierta, cuando el operador intenta registrar otra entrada, entonces el sistema la rechaza e informa el motivo.
- Dada una placa que no está registrada, cuando el operador intenta registrar la entrada, entonces el sistema la rechaza e indica que el vehículo no existe.

#### RF-002 — Verificar vigencia de la mensualidad al ingresar

| Campo | Detalle |
|---|---|
| Descripción | Antes de autorizar una entrada, el sistema comprueba que el vehículo tenga una mensualidad pagada que cubra la fecha actual. |
| Actor | Sistema (lo dispara RF-001) |
| Entradas | Vehículo y fecha actual. |
| Proceso | Consulta el estado de la mensualidad (RF-202). |
| Salidas | Ingreso autorizado, o rechazado con el motivo. |
| Reglas | RN-03 |
| Prioridad | Must |
| Dependencias | RF-201, RF-202 |
| Origen | [U] |

**Criterios de aceptación**

- Dado un vehículo con la mensualidad vencida o sin pagos, cuando se intenta registrar su entrada, entonces el sistema la rechaza con el mensaje "Mensualidad no vigente".
- Dado un vehículo cuya mensualidad cubre la fecha actual, cuando se intenta registrar su entrada, entonces el sistema la autoriza.

> **Pendiente P-04:** falta definir qué pasa si la mensualidad vence mientras el vehículo está dentro.

#### RF-003 — Determinar la celda del vehículo al ingresar

| Campo | Detalle |
|---|---|
| Descripción | El sistema determina en qué celda queda el vehículo. |
| Actor | Operador y sistema |
| Entradas | Vehículo y celda elegida (si aplica). |
| Proceso | **Opción fija:** usa la celda asignada a la mensualidad del vehículo. **Opción libre:** el operador elige una celda disponible y compatible. La opción depende de P-02. |
| Salidas | Celda asignada a la entrada. |
| Reglas | RN-05, RN-08, RN-09 |
| Prioridad | Must |
| Dependencias | RF-103 (registro de celdas) |
| Origen | [E] "manejar las celdas" + [I] |

**Criterios de aceptación**

- Dada una celda ocupada, cuando se intenta asignarla a otro vehículo, entonces el sistema lo impide.
- Dada una celda no compatible con el tipo de vehículo (si se aprueba RN-08), cuando se intenta asignarla, entonces el sistema lo impide.

#### RF-004 — Registrar salida de vehículo

| Campo | Detalle |
|---|---|
| Descripción | El sistema registra la salida de un vehículo que está dentro del parqueadero. |
| Actor | Operador |
| Entradas | Placa del vehículo. |
| Proceso | 1. Busca la entrada abierta del vehículo. 2. Registra la fecha y hora de salida y el operador. 3. Libera la celda. |
| Salidas | Confirmación con placa, hora de ingreso, hora de salida y celda liberada. |
| Reglas | RN-04, RN-05 |
| Prioridad | Must |
| Dependencias | RF-001 |
| Origen | [E] |

**Criterios de aceptación**

- Dado un vehículo con una entrada abierta, cuando el operador registra su salida, entonces el sistema cierra la entrada con fecha, hora y operador, y la celda queda disponible.
- Dado un vehículo sin entrada abierta, cuando se intenta registrar su salida, entonces el sistema la rechaza e informa que el vehículo no está dentro.

#### RF-005 — Consultar vehículos dentro del parqueadero

| Campo | Detalle |
|---|---|
| Descripción | El sistema muestra los vehículos que están dentro en este momento, con celda y hora de ingreso. |
| Actor | Operador, Administrador |
| Entradas | Ninguna, o filtro por tipo de vehículo. |
| Salidas | Lista de placa, tipo, celda y hora de ingreso. |
| Prioridad | Should |
| Dependencias | RF-001, RF-004 |
| Origen | [I] Necesario para operar la portería y las celdas |

**Criterios de aceptación**

- Dados N vehículos con entrada abierta, cuando el operador consulta la ocupación, entonces el sistema muestra exactamente esos N vehículos.

#### RF-006 — Consultar historial de entradas y salidas

| Campo | Detalle |
|---|---|
| Descripción | El sistema permite consultar los movimientos registrados, filtrando por placa y por rango de fechas. |
| Actor | Administrador (y Operador, si se aprueba) |
| Entradas | Placa (opcional) y rango de fechas (opcional). |
| Salidas | Lista de movimientos con placa, celda, ingreso, salida y operadores. |
| Prioridad | Should |
| Dependencias | RF-001, RF-004 |
| Origen | [I] |

**Criterios de aceptación**

- Dado un rango de fechas, cuando se consulta el historial, entonces se muestran solo los movimientos cuyo ingreso cae en ese rango.

#### RF-007 — Registrar novedad sobre un vehículo

| Campo | Detalle |
|---|---|
| Descripción | El sistema registra un inconveniente o suceso ocurrido dentro del parqueadero y relacionado con un vehículo (accidente, rayón, daño, etc.). |
| Actor | Operador |
| Entradas | Placa, tipo de novedad (accidente, rayón, daño, otro) y descripción. |
| Proceso | Registra la novedad asociada al vehículo, y a la estadía en curso si existe, con la fecha y hora del sistema y el usuario que la registra. |
| Salidas | Confirmación con el identificador de la novedad. |
| Reglas | RN-06, RN-07 |
| Prioridad | Must |
| Dependencias | RF-102 |
| Origen | [E][U] |

**Criterios de aceptación**

- Dado un vehículo registrado, cuando el operador registra una novedad con tipo y descripción, entonces el sistema la guarda con fecha, hora y usuario.
- Dada una novedad sin descripción, cuando se intenta guardar, entonces el sistema la rechaza.

> **Pendiente P-07:** falta definir si una novedad puede registrarse para un vehículo que no está dentro, si necesita estado (abierta/cerrada) y si se adjuntan fotos.

#### RF-008 — Consultar novedades

| Campo | Detalle |
|---|---|
| Descripción | El sistema permite consultar las novedades, filtrando por placa, tipo y rango de fechas. |
| Actor | Operador, Administrador |
| Salidas | Lista de novedades con fecha, tipo, descripción, vehículo y usuario que registró. |
| Prioridad | Should |
| Dependencias | RF-007 |
| Origen | [I] |

**Criterios de aceptación**

- Dada una placa con novedades registradas, cuando se consultan sus novedades, entonces se muestran todas las de ese vehículo, de la más reciente a la más antigua.

### 3.2. Módulo 2 — Gestión de usuarios y celdas (solo identificados)

| ID | Nombre | Descripción breve | Origen |
|---|---|---|---|
| RF-101 | Registrar cliente | Datos del cliente mensualista (documento, nombre, contacto). | [E] |
| RF-102 | Registrar vehículo | Placa, tipo (moto/carro/camioneta) y cliente propietario. | [E][U] |
| RF-103 | Registrar celdas | Código de la celda, tipo de vehículo admitido (si aplica RN-08) y estado. | [E] |
| RF-104 | Consultar estado de celdas | Celdas libres y ocupadas. | [E] |
| RF-105 | Modificar clientes, vehículos y celdas | Actualizar datos y activar o inactivar registros. | [I] |
| RF-106 | Gestionar usuarios del sistema | Crear operadores y administradores, con acceso por rol. | [S] Pendiente P-01 |

### 3.3. Módulo 3 — Gestión de pagos (solo identificados)

| ID | Nombre | Descripción breve | Origen |
|---|---|---|---|
| RF-201 | Registrar pago de mensualidad | Vehículo, periodo cubierto, valor y fecha de pago. | [E] |
| RF-202 | Consultar vigencia de la mensualidad | Indica si un vehículo está al día en una fecha dada. | [U] (requisito de RN-03) |
| RF-203 | Consultar historial de pagos | Pagos por vehículo o cliente. | [I] |
| RF-204 | Gestionar tarifas | Valor de la mensualidad, posiblemente por tipo de vehículo. | [I] Pendiente P-08 |

---

## 4. Requerimientos no funcionales

Las métricas marcadas como **propuesta** son sugerencias del arquitecto. Deben confirmarse o ajustarse; no son datos dados por el cliente.

| ID | Categoría | Descripción | Justificación | Métrica o condición verificable | Validación | Prioridad |
|---|---|---|---|---|---|---|
| RNF-001 | Seguridad | Solo usuarios autenticados acceden al sistema. Las contraseñas se guardan con un algoritmo de hash para contraseñas (p. ej. bcrypt o Argon2). | Hay datos personales y registros que sirven de evidencia. | Ninguna pantalla ni operación funciona sin sesión. No hay contraseñas en texto plano en la base de datos. | Pruebas de acceso sin sesión. Revisión de la base de datos. | Must |
| RNF-002 | Seguridad | Acceso por rol: el operador no gestiona pagos, tarifas ni usuarios. | Mínimo privilegio. | Cada operación restringida devuelve "acceso denegado" a un rol no autorizado. | Pruebas por rol. | Must (depende de P-01) |
| RNF-003 | Integridad | Las operaciones de entrada y salida son atómicas: el movimiento y el estado de la celda se actualizan juntos o no se actualiza ninguno. Se respetan RN-04 y RN-05 aunque haya registros simultáneos. | Evitar celdas "fantasma" o entradas duplicadas. | En una prueba con dos registros simultáneos de la misma placa o celda, solo uno queda guardado. | Pruebas de integración y de concurrencia. | Must |
| RNF-004 | Trazabilidad | Cada entrada, salida, novedad y pago guarda el usuario responsable y la fecha y hora del servidor. No se eliminan (RN-07). | Las novedades (accidentes, rayones) pueden usarse en reclamos. | El 100 % de esos registros tiene usuario y fecha. No existe una operación de borrado. | Pruebas funcionales. Revisión del esquema. | Must |
| RNF-005 | Usabilidad | Registrar una entrada o salida requiere solo escribir la placa y confirmar. | Es la tarea más frecuente en la portería. | **Propuesta:** como máximo 2 acciones del operador después de escribir la placa. | Prueba con usuario. | Should |
| RNF-006 | Rendimiento | Las operaciones de registro y consulta responden con rapidez con el volumen del parqueadero. | Operación en la portería con vehículos esperando. | **Propuesta:** menos de 2 s por operación con la capacidad total de celdas (P-06). | Medición en pruebas. | Should |
| RNF-007 | Privacidad | Los datos personales de los clientes se tratan según la Ley 1581 de 2012 (protección de datos personales en Colombia). | Obligación legal. | Solo los roles autorizados ven los datos personales. Los datos se usan únicamente para el servicio. | Revisión de permisos. | Must |
| RNF-008 | Mantenibilidad | El código se organiza en módulos que corresponden a los tres módulos funcionales. Hay pruebas automatizadas de las reglas de negocio. | Se entrega por iteraciones. | Cada RN tiene al menos una prueba automatizada. | Ejecución de las pruebas. | Must |
| RNF-009 | Fiabilidad / recuperación | Hay copias de seguridad de la base de datos. | Pérdida de evidencias y pagos. | **Propuesta:** copia diaria y procedimiento de restauración documentado. | Prueba de restauración. | Could (según el alcance académico, P-09) |
| RNF-010 | Disponibilidad | El sistema está disponible durante el horario de operación del parqueadero. | La portería depende del sistema. | Pendiente: horario (P-06). | Pendiente. | Should |
| RNF-011 | Compatibilidad / portabilidad | Plataforma de uso (web, escritorio, etc.). | Depende de la decisión de stack. | Se define con la decisión de arquitectura (DEC-002 en adelante). | Pendiente. | Pendiente |

---

## 5. Validación del borrador

- **Duplicidades:** RF-002 y RF-202 se tocan. RF-002 es la verificación al ingresar y RF-202 es la consulta del módulo de pagos que RF-002 utiliza. No es duplicado: RF-002 depende de RF-202.
- **Dependencias entre módulos:** el módulo 1 necesita RF-102, RF-103, RF-201 y RF-202 para funcionar completo. Para programarlo y probarlo antes de los módulos 2 y 3 hará falta cargar datos de prueba (vehículos, celdas, pagos) directamente en la base de datos. El Ingeniero lo planteará en su plan.
- **Ambigüedades abiertas:** P-01 a P-09.

## 6. Preguntas pendientes

| ID | Pregunta | Afecta |
|---|---|---|
| P-01 | ¿Quiénes usan el sistema: operador y administrador? ¿Los clientes entran al sistema? | Actores, RF-106, RNF-002 |
| P-02 | ¿Cada mensualidad tiene una celda fija o el vehículo ocupa cualquier celda libre? | RF-003, RN-09, modelo de datos |
| P-03 | ¿Las celdas son distintas por tipo de vehículo (moto, carro, camioneta)? | RN-08, RF-103 |
| P-04 | Si la mensualidad vence con el vehículo dentro, ¿qué hace el sistema? | RF-002, RN-03 |
| P-05 | ¿Un cliente puede tener varios vehículos? ¿La mensualidad se paga por vehículo? | Modelo de datos, RF-201 |
| P-06 | ¿Cuántas celdas tiene el parqueadero y cuál es el horario de operación? | RNF-006, RNF-010 |
| P-07 | Novedades: ¿solo para vehículos dentro? ¿Necesitan estado (abierta/cerrada)? ¿Fotos? | RF-007, modelo de datos |
| P-08 | ¿La tarifa de la mensualidad cambia según el tipo de vehículo? | RF-204, modelo de datos |
| P-09 | ¿Es un proyecto académico? ¿Se desplegará en producción o solo se ejecuta localmente? | RNF-009, RNF-010, RNF-011 |
