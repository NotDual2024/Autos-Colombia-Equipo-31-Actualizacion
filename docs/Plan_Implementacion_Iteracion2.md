# Plan de implementación — Iteración 2

**Autor:** Software Engineer · **Fecha:** 2026-11-15
**Base (aprobado):** Requerimientos iteración 2 v1.4 · HU-012 a HU-023 · Modelo de datos v1.3 (DDL 60/60) · Diseño iteración 2 v1 (mockups M-13 a M-25, UC-16 a UC-29, CL-03, CL-04, PK-01 v2, control de turno) · DEC-013 a DEC-015.
**Estado:** **Aprobado** por el equipo el 2026-11-15 (incluidos los horarios de demostración de la sección 3).

## 0. Inspección inicial

| Elemento | Resultado |
|---|---|
| Repositorio | `main` al día con GitHub (último commit: diseño aprobado de la iteración 2). |
| Pruebas actuales | `manage.py test apps` → **100/100 aprobadas**. Los modelos coinciden con las migraciones (`makemigrations --check`: sin cambios). |
| Dependencias | **No se agregan.** Todo se resuelve con Django 5.2.19 (backend de autenticación, middleware, sesiones) y JavaScript propio. |

## 1. Pasos (pruebas al final de cada uno)

| Paso | Contenido | HU | Pruebas |
|---|---|---|---|
| 1 | **Migraciones v1.3:** módulo `bitacora` (`RegistroOperacion`); `AutorizacionFueraTurno`; `HorarioOperador` definitivo; `SolicitudCambioPropietario`; `HistorialPropiedad`; celular con `CHECK`. Las restricciones son las mismas del DDL v1.3. | — | Las 18 comprobaciones nuevas del DDL, repetidas a través del ORM. |
| 2 | **`ServicioBitacora`** (registra los cambios con sus valores antes y después y nunca guarda contraseñas). | HU-023 (base) | Unitarias. |
| 3 | **Propietarios y vehículos:** servicios, búsquedas, fichas y formularios (M-13 a M-17). El menú agrega la sección "Clientes". | HU-012 a HU-015 | Todos los escenarios de las HU. |
| 4 | **Cambio de propietario:** solicitud, bandeja del administrador y aprobación transaccional con historial (M-18, M-19). | HU-016, HU-017 | Escenarios de las HU, incluida la transacción completa. |
| 5 | **Mapa de celdas** (M-20). | HU-018 | Escenarios de la HU. |
| 6 | **Operadores ampliado:** editar el nombre y restablecer la contraseña (M-21). | HU-019 | Escenarios de la HU. |
| 7 | **Horarios, autorizaciones y bitácora** (M-22, M-24, M-25). Franjas que se cruzan (RN-37) y turnos nocturnos. | HU-020, HU-022, HU-023 | Escenarios de las HU. |
| 8 | **Control de turno** (sección 5 del diseño): `BackendTurno`, `ControlTurnoMiddleware`, script de vigilancia de la sesión y sesión del operador de 12 horas como máximo. | HU-021 | Ingreso dentro y fuera del turno, sin horario, turno nocturno, autorización vigente y vencida, gracia de 5 minutos, guardado en curso después del fin del turno, administrador sin restricción. |
| 9 | **Datos de demostración**, README y regresión completa; verificación manual en el navegador; informe. | Todas | Suite completa + verificación manual. |

## 2. Efectos sobre lo ya implementado (sin cambiar el diseño aprobado)

1. **Pruebas de la iteración 1 que inician sesión:** con RN-36, un operador sin horario ya no puede iniciar sesión. Las 5 pruebas que inician sesión con el formulario y la base de las pruebas recibirán un horario de 24 horas para el operador. **No se cambia el comportamiento esperado de la iteración 1**; solo se ajusta la preparación de las pruebas a la nueva regla.
2. **Menú y encabezado:** el encabezado muestra "Operador · Turno 06:00 – 14:00" (RF-107). Se agregan las secciones del menú definidas en el diseño.
3. **Registro de vehículos y RN-23:** la coherencia entre el formato de la placa y el tipo (carro `ABC123`, moto `ABC12D` o `ABC12`) se valida en el servicio. Los datos de demostración actuales ya la cumplen.

## 3. Datos de demostración: un punto que necesita su aprobación

Con los turnos obligatorios, si el operador de demostración tuviera un horario fijo, **el profesor no podría probar con él fuera de ese horario.** Propongo:

| Usuario | Horario de demostración | Para qué |
|---|---|---|
| `operador` (María Rodríguez) | **Todos los días, 24 horas**: dos franjas por día, 00:00–12:00 y 12:00–00:00 (esta última termina a la medianoche). | Que el profesor pueda probar a cualquier hora. |
| `operador2` (Julián Torres) | **Lunes a viernes, 06:00–07:00** (una hora). | Mostrar el bloqueo fuera de turno (HU-021) y la autorización fuera de turno (HU-022). |
| `admin` | Sin restricción (RN-31). | — |

Además, los datos de demostración incluirán una **solicitud de cambio de propietario pendiente**, un vehículo con **historial de propietarios** y algunas **operaciones en la bitácora**.

## 4. Estrategia de pruebas

Igual que en la iteración 1: unitarias, de integración (servicios con base de datos), funcionales (pantallas con el cliente de pruebas, cubriendo los escenarios Dado/Cuando/Entonces de HU-012 a HU-023) y regresión completa. El reloj del sistema se sustituye para probar turnos, medianoche y vencimientos de la gracia.

**Limitación anunciada:** el script de vigilancia del navegador (avisos y cuenta regresiva de RN-35) **no** tiene pruebas automatizadas, porque el proyecto no usa herramientas de prueba de navegador y agregarlas sería una dependencia nueva. Se probará **manualmente** en el navegador. La parte del servidor (cierre al vencer la gracia, guardado en curso) sí tendrá pruebas automatizadas.

## 5. Riesgos

| Riesgo | Mitigación |
|---|---|
| Errores al calcular franjas que cruzan la medianoche | Los métodos `cubre()` y `fin_en()` del dominio se prueban con casos 22:00–06:00, 00:00–12:00 y 12:00–00:00, y en los bordes. |
| Cerrar una sesión mientras se guarda un registro | El middleware deja completar el guardado (POST) y cierra después (RN-35a). |
| Migración de `telefono` (20 → 10 caracteres) sobre datos existentes | Los datos de demostración ya cumplen el formato. La migración se prueba con una base nueva y con la base local actual. |
