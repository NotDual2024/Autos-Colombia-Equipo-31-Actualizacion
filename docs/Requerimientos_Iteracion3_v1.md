# Requerimientos — Iteración 3: Gestión de pagos

**Proyecto:** Parqueadero "Autos Colombia"
**Versión:** 1.2
**Fecha:** 2026-11-20
**Base:** Anexo A de `Requerimientos_v2.md` (RF-201 a RF-204), modelo de datos v1.3 (tablas `pagos_pago` y `pagos_tarifa`), RN-01 a RN-37 aprobadas y el pendiente P-33 de la iteración 2.
**Estado:** **Aprobado** por el equipo del proyecto el 2026-11-20.

| Versión | Cambios |
|---|---|
| 1 | Borrador inicial con las preguntas P-39 a P-47 y P-33. |
| 1.1 | Respuestas del equipo a P-33 y P-39 a P-47. Se proponen RN-38 a RN-47 y RF-208 (descuentos). Impacto en el modelo de datos. Nuevas preguntas: P-48 a P-51. |
| 1.2 | Respuestas del equipo a P-48 a P-51. Se ajustan RN-39, RN-42, RN-44 y RN-47, y RF-206 y RF-208. Sin preguntas abiertas. Aprobada por el equipo el 2026-11-20, incluidos los puntos [I]. |

Etiquetas de origen: **[E]** enunciado · **[U]** equipo · **[I]** inferido, por confirmar.

---

## 1. Respuestas del equipo (2026-11-20)

| Pregunta | Respuesta | Dónde quedó |
|---|---|---|
| P-39 Duración | La mensualidad vence el **mismo día del mes siguiente**: si se paga el 18, vence el 18 del otro mes; si se paga el 31 y el mes no tiene 31, vence el **último día del mes**. | RN-38 |
| P-40 Inicio del periodo | La fecha de cobro se mantiene desde que se obtuvo la membresía. Si el dueño paga 4 días tarde, el mes siguiente se paga normal: **la fecha de cobro no se mueve ni se extiende**. | RN-39 |
| P-41 Varios meses | Sí. | RN-40 |
| P-42 Descuentos | Puede haber descuentos. **Solo el administrador** los crea y habilita, por el motivo que sea; una vez habilitado, el **operador** puede aplicarlo al registrar un pago. | RN-41, RN-42, RF-208 |
| P-43 Medio de pago y comprobante | Sí. | RN-43 |
| P-44 Pago mal registrado | El pago mal registrado **queda en un registro** y se registra de nuevo la información corregida. | RN-44, RF-206 |
| P-45 Tarifas | Las gestiona el administrador. | RN-45, RF-204 |
| P-33 Inactivación | Se aprueba la recomendación: motivo "Falta de pago" u "Otro"; al pagar se reactiva solo lo inactivado por falta de pago. | RN-46, RF-205 |
| P-46 Confirmación | Sí: se envía un **correo simulado** y se genera una **factura simulada** que se puede **descargar**. | RN-47 |
| P-47 Consultas | Se aprueba la recomendación: mensualidades por vencer en los próximos 5 días e informe de ingresos por mes para el administrador (este último *Could*). | RF-207, RF-209 |
| P-48 Cliente que vuelve | Si el vehículo no está dentro, debe pagar para volver a ingresar; si no viene y no paga, no es problema del parqueadero. Vencida no entra (RN-03); si está dentro, aplican los avisos (RN-13 a RN-17). **No hay membresía nueva**: se mantiene la regla general. | RN-39 |
| P-49 Tipo de descuento | El descuento tiene una **descripción** y un **porcentaje** que define el administrador. | RN-42, RF-208 |
| P-50 Quién corrige | El operador puede corregir un pago durante las **24 horas** siguientes a su registro; después, solo el administrador. | RN-44, RF-206 |
| P-51 Factura | **Página para imprimir** que el navegador guarda como PDF. | RN-47 |

---

## 2. Lo que ya estaba definido

