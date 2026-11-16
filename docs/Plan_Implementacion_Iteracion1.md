# Plan de implementación — Iteración 1

**Autor:** Software Engineer
**Fecha:** 2026-11-15
**Base (todo aprobado):** Requerimientos v2.10 · HU-001 a HU-011 · Arquitectura v1 · Modelo de datos v1.1 (DDL validado) · Diseño UML v1 · Mockups v1 · DEC-001 a DEC-012.
**Estado:** **Aprobado** por el equipo del proyecto el 2026-11-15.

---

## 0. Inspección inicial (hecha)

| Elemento | Resultado |
|---|---|
| Estructura | Repositorio Git (`main`, sincronizado con `origin`) con `docs/`, `tools/` y `Skills/` (sin versionar). **No hay código previo.** |
| Python | 3.14.2, con `venv` disponible. |
| Dependencias | Instalación de prueba en un entorno aislado: **Django 5.2.19**, **APScheduler 3.11.3** y **argon2-cffi 25.1.0** se instalan con wheels para Python 3.14. Verifiqué que Argon2 genera hashes `$argon2id`. |
| Versiones | Consultadas en PyPI el 2026-11-15. Django 5.2.19 es la última de la rama 5.2 LTS (DEC-010); APScheduler 3.11.3 es la última estable; argon2-cffi 25.1.0 es la última. |

---

## 1. Objetivo y alcance

**Objetivo:** implementar y probar la iteración 1 según los artefactos aprobados.

| Incluido | No incluido (otras iteraciones) |
|---|---|
| Todos los **modelos** del sistema completo (DEC-001), con las restricciones del DDL aprobado | Pantallas de propietarios, vehículos y celdas (iteración 2) |
| Inicio de sesión y roles (UC-01, RNF-001, RNF-002) | Horarios de operador (RF-107): solo se crea la tabla provisional |
| HU-001 a HU-011 (UC-02 a UC-15) y pantallas M-01 a M-12 | Pantallas de pagos y tarifas (iteración 3) |
| Correo simulado, planificador APScheduler | Correo real |
| Datos de demostración (RNF-014) y README | Despliegue en servidor (fuera del alcance, P-09) |

---

## 2. Dependencias (`requirements.txt`, versiones fijadas)

```
Django==5.2.19
APScheduler==3.11.3
argon2-cffi==25.1.0
tzdata==2026.6          # zona horaria America/Bogota en Windows (dependencia de Django)
```

No se agregan otras librerías. Las pruebas usan el framework de pruebas que trae Django (sin pytest) y la interfaz usa CSS propio (sin frameworks), como dice la arquitectura (sección 9).

---

## 3. Archivos que se crearán

```
requirements.txt
README.md                                 instalación, ejecución, usuarios de demostración, pruebas, copia de seguridad
src/manage.py
src/config/{settings.py, urls.py, wsgi.py}
src/templates/base.html                   menú por rol (M-01 a M-12)
src/static/css/estilos.css
src/apps/core/        reloj.py, errores.py, correo.py (ServicioCorreo + simulado), lookups.py (GLOB), tests/
src/apps/cuentas/     models.py (Usuario, HorarioOperador), permisos.py, services.py, views.py, forms.py, urls.py, templates/, tests/
src/apps/usuarios_celdas/  models.py (Propietario, Vehiculo, Celda), tests/
src/apps/pagos/       models.py (Tarifa, Pago), services.py (ServicioVigencia), tests/
src/apps/entradas_salidas/ models.py (Estadia), services.py, selectors.py, views.py, forms.py, urls.py, templates/, tests/
src/apps/novedades/   models.py (Novedad, NovedadEstadia), services.py, selectors.py, views.py, forms.py, urls.py, templates/, tests/
src/apps/notificaciones/ models.py (AvisoCorreo, ContactoAutoridad), services.py, planificador.py, management/commands/enviar_avisos_vencimiento.py, views.py, urls.py, templates/, tests/
src/apps/demo/        management/commands/cargar_datos_demo.py, tests/
```

Además: `.gitignore` (se agrega `db.sqlite3`, que ya está cubierto por `*.sqlite3`) y `docs/ESTADO_PROYECTO.md`. No se modifica ningún documento de diseño aprobado.

---

## 4. Estrategia de implementación (pasos incrementales; pruebas al final de cada paso)

