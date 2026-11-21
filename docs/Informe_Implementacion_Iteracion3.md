# Informe de implementación — Iteración 3

**Autor:** Software Engineer · **Fecha:** 2026-11-20

**Funcionalidad:** Gestión de pagos. Incluye:
- registro de pagos de 1 a 12 meses, con el periodo calculado desde el día de cobro y el valor calculado por el sistema;
- descuentos por porcentaje;
- factura simulada para imprimir y correo simulado de confirmación;
- vigencia e historial de pagos;
- corrección de pagos sin borrado;
- tarifas con fecha de vigencia;
- motivo de inactivación y reactivación automática al pagar;
- mensualidades por vencer e informe de ingresos.

**Requerimientos relacionados:** RF-201 a RF-209 · HU-024 a HU-032 · RN-38 a RN-47 · Modelo de datos v1.4 (DM-12 a DM-19) · Diseño iteración 3 (UC-30 a UC-40, M-26 a M-35, sección 5).

## Archivos creados

- `src/apps/pagos/`:
  - `calendario.py`: funciones puras del calendario de cobro.
  - `tarifas.py`: tarifas y descuentos.
  - `registro.py`: registrar, corregir y confirmación.
  - `selectors.py`: historiales, factura, por vencer e ingresos.
  - `views.py` y `urls.py` (`/pagos/`).
  - `templatetags/pagos_extras.py`.
  - Plantillas de M-26 a M-35, incluida la factura para imprimir.
  - Migración `0002`.
- Migraciones `bitacora 0002` (acciones y entidades nuevas) y `usuarios_celdas 0003` (motivo de inactivación).
- `src/apps/usuarios_celdas/templates/usuarios_celdas/_inactivar.html` (M-33).
- Pruebas:
  - `pagos/tests/test_calendario.py`.
  - `pagos/tests/test_hu024_032.py`.
  - `demo/tests/test_modelo_datos_v14.py`.

## Archivos modificados

- `apps/pagos/models.py`: `Pago` ampliado según el modelo v1.4; `Descuento` y `CorreoConfirmacion` nuevos.
- `apps/pagos/services.py`: la vigencia solo cuenta pagos registrados. Agrega día de cobro, estado y meses pendientes.
- `apps/usuarios_celdas/`:
  - Motivo de inactivación en los modelos.
  - `cambiar_estado_*` exige el motivo.
  - `reactivar_por_pago`.
  - Las fichas muestran el motivo y los botones "Pagos y vigencia" y "Registrar pago".
- `apps/bitacora/models.py`: acciones CORREGIR_PAGO, HABILITAR y DESHABILITAR; entidades PAGO, TARIFA y DESCUENTO.
- `apps/core/lookups.py`: `Trim` también para `CharField`, para las restricciones de texto no vacío.
- `config/settings.py` (`DATOS_FACTURA`, ficticios) y `config/urls.py` (`/pagos/`).
- `templates/base.html`: secciones Pagos (Registrar pago, Por vencer) y Administración (Tarifas, Descuentos, Ingresos).
- `static/css/estilos.css`: estilo para los campos de mes.
- `apps/demo`:
  - La fábrica de pagos usa meses de calendario.
  - Los registros inactivos llevan motivo.
  - Datos de demostración de la iteración 3.
- Pruebas anteriores adaptadas, sin cambiar lo que verifican:
  - las inactivaciones de HU-015 envían el motivo;
  - las pruebas del modelo v1.1 crean pagos con las columnas nuevas.
- `README.md`: escenarios de la iteración 3 y número de pruebas.

## Implementación realizada

| Paso | Resultado |
|---|---|
| 1. Modelo v1.4 | Restricciones iguales a las del DDL v1.4. La migración se probó sobre la base local actual: los 15 pagos existentes quedaron como 1 mes, en efectivo, con su id como número de factura; los inactivos, con motivo "Otro". |
| 2. Calendario y vigencia | Vencimientos desde el ancla, fin de mes, año bisiesto, meses pendientes y los cuatro estados. |
| 3. Tarifas y descuentos | Tarifas con fecha (también futuras), sin edición. Descuentos de 1 % a 100 %, habilitar y deshabilitar. Todo queda en la bitácora. |
| 4. Registrar pago | Resumen antes de confirmar. Transacción con número de factura consecutivo, protección contra pagos duplicados, correo simulado y bitácora. |
| 5. Inactivación y reactivación | Motivo obligatorio; "Otro" exige descripción. Al pagar y quedar al día, se reactiva lo inactivado por falta de pago, también el propietario. Si el motivo es "Otro", el sistema lo advierte. |
| 6. Vigencia, historial y factura | Página de pagos por vehículo y por propietario. Factura para imprimir con la marca de simulación y el sello "Anulada". |
| 7. Corregir pago | Ventana de 24 horas para el operador, el administrador sin límite, solo el último pago registrado, motivo obligatorio y enlace `corrige_a`. |
| 8. Por vencer e ingresos | Hoy y los próximos 5 días, solo vehículos activos. Ingresos por fecha de pago, sin pagos corregidos, por tipo y por medio. |
| 9. Datos de demostración | Descuentos (uno habilitado y uno deshabilitado), tarifa programada, pago con descuento (`KJH205`), pago corregido (`TYU318`), vehículo atrasado e inactivo por falta de pago (`WER74D`) y vehículos por vencer (`ABC123`, `GHJ852`). |

