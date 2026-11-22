# Solicitud de cambio CHG-003 — Creación y administración de celdas

**Proyecto:** Parqueadero "Autos Colombia"
**Versión:** 1.1
**Fecha:** 2026-11-22
**Origen:** observación del profesor a la entrega de la iteración 2.
**Estado:** **Aprobada** por el equipo el 2026-11-22: se aceptaron las recomendaciones de P-52 a P-57.

---

## 1. Observación recibida

> "La principal falta fue limitar las celdas a un inventario fijo y a la consulta del mapa: debieron permitir su creación y administración por el administrador, con las validaciones de código y ocupación correspondientes. Esa exclusión dejó incompletos también los requisitos, las historias, los mockups, los casos de uso, las secuencias y las pruebas de celdas. Los horarios y cambios de propietario amplían el proyecto, pero no cubren esas funciones faltantes."

## 2. Qué se aprobó antes y qué cambia

| Artefacto aprobado | Qué dice hoy | Cambio propuesto |
|---|---|---|
| P-28 (respuesta del equipo, iteración 2) | Las celdas son fijas: no se agregan ni cambian de tipo. | Se reemplaza: el administrador crea y administra las celdas. |
| RN-27 | Las celdas son fijas: no se agregan, no cambian de tipo y no se borran. | Se reemplaza por las reglas RN-48 a RN-53 (sección 3). |
| RF-103 "Agregar celdas" | *Won't*, fuera de alcance. | Pasa a **Must** como "Gestionar celdas". |
| RN-20 | 150 celdas de carro/camioneta y 50 de moto "por el momento", como dato configurable. | Se mantiene como **carga inicial** de la demostración; después el administrador cambia el inventario. |
| HU-018, escenario "Las celdas son fijas" | No hay opciones para agregar, borrar ni cambiar el tipo. | Se elimina ese escenario y se agregan historias nuevas. |
| Modelo de datos v1.4 (`usuarios_celdas_celda`) | Código único, tipo y `activa`. | Se amplía para guardar el motivo de inactivación y los datos de auditoría (sección 5). |

## 3. Reglas de negocio propuestas

| ID | Regla | Origen |
|---|---|---|
| RN-48 | Solo el **administrador** crea, modifica, inactiva y reactiva celdas. El operador solo las consulta en el mapa. | [E] observación del profesor |
| RN-49 | **Código de celda:** único, sin importar mayúsculas y minúsculas, con el formato del tipo (por ejemplo, `A-151` para carro/camioneta y `M-51` para moto; formato exacto según P-53). El sistema sugiere el siguiente código libre. | [E] "validaciones de código"; [I] formato |
| RN-50 | **Celda ocupada:** no se puede inactivar ni cambiar de tipo mientras tenga un vehículo dentro. | [E] "validaciones de ocupación" |
| RN-51 | **Celda inactiva** (por ejemplo, en mantenimiento): no aparece como disponible al registrar una entrada; sí aparece en el mapa, marcada como inactiva. Se inactiva con un motivo obligatorio. | [I] P-54 |
| RN-52 | **Eliminar:** solo se puede eliminar una celda que nunca se ha usado; si ya tuvo estadías, se inactiva (para no perder el historial, RN-07). | [I] P-55 |
| RN-53 | Cada creación, modificación, inactivación, reactivación o eliminación de una celda queda en la **bitácora** (RN-34). | [I] |

## 4. Requerimiento funcional propuesto

### RF-103 — Gestionar celdas [E]
- **Actor:** Administrador.
- **Proceso:** crear una celda (tipo y código, con el siguiente código sugerido), modificarla, inactivarla con motivo, reactivarla y, si nunca se usó, eliminarla (RN-48 a RN-53). Ver la lista de celdas con su estado, filtrar por tipo y estado, y buscar por código.
- **Validaciones:** código único y con formato válido; no inactivar ni cambiar de tipo una celda ocupada; no eliminar una celda con historial.
- **Prioridad:** Must.

RF-104 (mapa de celdas) se ajusta: el mapa muestra también las celdas inactivas, y los contadores usan el inventario real.

## 5. Impacto en los artefactos

