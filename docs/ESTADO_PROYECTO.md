# Estado del proyecto — Parqueadero "Autos Colombia"

**Última actualización:** 2026-11-15

## Objetivo
Software para la operación diaria de un parqueadero por mensualidad: entradas y salidas de vehículos, novedades, usuarios, celdas y pagos.

## Proceso de trabajo (definido por el equipo)
Se avanza paso a paso, por iteraciones:
1. **Iteración 1:** Gestión de la entrada y salida de vehículos (incluye novedades).
2. **Iteración 2:** Gestión de usuarios y celdas.
3. **Iteración 3:** Gestión de pagos.

En cada iteración: documentación y diagramas (Arquitecto) → código (Ingeniero) → commit a GitHub.

## Fase actual
Iteración 1 cerrada y subida a GitHub (2026-11-15). **Iteración 2 (gestión de usuarios y celdas):** requerimientos (v1.4) e historias HU-012 a HU-023 aprobados; modelo de datos v1.3 aprobado (DDL 60/60). **Diseño de la iteración 2 aprobado** e incorporado al PDF (114 páginas). Siguiente: plan de implementación del Ingeniero.

## Artefactos
| Artefacto | Archivo | Estado |
|---|---|---|
| Requerimientos v1 | docs/Requerimientos_v1.md | Sustituido por v2 (se conserva como historial) |
| Requerimientos v2.10 (iteración 1) | docs/Requerimientos_v2.md | **Aprobado** (2026-11-15; v2.5 = RNF-014, v2.6 = RF-106 básico y RN-21, v2.7 = correo simulado y RF-012, v2.8 = RN-22 por P-20, v2.9 = un solo reenvío, v2.10 = RN-23 y datos de propietario y vehículo) |
| Historias de usuario v1 (iteración 1) | docs/Historias_Usuario_v1.md | HU-001 a HU-011 **Aprobadas** (2026-11-15) |
| .gitignore | .gitignore | Creado |
| PlantUML 1.2026.10 | tools/plantuml.jar (no se versiona) | Descargado del repositorio oficial y verificado (diagrama de clases con Smetana y mockup Salt) |
| Registro de decisiones | docs/Registro_Decisiones.md | En uso |
| Arquitectura v1 | docs/Arquitectura_v1.md + docs/latex/diagrams/arquitectura/ARQ-01 a ARQ-05 | **Aprobado** (2026-11-15) |
| Modelo de datos v1.1 | docs/Modelo_Datos_v1.md + diagrams/datos (MER-01, MR-01) + docs/sql/ddl_sqlite_v1.sql + validar_ddl.py (42/42) | **Aprobado** (2026-11-15) |
| Diseño UML v1 | docs/Diseno_UML_v1.md + diagrams/uml (UC-01, CL-01, CL-02, PK-01) | **Aprobado** (2026-11-15) |
| Mockups v1 | docs/Mockups_v1.md + diagrams/mockups (M-01 a M-12) | **Aprobado** (2026-11-15) |
| Plan de implementación (iteración 1) | docs/Plan_Implementacion_Iteracion1.md | **Aprobado** (2026-11-15) |
| Código de la iteración 1 (pasos 1-8) | src/ + requirements.txt + README.md | Implementado y probado: 100/100 pruebas |
| Informe de implementación | docs/Informe_Implementacion_Iteracion1.md | Hecho |
| Requerimientos iteración 2 v1.4 | docs/Requerimientos_Iteracion2_v1.md | **Aprobado** (2026-11-15; v1.4 = aclaraciones de RN-35, RN-37 y del turno en el encabezado) |
| Historias de usuario iteración 2 v1.1 | docs/Historias_Usuario_Iteracion2_v1.md | **Aprobado** (2026-11-15) |
| Modelo de datos v1.3 (iteración 2) | docs/Modelo_Datos_v1.md §7 + DDL v1.3 + MER-01/MR-01 | **Aprobado** (2026-11-15; incluye DM-08: nuevo módulo `bitacora`) |
| Diseño iteración 2 v1 | docs/Diseno_Iteracion2_v1.md + diagrams (mockups M-13 a M-25, uml UC-02/CL-03/CL-04/PK-01 v2, arquitectura ARQ-03 v2) | **Aprobado** (2026-11-15) |
| Referencias de interfaz | docs/referencias_ui/ + docs/Analisis_Referencias_UI.md | CHG-002 **aprobado** (2026-11-15) |
| Documento LaTeX | docs/latex/main.tex → main.pdf (capítulos 03, 05 y 11 generados con scripts/generar_capitulos.py) | **Completo** para la iteración 1 (83 páginas, incluye conclusiones) |