| Paso | Contenido | HU / RF | Pruebas del paso |
|---|---|---|---|
| 1 | Proyecto base: `settings` (español de Colombia, `America/Bogota`, `USE_TZ`, Argon2 primero, `AUTH_USER_MODEL`, sin `/admin`), `core` (Reloj, ErrorNegocio, ServicioCorreo y simulado, lookup GLOB), plantilla base y CSS, `cuentas` (Usuario con rol, inicio y cierre de sesión, control de acceso por rol). | UC-01, RNF-001, RNF-002 | Hash Argon2, inicio de sesión, usuario inactivo, acceso por rol, vistas sin sesión. |
| 2 | **Todos los modelos** con las restricciones del DDL aprobado (`UniqueConstraint` parciales, `CheckConstraint`, `on_delete=PROTECT`) y migraciones. | DEC-001, modelo v1.1 | Las 42 reglas del DDL, repetidas a través del ORM (placas, cédula, RN-04, RN-05, RN-22…). |
| 3 | `entradas_salidas`: servicios de entrada y salida (transacción), vigencia (`pagos.ServicioVigencia`), celdas compatibles, ocupación, consulta de celda, historial. Pantallas M-02 a M-05. | HU-001 a HU-004 | Todos los escenarios Dado/Cuando/Entonces de HU-001 a HU-004, incluida la medianoche. |
| 4 | `novedades`: registro con varias placas y validación de presencia; consulta. Pantallas M-06 y M-07. | HU-005, HU-006 | Escenarios de HU-005 y HU-006 (dos vehículos, después de la salida, rechazo total). |
| 5 | `notificaciones`: lista de vencidos, aviso automático idempotente (RN-11, RN-21), botón manual con confirmación y un solo reenvío (RN-22), fallos que no cuentan, contacto con autoridades (solo administrador), planificador APScheduler y comando. Pantallas M-08 a M-11. | HU-007 a HU-009, HU-011 | Escenarios de las HU; día 8 frente a día 9; fallo simulado del correo (RNF-013); el planificador no arranca dos veces. |
| 6 | Gestión de operadores (crear, desactivar, reactivar). Pantalla M-12. | HU-010 | Escenarios de HU-010. |
| 7 | Comando `cargar_datos_demo` (administrador y operador de prueba, 150 + 50 celdas, propietarios, vehículos, pagos vigentes, uno que vence hoy y uno vencido hace más de 8 días, vehículos dentro) y `README.md`. | RNF-014, RNF-011 | Ejecución del comando en una base de datos vacía; recorrido de las HU con esos datos. |
| 8 | Regresión completa, verificación manual en el navegador (pantallas reales frente a los mockups) e informe de implementación. | Todas | Suite completa + verificación manual documentada. |

### Detalles técnicos (sin cambios de diseño)

- **Formato de placa y cédula en la base de datos:** Django no tiene `GLOB`. Registro un *lookup* personalizado `__glob` en `core`, para que `CheckConstraint` genere exactamente las restricciones `GLOB` del DDL aprobado. Además, los formularios validan el formato y muestran mensajes claros.
- **Concurrencia (RNF-003):** se prueba que la restricción de la base de datos rechaza la segunda estadía abierta y que el servicio convierte el `IntegrityError` en el mensaje de negocio. Una prueba con dos hilos reales sobre SQLite no es confiable, por eso **no** la presentaré como prueba de concurrencia real.
- **APScheduler:** se inicia desde `AppConfig.ready()` solo cuando el proceso es el servidor (`runserver`, una vez con la recarga automática) y nunca durante las pruebas ni las migraciones.
- **Credenciales de demostración:** se documentan en el README y se crean con el comando de demostración. Son solo para pruebas locales.
- **Nombres en el código:** en español, iguales a los diagramas aprobados (`ServicioEstadias`, `registrar_entrada`, …).

---

## 5. Estrategia de pruebas

| Tipo | Qué cubre |
|---|---|
| Unitarias | Métodos de dominio (`Celda.admite`, `Pago.cubre`, `Estadia.incluye`…), Reloj y correo simulado. |
| Integración (servicios + base de datos) | Cada regla RN implementada tiene al menos una prueba (RNF-008); restricciones de la base de datos. |
| Funcionales (vistas con el cliente de pruebas de Django) | Cada escenario Dado/Cuando/Entonces de HU-001 a HU-011, permisos por rol y "acceso denegado". |
| Regresión | La suite completa se ejecuta al final de cada paso. |
| Manual | Recorrido en el navegador con los datos de demostración, comparando con los mockups. |

Los resultados se informarán con números reales (pruebas ejecutadas, aprobadas y fallidas). Nada se dará por terminado sin ejecutar las pruebas.

---

## 6. Riesgos

| Riesgo | Mitigación |
|---|---|
| El planificador se ejecuta dos veces con la recarga automática | Protección en `ready()` + idempotencia + restricción única de la base de datos (doble barrera). |
| Errores de fechas (UTC frente a Bogotá, día 8 frente a día 9) | Todo se calcula con `Reloj` en hora local; pruebas con fechas fijas. |
| Diferencias entre las migraciones y el DDL aprobado | Prueba que repite las comprobaciones del DDL a través del ORM. |
| El proyecto está en OneDrive (bloqueo de `db.sqlite3` durante la sincronización) | Se documenta en el README; la base de datos no se sube a Git. |
| El servidor de desarrollo no es de producción | Limitación ya documentada en la arquitectura. |

---

## 7. Lo que se necesita del equipo

Solo la **aprobación de este plan**. No hay decisiones de diseño nuevas: las dependencias y sus versiones ya están cubiertas por DEC-005, DEC-008, DEC-010 y DEC-012. `tzdata` es una dependencia de Django en Windows.