| Artefacto | Cambio |
|---|---|
| Requerimientos de la iteración 2 | Versión 1.5: RF-103 Must, RN-27 reemplazada por RN-48 a RN-53, RF-104 ajustado, matriz de permisos. |
| Historias de usuario | Historias nuevas (numeración propuesta HU-033 a HU-036): crear celda, modificar celda, inactivar/reactivar celda, eliminar celda; HU-018 sin el escenario "celdas fijas" y con celdas inactivas. |
| Modelo de datos | Versión 1.5: en `usuarios_celdas_celda`, motivo de inactivación, fecha de creación y quién la creó; CHECK del formato del código por tipo; acciones de bitácora para celdas. |
| Mockups | Nuevos: lista de celdas (administrador), formulario de crear o editar, inactivar con motivo; M-20 (mapa) actualizado con celdas inactivas. |
| Casos de uso | UC nuevos de gestión de celdas (crear, modificar, inactivar/reactivar, eliminar) con «include» a la bitácora; UC-02 actualizado. |
| Diagramas de secuencia | Nuevos SD: crear celda (validación de código) e inactivar celda (validación de ocupación). |
| Clases y paquetes | `ServicioCeldas` en `usuarios_celdas`; sin módulos nuevos. |
| Código | Pantallas del administrador, servicio con validaciones, migración, menú; la entrada de vehículos ya ignora celdas inactivas. |
| Pruebas | Escenarios de las HU nuevas, validaciones de código y ocupación, y regresión completa. |
| Documentos | PDF técnico, README y, según P-57, la entrega al profesor. |

## 6. Respuestas del equipo (2026-11-22)

El equipo aceptó todas las recomendaciones:

| Pregunta | Respuesta |
|---|---|
| P-52 | **A.** Crear, modificar, inactivar/reactivar y eliminar (solo si nunca se usó). |
| P-53 | **A.** `A-` + 3 dígitos para carro/camioneta y `M-` + 2 dígitos para moto; el sistema sugiere el siguiente. |
| P-54 | **A.** Se inactiva con motivo obligatorio y solo si está libre. |
| P-55 | **A.** Solo el tipo, si está libre y nunca se ha usado; el código no se modifica. |
| P-56 | **A.** Sin máximo configurable; el límite es el del formato del código. |
| P-57 | **C.** Se corrige la entrega de la iteración 2 y se incluye en el documento técnico y en la entrega de la iteración 3. |

## 7. Preguntas (resueltas)

| ID | Pregunta | Alternativas | Recomendación |
|---|---|---|---|
| P-52 | ¿Qué operaciones tiene el administrador sobre una celda? | **A.** Crear, modificar, inactivar/reactivar y eliminar (solo si nunca se usó). **B.** Crear, modificar e inactivar/reactivar, sin eliminar nunca. **C.** Solo crear e inactivar. | **A.** Cubre "creación y administración" y protege el historial con RN-52. |
| P-53 | ¿Cómo es el código de una celda? | **A.** Prefijo por tipo y número: `A-` + 3 dígitos para carro/camioneta (`A-001` a `A-999`) y `M-` + 2 dígitos para moto (`M-01` a `M-99`), como las actuales; el sistema sugiere el siguiente. **B.** Prefijo y número libres, solo únicos. **C.** Igual que A pero con 3 dígitos también en motos (`M-001`), migrando las actuales. | **A.** Mantiene los códigos actuales y permite validar el formato. |
| P-54 | ¿Una celda se puede inactivar (por ejemplo, por mantenimiento)? | **A.** Sí, con motivo obligatorio; solo si está libre. **B.** No, solo se crean y eliminan. | **A.** |
| P-55 | ¿Qué se puede modificar de una celda existente? | **A.** El tipo, solo si está libre y nunca se ha usado; el código no se cambia (si está mal, se elimina o inactiva y se crea otra). **B.** Código y tipo, si está libre. **C.** Nada; solo inactivar. | **A.** Evita que el historial de estadías quede con un código o tipo distinto del que tenía. |
| P-56 | ¿Hay un número máximo de celdas por tipo? | **A.** No; el límite lo da el formato del código (999 y 99). **B.** Sí, un máximo configurable. | **A.** |
| P-57 | ¿Cómo se entrega el cambio al profesor? | **A.** Se corrige la entrega de la iteración 2 (nuevo PDF de entrega con requerimientos, historias, mockups, casos de uso y secuencias en StarUML y plan de pruebas de celdas), sin subirlo a GitHub. **B.** Se incluye solo en el documento técnico y en la entrega de la iteración 3. **C.** Ambas. | **C.** El profesor señaló la falta en la iteración 2; corregirla allí y mostrarla también en la siguiente entrega. |
