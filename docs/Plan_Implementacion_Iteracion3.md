# Plan de implementación — Iteración 3

**Autor:** Software Engineer · **Fecha:** 2026-11-20
**Base (aprobado):** Requerimientos iteración 3 v1.2 · HU-024 a HU-032 · Modelo de datos v1.4 (DDL 91/91, DM-12 a DM-19) · Diseño iteración 3 v1 (mockups M-26 a M-35, UC-30 a UC-40, CL-05, CL-06, PK-01 v3, ARQ-03 v3, mecanismos de la sección 5).
**Estado:** **Aprobado** por el equipo el 2026-11-20.

## 0. Inspección inicial

| Elemento | Resultado |
|---|---|
| Repositorio | `main` con el commit de las historias de la iteración 3 (`66b86a4`). Los requerimientos, el modelo v1.4 y el diseño todavía no están commiteados. |
| Pruebas actuales | `manage.py test apps` → **154/154 aprobadas**. `makemigrations --check`: sin cambios. |
| Dependencias | **No se agregan.** La factura es una página HTML con `@media print`; el calendario de cobro usa `datetime` y `calendar` de Python. |

## 1. Pasos (pruebas al final de cada uno)

| Paso | Contenido | HU | Pruebas |
|---|---|---|---|
| 1 | **Migraciones v1.4:** columnas nuevas de `Pago`, `Descuento`, `CorreoConfirmacion`, motivo de inactivación en propietario y vehículo, acciones y entidades nuevas de la bitácora. Migración de datos según la sección 8.3 del modelo (pagos existentes: 1 mes, efectivo, factura = id; inactivos: motivo OTRO). | — | Las 31 comprobaciones nuevas del DDL, repetidas a través del ORM. Migración probada sobre una base nueva y sobre la base local actual. |
| 2 | **`CalendarioCobro` y `ServicioVigencia` ampliado:** día de cobro, vencimientos desde el ancla, meses pendientes, estado. `ultimo_pago` y `esta_vigente` solo cuentan pagos REGISTRADOS. | HU-025 | Unitarias: 18 → 18, 31/01 → 28/02 → 31/03, 29/02 en año bisiesto, 30 → 28/02 → 30/03, diciembre → enero; meses pendientes con 4 meses atrasados; los cuatro estados. |
| 3 | **Tarifas y descuentos** (M-31, M-32): servicios, pantallas del administrador y bitácora. El menú amplía la sección Administración. | HU-027, HU-031 | Escenarios de las HU, incluidos tarifa futura, fecha repetida, porcentaje inválido y 403 del operador. |
| 4 | **Registrar pago** (M-26, M-27): `preparar` y `registrar` en una transacción, número de factura consecutivo, protección contra pagos duplicados, correo de confirmación y bitácora. El menú agrega la sección Pagos. | HU-024 | Todos los escenarios de HU-024: primer pago, pago tarde, fin de mes, meses atrasados, varios meses, descuento, valor no editable, medio obligatorio, vehículo dentro que sale del proceso de retiro, correo. |
| 5 | **Motivo de inactivación y reactivación** (M-33): `cambiar_estado` con motivo en `usuarios_celdas`, `reactivar_por_pago`, advertencia si el motivo es "Otro". La ficha del vehículo y del propietario muestran el motivo y los botones de pagos. | HU-028 | Escenarios de HU-028, incluida la reactivación del propietario y que el sistema no inactiva solo. |
| 6 | **Vigencia, historial y factura** (M-28, M-29): página de pagos del vehículo y del propietario, factura para imprimir con el sello "Anulada". | HU-025, HU-026 | Escenarios de las HU; la factura contiene todos los datos y la marca de simulación. |
| 7 | **Corregir pago** (M-30): regla de las 24 horas, solo el último pago registrado, motivo obligatorio, transacción con `corrige_a`. | HU-029 | Escenarios de HU-029: dentro y fuera de las 24 horas, administrador, sin motivo, pago ya corregido, pago que no es el último, factura anulada. |
| 8 | **Por vencer e ingresos** (M-34, M-35). | HU-030, HU-032 | Escenarios de las HU: vence hoy, límite de 5 días, solo activos; ingresos sin corregidos y por fecha de pago. |
| 9 | **Datos de demostración**, README y regresión completa; verificación manual en el navegador (incluida la impresión de la factura); informe. | Todas | Suite completa + verificación manual. |