| Tema | Definición | Origen |
|---|---|---|
| Servicio | Solo por mensualidad, sin cobro por horas. | RN-01 |
| Pago por vehículo | Un propietario con varios vehículos paga una mensualidad por cada uno. | RN-10 |
| Tarifas | Carro o camioneta 150 000 COP; moto 80 000 COP. | RN-19 |
| Entrada | Solo entra un vehículo con la mensualidad vigente. | RN-03 |
| Vencida dentro | Puede salir pero no volver a entrar sin pagar; si paga dentro de los 8 días, sale del proceso de retiro. | RN-13, RN-17 |
| Quién registra | El operador registra pagos; el administrador puede hacer todo. | RNF-002 |
| Trazabilidad | Cada pago guarda el usuario y la fecha y hora; no hay borrado; queda en la bitácora. | RNF-004, RN-07, RN-34 |
| Valor histórico | El pago guarda una copia del valor cobrado; si la tarifa cambia, los pagos anteriores no cambian. | DM-04 |
| Cambio de propietario | Los pagos siguen asociados al vehículo. | RN-33 |

---

## 3. Reglas de negocio propuestas

| ID | Regla | Origen |
|---|---|---|
| RN-38 | **Fecha de cobro.** La membresía de un vehículo empieza el día de su primer pago; ese número de día es su **día de cobro**. Cada mensualidad vence el día de cobro del mes siguiente; si ese mes no tiene ese día, vence el último día del mes. Ejemplos: 18/11 → 18/12; 31/01 → 28/02 (o 29/02) → 31/03. La mensualidad está vigente hasta el día de vencimiento inclusive. | [U] P-39 |
| RN-39 | **Pagar tarde no mueve la fecha.** Cada pago cubre desde el vencimiento anterior, sin excepción, aunque el vehículo haya estado fuera varios meses. Si vence el 18/12 y paga el 22/12, el pago cubre hasta el 18/01. Mientras no pague, el vehículo no puede entrar (RN-03). El sistema muestra cuántos meses debe pagar para quedar al día. | [U] P-40, P-48 |
| RN-40 | Un pago puede cubrir de **1 a 12 meses** seguidos. | [U] P-41 (el máximo de 12 es [I]) |
| RN-41 | **Valor del pago** = tarifa vigente del tipo de vehículo × número de meses − descuento aplicado (si hay). El sistema lo calcula; no se escribe a mano. | [U] P-42, RN-19 |
| RN-42 | **Descuentos.** Solo el administrador crea descuentos, con una **descripción** (el motivo) y un **porcentaje** entre 1 % y 100 %, y los habilita o deshabilita. Un descuento no se edita: si cambia, se deshabilita y se crea otro. Al registrar un pago, el operador puede aplicar **un** descuento habilitado; el porcentaje se aplica sobre el valor de todos los meses del pago. | [U] P-42, P-49 (rango y "no se edita" son [I]) |
| RN-43 | Todo pago registra el **medio de pago** (efectivo, transferencia o tarjeta). | [U] P-43 |
| RN-44 | **Corrección.** Un pago mal registrado no se borra ni se modifica: queda en el registro marcado como corregido, con el motivo obligatorio, y se registra un pago nuevo con los datos correctos. El pago corregido deja de contar para la vigencia y para los ingresos. El operador puede corregir un pago durante las **24 horas** siguientes a su registro; después, solo el administrador. | [U] P-44, P-50 |
| RN-45 | **Tarifas.** Solo el administrador registra una tarifa nueva por tipo de vehículo, con la fecha desde la que rige (puede ser futura). Las tarifas anteriores no se editan ni se borran. | [U] P-45 |
| RN-46 | **Motivo de inactivación.** Al inactivar un vehículo o un propietario se elige el motivo "Falta de pago" u "Otro" (con descripción). Al registrar un pago, si el vehículo o su propietario están inactivos **por falta de pago**, se reactivan automáticamente; si es por "Otro", siguen inactivos y el sistema lo advierte. El sistema no inactiva a nadie por su cuenta. | [U] P-33 |
| RN-47 | **Confirmación.** Al registrar un pago, el sistema envía un **correo simulado** al propietario y deja disponible una **factura simulada** como página para imprimir (el navegador la guarda como PDF). La factura lleva número consecutivo, fecha, datos ficticios del parqueadero, propietario (nombre y cédula), vehículo, periodo, meses, tarifa, descuento, total, medio de pago y quién lo registró, con la marca "Simulación – sin validez fiscal". | [U] P-46, P-51 (los datos de la factura son [I]) |

---

## 4. Requerimientos funcionales

