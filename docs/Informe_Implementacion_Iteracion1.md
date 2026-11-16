# Informe de implementación — Iteración 1

**Autor:** Software Engineer · **Fecha:** 2026-11-15

**Funcionalidad:** Gestión de la entrada y salida de vehículos, novedades, avisos de vencimiento (simulados), contacto con autoridades y gestión básica de operadores.

**Requerimientos relacionados:** RF-001 a RF-012 y RF-106 · HU-001 a HU-011 · RN-01 a RN-24 · RNF-001 a RNF-014 · DEC-001 a DEC-012 · CHG-001 y CHG-002.

## Archivos creados

- `requirements.txt`, `README.md`, `.claude/launch.json` (configuración local de vista previa).
- `src/manage.py`, `src/config/` (settings, urls, wsgi).
- `src/apps/` con 8 módulos (`core`, `cuentas`, `usuarios_celdas`, `pagos`, `entradas_salidas`, `novedades`, `notificaciones`, `demo`). Cada uno tiene `models`, `services`, `selectors`, vistas, plantillas, migraciones y pruebas, según corresponda.
- `src/templates/` (base, inicio de sesión, operadores, 403) y `src/static/css/estilos.css` (estilo de las referencias, CHG-002).
- `docs/Analisis_Referencias_UI.md`, `docs/referencias_ui/`.

## Archivos de documentación modificados

- Requerimientos v2.11: RN-24 y el tipo de novedad "Observación" (CHG-002).
- Modelo de datos v1.2 y DDL v1.2: `OBSERVACION`; la columna `tipo` de la novedad pasa a `VARCHAR(12)`. El DDL sigue pasando 42/42.
- Mockups: nota del estilo final. PDF: tabla de entregables.

## Implementación realizada

| Paso | Resultado |
|---|---|
| 1. Base, `core`, `cuentas` | Argon2, inicio de sesión con mensaje genérico, roles, sin `/admin`, reloj sustituible, correo simulado detrás de una interfaz, lookup `GLOB`. |
| 2. Modelos | Todo el modelo v1.2 con las mismas restricciones del DDL aprobado (`UniqueConstraint` parciales, `CheckConstraint` con `GLOB` y longitud, clave primaria compuesta de `NovedadEstadia`). |
| 3. Entradas y salidas | Servicios transaccionales; cuadrícula de celdas por bloques de 24; ocupación; consulta de celda; historial con novedades. |
| 4. Novedades | Varias placas por novedad, hora del hecho y validación de presencia de cada vehículo (rechazo total). Modal desde la salida. |
| 5. Vencimientos | Lista calculada; aviso automático idempotente (APScheduler al iniciar y cada hora, también recupera los atrasados); botón con confirmación y un solo reenvío; los fallidos no cuentan; contacto con autoridades solo para el administrador. |
| 6. Operadores | Crear, desactivar y reactivar (sin borrado). |
| 7. Datos de demostración | Comando `cargar_datos_demo`: 4 usuarios, 200 celdas, 8 propietarios (1 inactivo), 15 vehículos, pagos con fechas relativas, 11 vehículos dentro, historial y novedades. |

## Pruebas ejecutadas (resultados reales)

`python manage.py test apps` → **Ran 100 tests … OK**

| Prueba | Resultado |
|---|---|
| Unitarias (reloj, correo, métodos de dominio, detección del proceso del planificador) | Aprobadas |
| Integración (servicios + base de datos; restricciones del DDL a través del ORM) | Aprobadas |
| Funcionales (todos los escenarios Dado/Cuando/Entonces de HU-001 a HU-011 y permisos por rol, con el cliente de pruebas) | Aprobadas |
| Regresión (suite completa después de cada paso y al final) | Aprobadas: 100/100 |
| Verificación manual en el navegador | Inicio de sesión, entrada (cuadrícula y registro), salida con novedades y modal, vehículos dentro, historial, vencidos (operador y administrador) y operadores. Coinciden con las referencias. Al iniciar el servidor, el planificador envió exactamente 1 correo por cada uno de los 3 vencimientos (sin duplicados). |

## Problemas encontrados y resueltos

- `OBSERVACION` (11 caracteres) no cabía en `VARCHAR(10)`. Se amplió a 12 como parte de CHG-002 y se documentó en el DDL v1.2.
- Las plantillas modificadas no se recargaron en el servidor ya iniciado. Se verificó con un render directo; basta con reiniciar el servidor.

## Limitaciones conocidas

- **RNF-003:** la prueba de concurrencia simula el choque en la base de datos y verifica el mensaje. No es una prueba con dos hilos reales sobre SQLite.
- **RNF-006** (menos de 2 s): no se midió formalmente. En la verificación manual las páginas respondieron de forma inmediata, pero esto no es una medición.
- La demostración usa el servidor de desarrollo de Django (limitación aceptada en la arquitectura).
- Sin pantallas de las iteraciones 2 y 3.

## Estado final

**Completado y verificado**, salvo las limitaciones anteriores. Falta escribir las conclusiones del PDF (capítulo 12) y hacer el commit.