## 2. Efectos sobre lo ya implementado (sin cambiar el diseño aprobado)

1. **Fábrica de pagos de prueba (`demo/fabricas.py`):** hoy crea periodos de 30 días. Pasará a usar meses de calendario (`CalendarioCobro`) con 1 mes, efectivo y número de factura consecutivo. Las pruebas de las iteraciones 1 y 2 que la usan no cambian lo que verifican; solo cambian las fechas internas de los periodos.
2. **Inactivar propietarios y vehículos (iteración 2):** el formulario pide el motivo (M-33). Las pruebas de HU-015 que inactivan se actualizan para enviar el motivo; el comportamiento verificado (puede salir, no puede entrar) no cambia.
3. **Avisos de retiro, entrada y mapa:** usan `ultimo_pago` y `esta_vigente`. Al filtrar solo pagos REGISTRADOS, un pago corregido deja de contar sin tocar ese código. Se agregan pruebas de regresión para esto.
4. **Configuración:** `settings.DATOS_FACTURA` con los datos ficticios del parqueadero (nombre, NIT ficticio, dirección).

## 3. Datos de demostración

| Dato | Para qué |
|---|---|
| Descuento "Cliente frecuente" de 10 %, habilitado, y "Promoción apertura" de 15 %, deshabilitado | Probar HU-024 y HU-031. |
| Un vehículo con un pago de 3 meses con descuento, y otro con un pago corregido y su reemplazo | Ver el historial, la factura anulada y la nueva (HU-026, HU-029). |
| Un vehículo con la mensualidad vencida hace 3 meses e inactivo por falta de pago | Ver los meses pendientes y la reactivación al pagar (HU-024, HU-028). |
| Dos vehículos que vencen en los próximos 5 días, uno de ellos hoy | Ver la lista de por vencer (HU-030). |
| Un pago registrado por el operador hace menos de 24 horas | Que el profesor pueda probar la corrección con el operador (HU-029). |
| Una tarifa de carro programada para el 01/01/2027 | Ver una tarifa futura (HU-027). |

Las fechas se calculan desde el día en que se cargan los datos, para que los estados se vean igual sin importar cuándo se prueba.

## 4. Estrategia de pruebas

Igual que en las iteraciones anteriores: unitarias (calendario, cálculo del valor, `corregible_por`), de integración (servicios con base de datos y transacciones), funcionales (pantallas con el cliente de pruebas, cubriendo los escenarios de HU-024 a HU-032) y regresión completa. El reloj del sistema se sustituye para probar fin de mes, año bisiesto y la ventana de 24 horas.

**Limitación anunciada:** la impresión real de la factura (diálogo del navegador) no se prueba automáticamente; se verifica que la página tenga los datos y la hoja de estilos de impresión, y se prueba la impresión **manualmente** en el navegador.

## 5. Riesgos

| Riesgo | Mitigación |
|---|---|
| Errores en fin de mes y años bisiestos | Funciones puras con pruebas de cada caso borde (paso 2) antes de usarlas en los servicios. |
| Migración que choque con los nuevos CHECK (por ejemplo, el valor calculado) | Los datos existentes se migran con `tarifa_unitaria = valor_bruto = valor` y `meses = 1`, que cumplen los CHECK. Se prueba sobre la base local actual. |
| Dos operadores registran el mismo pago a la vez | Restricciones UNIQUE de factura y de (vehículo, inicio) más mensaje claro (diseño, sección 5.2). |
| Un pago corregido que siga contando para la entrada o los avisos | Pruebas de regresión del paso 3 del apartado 2. |