## Pruebas ejecutadas (resultados reales)

`python manage.py test apps` → **Ran 240 tests … OK** · `makemigrations --check` → sin cambios pendientes · `docs/sql/validar_ddl.py` → 91/91.

| Prueba | Resultado |
|---|---|
| Unitarias del calendario (18 → 18, 31/01 → 28/02 → 31/03, 29/02, día 30, cambio de año, meses pendientes) | Aprobadas |
| Integración: restricciones del DDL v1.4 a través del ORM (valor calculado, descuento, corrección, factura única, pago repetido, motivo de inactivación) | Aprobadas |
| Funcionales: escenarios Dado/Cuando/Entonces de HU-024 a HU-032 y permisos por rol, con el cliente de pruebas | Aprobadas |
| Regresión: las 154 pruebas de las iteraciones 1 y 2, más una prueba nueva de que un pago corregido no cuenta para la entrada ni para los avisos | Aprobadas: 240/240 en total |

Verificación manual en el navegador, el 20/11/2026 hacia las 23:50, con una base de demostración aparte; la base local `db.sqlite3` no se tocó:

| Caso | Resultado |
|---|---|
| Registrar pago de `WER74D` como `operador` | Vencida hace 94 días, debe 4 meses. Con 4 meses, transferencia y 10 % de descuento: periodo 18/08/2026 → 18/12/2026, 320 000 − 32 000 = 288 000 COP. Se reactivó el vehículo y se envió el correo simulado. |
| Pagos de `TYU318` | Factura 000017 "Corregido" con el motivo y el número de la que la reemplaza (000018). Vigencia "Al día" hasta el 20/01/2027. |
| Factura 000017 | Marca "SIMULACIÓN – SIN VALIDEZ FISCAL", datos ficticios del parqueadero, cliente, vehículo, totales y sello "ANULADA – reemplazada por la factura N.º 000018". |
| Ficha de `TYU318` | Botones "Pagos y vigencia" y "Registrar pago". El formulario de inactivar pide "Falta de pago" u "Otro" con descripción. |
| Administrador | Tarifas: actuales e historial, con la tarifa de 2027 como "Programada". Descuentos: uno habilitado y uno deshabilitado. Ingresos de noviembre por tipo y medio. |
| Por vencer | `ABC123` "Vence hoy" y `GHJ852` en 3 días. |

## Problemas encontrados y resueltos

- **CHECK con valores nulos.** En SQLite, `length(trim(NULL)) > 0` da NULL, y un CHECK con NULL se acepta. Por eso un pago "corregido" sin motivo, o un motivo "Otro" sin descripción, pasaban la restricción del ORM. Lo detectaron las pruebas del modelo. Se agregó `isnull=False` a esas condiciones; el DDL ya usaba `coalesce`.
- **Lookup `trim` en `CharField`.** Solo estaba registrado para `TextField`, y la migración de la descripción de inactivación fallaba. Se registró también para `CharField`.
- **Página de resultado sin la factura.** El diccionario guardado en la sesión tenía la clave `pago` (un número) y reemplazaba al objeto en el contexto. Se reordenó el contexto.
- **Historial ancho.** En pantallas angostas los botones quedaban fuera de vista. La tabla ahora se desplaza horizontalmente y las fechas ocupan dos líneas.
- **Campos sin estilo.** Los campos de texto sin `type` y el selector de mes no tomaban el estilo; se corrigió.

## Limitaciones conocidas

- **Diálogo de impresión:** se verificó el contenido de la factura y que tenga la hoja de estilos de impresión, pero no se abrió el diálogo de impresión del navegador.
- **Correos de confirmación:** se guardan en la base de datos y en el registro del servidor; no hay una pantalla para verlos, porque no estaba en el diseño.
- **Bitácora de la ficha del vehículo:** los pagos y correcciones se registran con la entidad PAGO, así que aparecen en la bitácora general y no en la de la ficha del vehículo.
- **Fechas de los pagos de demostración:** la fábrica pone como fecha de pago el inicio del periodo, para que el historial se vea realista. Por eso el informe de ingresos del mes actual muestra solo los pagos cuyo periodo empezó este mes.
- **RNF-006** (menos de 2 s): no se midió formalmente.