### RF-201 — Registrar pago de mensualidad [E][U]
- **Actor:** Operador, Administrador.
- **Entradas:** placa, número de meses (1 a 12), medio de pago y, opcional, un descuento habilitado.
- **Proceso:** el sistema muestra el vehículo, su propietario, la tarifa vigente, los meses pendientes, el periodo que cubrirá el pago (RN-38, RN-39) y el valor calculado (RN-41); el usuario confirma; se guarda con el usuario y la fecha y hora; se reactiva lo que corresponda (RN-46); se envía el correo simulado y queda disponible la factura (RN-47); queda en la bitácora.
- **Efecto:** el vehículo queda al día si el pago cubre hasta hoy o después. Si estaba dentro con la mensualidad vencida, sale del proceso de retiro (RN-17).
- **Prioridad:** Must.

### RF-202 — Consultar vigencia de la mensualidad [U]
- **Actor:** Operador, Administrador.
- **Salida:** estado (**al día**, **vence hoy** o **vencida hace N días**), fecha de vencimiento, día de cobro, meses pendientes y último pago. En la ficha del vehículo y al buscar por placa.
- **Prioridad:** Must.

### RF-203 — Consultar historial de pagos [I]
- **Actor:** Operador, Administrador.
- **Salida:** pagos de un vehículo o de todos los vehículos de un propietario: periodo, meses, valor, descuento, medio de pago, fecha, quién lo registró y si fue corregido. Desde cada pago se abre su factura para imprimir.
- **Prioridad:** Must.

### RF-204 — Gestionar tarifas [U]
- **Actor:** Administrador.
- **Proceso:** registrar una tarifa nueva por tipo con su fecha "vigente desde" (RN-45). Ver la tarifa actual y el historial.
- **Prioridad:** Must.

### RF-205 — Motivo de inactivación y reactivación al pagar [U]
- **Actor:** Operador, Administrador.
- **Proceso:** RN-46. La ficha muestra el motivo de la inactivación.
- **Prioridad:** Must.

### RF-206 — Corregir un pago mal registrado [U]
- **Actor:** Operador (dentro de las 24 horas siguientes al registro), Administrador (en cualquier momento).
- **Proceso:** se elige el pago, se escribe el motivo y se registran los datos correctos (RN-44). Ambos pagos quedan en el historial y en la bitácora. Si el operador intenta corregir un pago de más de 24 horas, el sistema se lo impide e indica que lo haga el administrador.
- **Prioridad:** Must.

### RF-207 — Mensualidades por vencer [U]
- **Actor:** Operador, Administrador.
- **Salida:** vehículos cuya mensualidad vence en los próximos 5 días, con el propietario y su celular.
- **Prioridad:** Should.

### RF-208 — Gestionar descuentos [U]
- **Actor:** Administrador.
- **Proceso:** crear un descuento con descripción y porcentaje, habilitarlo y deshabilitarlo (RN-42). Ver la lista de descuentos con su estado.
- **Prioridad:** Must.

### RF-209 — Informe de ingresos por mes [U]
- **Actor:** Administrador.
- **Salida:** total recaudado por mes, por tipo de vehículo y por medio de pago, sin contar pagos corregidos.
- **Prioridad:** Could.

---

## 5. Impacto en el modelo de datos (para la siguiente fase)

Las respuestas requieren cambios al modelo aprobado (v1.3), que se presentarán en el modelo v1.4 para su aprobación:

- **Pago:** número de meses, medio de pago, descuento aplicado, porcentaje y valor antes del descuento, estado (registrado o corregido), motivo de la corrección, quién corrigió y el pago que lo reemplaza, número de factura.
- **Descuento:** tabla nueva (descripción, porcentaje, habilitado, quién lo creó, fecha).
- **Propietario y vehículo:** motivo de inactivación y su descripción.
- **Correo simulado de confirmación:** hoy los correos están ligados a un vencimiento (máximo 2 por vencimiento); el de confirmación de pago necesita su propio tipo o tabla.
- **Día de cobro:** como no cambia nunca (RN-39), se puede calcular desde el primer pago vigente; se decide en el modelo.
- **Factura:** al ser una página para imprimir, no se necesita biblioteca de PDF.

---

## 6. Preguntas para el equipo

No hay preguntas abiertas. Los puntos marcados **[I]** (máximo de 12 meses, rango del porcentaje, descuentos no editables y datos de la factura) quedaron aprobados con este documento el 2026-11-20.