## Decisiones
| ID | Decisión | Estado |
|---|---|---|
| DEC-001 | Modelo de datos completo desde el inicio; implementación por iteración (alternativa B) | Aprobada (2026-11-15) |
| DEC-002 | Notificación al propietario por correo automático (alternativa B) | Aprobada (2026-11-15) |
| DEC-003 | Aplicación web local | Aprobada (2026-11-15) |
| DEC-004 | Monolito modular en capas | Aprobada (2026-11-15) |
| DEC-005 | Python + Django, plantillas en el servidor | Aprobada (2026-11-15) |
| DEC-006 | SQLite | Aprobada (2026-11-15) |
| DEC-007 | Correo simulado (dummy): proceso automático + botón "Enviar correo" | Aprobada (2026-11-15) |
| DEC-008 | Proceso diario con APScheduler (al iniciar y cada hora); P-19 sí | Aprobada (2026-11-15) |
| DEC-009 | LaTeX (13 capítulos, incluye requerimientos y decisiones) + MiKTeX + PlantUML local | Aprobada (2026-11-15) |
| DEC-010 | Django 5.2 LTS + Python 3.12 o superior | Aprobada (2026-11-15) |
| DEC-011 | Creación de operadores (RF-106 básico) en la iteración 1 | Aprobada (2026-11-15) |
| DEC-012 | Hash de contraseñas: Argon2 (argon2-cffi) | Aprobada (2026-11-15) |
| DEC-013 | Bitácora de operaciones | Aprobada (2026-11-15) |
| DEC-014 | Horarios por franjas (con turnos nocturnos) + autorizaciones fuera de turno | Aprobada (2026-11-15) |
| DEC-015 | Cambio de propietario con solicitud e historial | Aprobada (2026-11-15) |

## Información dada por el equipo
- El servicio es solo por mensualidad. La mensualidad se paga por vehículo (carro/camioneta 150 000 COP; moto 80 000 COP).
- Se admiten motos, carros y camionetas. Hay dos tipos de celda: 150 de carro/camioneta y 50 de moto (por el momento). Operación 24 horas.
- Proyecto académico que se ejecuta en local. El profesor lo ejecutará y probará en su máquina. El curso no exige ningún lenguaje. El programa se mantendría activo 24/7. El correo es un dummy de demostración: un botón para enviarlo que no necesita funcionar de verdad.
- Se necesitan un administrador y un operador de prueba (CHG-001 aprobado → RNF-014). El administrador debe poder crear operadores nuevos (DEC-011, aprobada).
- El PDF LaTeX debe incluir: portada, introducción, entregables, arquitectura, historias de usuario, mockups, MER, MR, modelo físico, casos de uso, diagrama de clases, diagrama de paquetes y conclusiones.
- Al terminar cada fase se entregan los comandos de Git (commit y push) para que el equipo los ejecute.
- El vehículo toma cualquier celda libre de su tipo; el operador registra la celda y puede consultar si una celda está ocupada y por quién.
- Solo pueden estar dentro los vehículos con la mensualidad pagada.
- Si la mensualidad vence con el vehículo dentro, se notifica al propietario. Si sigue dentro en el día vencimiento + 8 (por ejemplo, vence el 1 y se marca el 9), el administrador (solo él) contacta a las autoridades.
- Los 8 días se cuentan desde el vencimiento de la mensualidad. Se envía un solo correo automático el día del vencimiento: debe pagar para mantener el vehículo o habrá consecuencias.
- Correo de retiro: el primero (automático o manual) y como máximo un reenvío con confirmación (RN-22).
- Un vehículo con la mensualidad vencida puede salir, pero no vuelve a entrar mientras no pague.
- Propietario: nombre completo, cédula, teléfono, correo y dirección. Vehículo: placa (ABC123 / ABC12D / ABC12), tipo, marca, nombre, modelo y color.
- Al registrar una novedad, el sistema verifica que todos los vehículos involucrados estaban dentro a la hora del hecho.
- Si el propietario paga dentro de los 8 días, el vehículo sale del proceso de retiro.
- Las novedades no llevan fotos ni adjuntos en esta versión.
- Las novedades solo se registran si el hecho ocurrió dentro de las instalaciones. Tienen un identificador propio, pueden vincular varios vehículos, se pueden registrar después de la salida y no tienen estado (son solo documentación).
- Roles: Administrador (acceso total, crea operadores y les asigna horario) y Operador (registra clientes y pagos, consulta vehículos y mensualidades).

## Datos de la portada (P-21, dados por el equipo el 2026-11-15)
- Institución: IU Digital (confirmado por el equipo).
- Asignatura: Ingeniería de Software. Profesor: Reinaldo Rojas Lopez.
- Integrantes: Juan Sebastian Lopez Gallo y Andres Miguel Hernandez.
- Fecha: la actual. Semestre: sexto.

## Pendientes
- Iteración 2: plan de implementación (Ingeniero).
- Iteración 3 (pendiente anotado): motivo de inactivación y reactivación automática al registrar el pago (P-33).
- Revisión del primer PDF LaTeX.

## Próximas actividades
1. ~~Aprobar los requerimientos de la iteración 1~~ (hecho 2026-11-15).
2. ~~Aprobar las historias de usuario de la iteración 1~~ (hecho 2026-11-15).
3. ~~Aprobar la arquitectura v1~~ (hecho 2026-11-15).
4. ~~Crear el documento LaTeX inicial~~ (hecho 2026-11-15; pendiente la revisión del equipo).
5. ~~Aprobar el modelo de datos e incorporarlo al capítulo 7~~ (hecho 2026-11-15).
6. ~~Aprobar UML y mockups e incorporarlos al PDF~~ (hecho 2026-11-15).
7. ~~Implementación (Ingeniero)~~ (hecho 2026-11-15: 100/100 pruebas).
8. ~~Conclusiones (capítulo 12)~~ (hecho 2026-11-15).
9. Iteración 2: gestión de usuarios y celdas (en análisis).
10. Iteración 3: gestión de pagos.
