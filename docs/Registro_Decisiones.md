# Registro de decisiones — Parqueadero "Autos Colombia"

| ID | Tema | Estado |
|---|---|---|
| DEC-001 | Alcance del modelo de datos frente a la entrega por módulos | **Aprobada** |
| DEC-002 | Mecanismo de notificación al propietario (mensualidad vencida con el vehículo dentro) | **Aprobada** (B: correo automático) |
| DEC-003 | Tipo de aplicación | **Aprobada** (A: web local) |
| DEC-004 | Estilo arquitectónico | **Aprobada** (A: monolito modular en capas) |
| DEC-005 | Lenguaje, framework y forma de construir la interfaz | **Aprobada** (A: Python + Django, plantillas en el servidor) |
| DEC-006 | Motor de base de datos | **Aprobada** (A: SQLite) |
| DEC-007 | Envío de correo simulado (dummy) para la demostración | **Aprobada** (A: automático + botón, ambos simulados) |
| DEC-008 | Mecanismo del proceso diario de avisos | **Aprobada** (B: APScheduler; P-19 sí) |
| DEC-009 | Documentación LaTeX y herramienta de diagramas | **Aprobada** (estructura con 13 capítulos, MiKTeX, PlantUML local) |
| DEC-010 | Versiones de Python y Django | **Aprobada** (Django 5.2 LTS, Python 3.12 o superior) |
| DEC-011 | Creación de operadores por el administrador desde la iteración 1 | **Aprobada** (A) |
| DEC-012 | Algoritmo de hash de contraseñas | **Aprobada** (A: Argon2 con argon2-cffi) |
| DEC-013 | Registro de "qué operador hizo qué operación" (iteración 2) | **Aprobada** (B: bitácora de operaciones) |
| DEC-014 | Modelo de horarios y autorizaciones fuera de turno (iteración 2) | **Aprobada** (A: franjas por día + autorizaciones) |
| DEC-015 | Cambio de propietario con solicitud e historial (iteración 2) | **Aprobada** (A: solicitud + historial) |

---

## DEC-001 — Alcance del modelo de datos frente a la entrega por módulos

**Problema:** El módulo 1 (entrada y salida de vehículos) depende de datos que pertenecen a los módulos 2 (usuarios y celdas) y 3 (pagos): propietario del vehículo, vigencia de la mensualidad y celda asignada.

**Alternativas evaluadas:**

- **A.** Diseñar en el módulo 1 solo entidades mínimas (`Vehículo`, `Celda`) y ampliarlas en los módulos siguientes.
- **B.** Diseñar desde el inicio el modelo de datos completo del sistema e implementar únicamente la funcionalidad del módulo en curso.
- **C.** Implementar el módulo 1 sin validar la vigencia de la mensualidad y añadir esa validación en el módulo 3.

**Decisión seleccionada:** B. Diseñar desde el inicio el modelo de datos completo e implementar solo la funcionalidad de la iteración en curso.

**Justificación:** El dominio es pequeño, el modelo completo cabe en pocas entidades y así se evita rediseñar el MER en cada módulo. La documentación y el código avanzan módulo por módulo.

**Fecha:** 2026-11-15

**Responsable de aprobación:** Equipo del proyecto.

**Artefactos afectados:** Requerimientos (se identifican los RF de todo el sistema; se detallan los del módulo 1), MER, modelo relacional y modelo físico.

**Estado:** Aprobada.

---

## DEC-002 — Mecanismo de notificación al propietario

**Problema:** RN-11 dice que, si la mensualidad vence con el vehículo dentro, se notifica al propietario. Falta definir quién envía esa notificación y por qué medio.

**Contexto:** Si la notificación es automática, el sistema depende de un servicio externo (correo o SMS). Eso afecta la arquitectura, la configuración y las pruebas.

**Alternativas:**

**A. Notificación manual registrada en el sistema**
- Cómo funciona: el sistema detecta el vencimiento (RF-009). El operador o el administrador avisa al propietario por teléfono, WhatsApp o en persona y registra la notificación con fecha y medio (RF-010). El sistema controla el plazo de 8 días (RF-011).
- Ventajas: no depende de servicios externos ni tiene costos. Es fácil de probar.
- Desventajas: depende de que el personal haga el aviso.

**B. Correo electrónico automático**
- Cómo funciona: el sistema envía un correo al propietario y registra el envío.
- Ventajas: no depende del personal.
- Desventajas: requiere un servidor SMTP o un proveedor de correo y credenciales. El correo del propietario pasa a ser obligatorio. Las pruebas son más complejas.

**C. SMS o WhatsApp automático**
- Cómo funciona: el sistema envía un mensaje al celular del propietario.
- Ventajas: tiene alto alcance.
- Desventajas: requiere un proveedor de pago y su API. Es la opción más compleja.

**Recomendación del arquitecto:** A para la iteración 1, porque cumple RN-11 y RN-12 sin dependencias externas. Se puede dejar B como mejora futura (Could), reutilizando el mismo registro de notificación.

**Impacto:** arquitectura (servicios externos), modelo de datos (registro de notificación), RF-010 y pruebas.

**Decisión seleccionada:** B. Correo electrónico automático. El equipo no eligió la recomendación del arquitecto (A).

**Justificación:** Decisión del equipo. El aviso no depende de que el personal lo haga.

**Fecha:** 2026-11-15

**Responsable de aprobación:** Equipo del proyecto.

**Consecuencias que hay que atender:**
- El correo del propietario es obligatorio (RF-101, iteración 2).
- Hace falta elegir un servicio o proveedor de correo y gestionar sus credenciales fuera del código. Es una decisión de arquitectura pendiente.
- Hace falta un proceso programado que detecte los vencimientos y envíe los correos. Es una decisión de arquitectura pendiente.
- Las pruebas usarán un servidor de correo simulado o un doble de prueba. No se enviarán correos reales.

**Artefactos afectados:** RF-010, RN-11, RNF-012, RNF-013, RF-101, arquitectura y modelo de datos.

**Estado:** Aprobada.

---

# Decisiones de arquitectura (Fase 3)

**Requerimientos que guían estas decisiones:**

| Requerimiento | Qué exige a la arquitectura |
|---|---|
| RNF-011, P-09 | Proyecto académico que corre en un equipo local y se instala siguiendo el README. |
| RNF-001, RNF-002 | Inicio de sesión, contraseñas con hash y dos roles (administrador y operador). |
| RNF-003 | Transacciones y restricciones de unicidad: un vehículo con una sola entrada abierta y una celda con un solo vehículo. |
| RNF-004, RNF-007 | Usuario y hora del servidor en cada registro, sin borrado; datos personales protegidos. |
| RNF-008 | Código organizado por módulos y pruebas automatizadas de las reglas de negocio. |
| DEC-002, RF-010, RNF-012, RNF-013 | Envío automático de correo, un proceso diario y credenciales fuera del código. |
| Proceso del equipo | Tres iteraciones que agregan módulos sobre la misma base. |

---

## DEC-003 — Tipo de aplicación

**Problema:** Hay que definir cómo usarán el sistema el administrador y los operadores.

**Alternativas:**

**A. Aplicación web local (cliente-servidor en el mismo equipo)**
- Cómo funciona: un servidor corre en el equipo y se usa desde el navegador en `localhost`.
- Ventajas: inicio de sesión y roles con soporte estándar de los frameworks; interfaz con HTML; el proceso diario de correo encaja bien; si más adelante se quiere usar desde otro equipo de la red, la arquitectura no cambia.
- Desventajas: hay que levantar un servidor local para usarla.

**B. Aplicación de escritorio**
- Ejemplos: JavaFX, WinForms o Tkinter.
- Ventajas: no necesita navegador.
- Desventajas: los roles, el inicio de sesión y el proceso programado se hacen más a mano; la interfaz cuesta más; queda atada al equipo.

**C. Aplicación de consola**
- Ventajas: es la más simple.
- Desventajas: mala usabilidad para el operador (RNF-005); poco presentable en un proyecto académico.

**Recomendación del arquitecto:** A.

**Impacto:** define DEC-004 y DEC-005, y el diagrama de despliegue.

**Decisión seleccionada:** A. Aplicación web local (cliente-servidor en el mismo equipo, usada desde el navegador).

**Justificación:** El equipo aceptó la recomendación del arquitecto. El curso no exige ningún lenguaje ni framework (P-18). El sistema se ejecutará en local, y el profesor también lo ejecutará y probará en su propia máquina.

**Fecha:** 2026-11-15

**Responsable de aprobación:** Equipo del proyecto.

**Estado:** Aprobada.

---

## DEC-004 — Estilo arquitectónico

**Problema:** Hay que organizar el código para que crezca en tres iteraciones sin rehacerse.

**Alternativas:**

**A. Monolito modular en capas**
- Cómo funciona: una sola aplicación, dividida en módulos funcionales (`entradas_salidas`, `novedades`, `usuarios_celdas`, `pagos`, `notificaciones`). Cada módulo tiene tres capas: **presentación** (vistas y formularios), **lógica de negocio** (servicios con las reglas RN) y **acceso a datos** (modelos y repositorios).
- Ventajas: cada iteración agrega un módulo; las reglas de negocio quedan aisladas y se pueden probar (RNF-008); es simple de ejecutar en local.
- Desventajas: exige disciplina para no saltarse capas.

**B. Arquitectura hexagonal (puertos y adaptadores)**
- Ventajas: el dominio queda totalmente independiente del framework y de la base de datos.
- Desventajas: más interfaces y más código; es desproporcionada para el tamaño del proyecto.

**C. Microservicios**
- Desventajas: varios servicios, comunicación por red y despliegue complejo. No hay ningún requerimiento que lo justifique.

**Recomendación del arquitecto:** A. Del estilo hexagonal se toma una sola idea: el envío de correo va detrás de una interfaz, para poder simularlo en las pruebas y cambiar de proveedor sin tocar la lógica de negocio.

**Impacto:** diagrama de paquetes, diagrama de clases y estructura de carpetas del Ingeniero.

**Decisión seleccionada:** A. Monolito modular en capas (presentación, lógica de negocio y acceso a datos).

**Justificación:** El equipo aceptó la recomendación del arquitecto. El curso no exige ningún lenguaje ni framework (P-18). El sistema se ejecutará en local, y el profesor también lo ejecutará y probará en su propia máquina.

**Fecha:** 2026-11-15

**Responsable de aprobación:** Equipo del proyecto.

**Estado:** Aprobada.

---

## DEC-005 — Lenguaje, framework y forma de construir la interfaz

**Problema:** Hay que elegir la tecnología de implementación. Depende de DEC-003 y de lo que el equipo sepa o el curso exija (P-18).

**Alternativas:**

**A. Python + Django, con plantillas renderizadas en el servidor**
- Ventajas: trae inicio de sesión, grupos y permisos (roles), hash de contraseñas, ORM con transacciones y restricciones, migraciones versionadas, protección CSRF, sistema de correo configurable y un backend de correo en memoria para pruebas, y un framework de pruebas integrado. Es el que menos piezas externas necesita para cumplir los RNF.
- Desventajas: el tipado es opcional (type hints); hay que conocer las convenciones de Django.

**B. Java + Spring Boot, con plantillas Thymeleaf**
- Ventajas: tipado fuerte; las clases corresponden de forma directa al diagrama UML; es muy usado en cursos de Ingeniería de Software. Spring Security, Spring Data JPA, JavaMail y `@Scheduled` cubren los RNF.
- Desventajas: más configuración y más código; los tiempos de arranque y compilación son mayores.

**C. JavaScript/TypeScript + Node.js (Express o NestJS)**
- Ventajas: un solo lenguaje si se hace una interfaz SPA.
- Desventajas: la autenticación, los roles, el ORM y las migraciones salen de bibliotecas separadas que hay que elegir e integrar; hay más decisiones y dependencias.

**D. C# + ASP.NET Core MVC**
- Ventajas: tipado fuerte; Identity cubre usuarios y roles; Entity Framework cubre datos y migraciones.
- Desventajas: más ligado al ecosistema .NET y a Visual Studio.

**Sobre la interfaz:** se recomienda renderizar en el servidor (plantillas HTML), sin una SPA separada. Una SPA agrega un segundo proyecto, una API y autenticación por tokens, y ningún requerimiento lo pide.

**Recomendación del arquitecto:** A (Django), **siempre que el curso no exija otro lenguaje y el equipo no domine mejor otro stack**. Si el curso pide Java o el equipo lo conoce mejor, la recomendación cambia a B.

**Impacto:** todo el código, las pruebas, el README, el diagrama de clases (tipos de datos) y el modelo físico.

**Decisión seleccionada:** A. Python + Django, con plantillas HTML renderizadas en el servidor.

**Justificación:** El equipo aceptó la recomendación del arquitecto. El curso no exige ningún lenguaje ni framework (P-18). El sistema se ejecutará en local, y el profesor también lo ejecutará y probará en su propia máquina.

**Fecha:** 2026-11-15

**Responsable de aprobación:** Equipo del proyecto.

**Estado:** Aprobada.

---

## DEC-006 — Motor de base de datos

**Problema:** Hay que elegir el motor relacional para el modelo físico.

**Alternativas:**

**A. SQLite**
- Ventajas: no requiere instalación, porque la base de datos es un archivo; es lo más portable (RNF-011); soporta transacciones, claves foráneas, CHECK e índices únicos parciales (necesarios para "una sola entrada abierta por vehículo", RN-04).
- Desventajas: las escrituras se serializan (suficiente para un parqueadero en un solo equipo); el tipado de columnas es flexible, así que el modelo físico documenta tipos que el motor no impone de forma estricta.

**B. PostgreSQL**
- Ventajas: motor robusto; tipado estricto; concurrencia real; restricciones e índices parciales completos; es el estándar en la industria.
- Desventajas: cada integrante debe instalarlo y configurarlo, lo que complica RNF-011.

**C. MySQL / MariaDB**
- Ventajas: muy conocido; también se instala por separado.
- Desventajas: las mismas de PostgreSQL en cuanto a instalación; el soporte de índices únicos parciales es más limitado, así que RN-04 requeriría otra técnica.

**Recomendación del arquitecto:** A (SQLite), por la ejecución local y académica. Si se aprueba DEC-005 A o B, el ORM permite pasar a PostgreSQL después cambiando solo la configuración, siempre que el modelo use tipos y restricciones estándar.

**Impacto:** modelo físico, scripts DDL, README e instalación.

**Decisión seleccionada:** A. SQLite.

**Justificación:** El equipo aceptó la recomendación del arquitecto. El curso no exige ningún lenguaje ni framework (P-18). El sistema se ejecutará en local, y el profesor también lo ejecutará y probará en su propia máquina.

**Fecha:** 2026-11-15

**Responsable de aprobación:** Equipo del proyecto.

**Estado:** Aprobada.

---


---

# Decisiones que dependen del stack

**Nuevo contexto (2026-11-15):** el profesor ejecutará y probará el sistema en su propia máquina. Por eso:
- el sistema debe funcionar **sin credenciales privadas** del equipo (RNF-012 prohíbe incluirlas en el repositorio);
- la instalación debe ser corta y estar documentada (RNF-011);
- el profesor necesita **datos de demostración** para probar los escenarios (ver la solicitud de cambio CHG-001 en `ESTADO_PROYECTO.md`).

**Herramientas encontradas en el equipo de desarrollo:** Python 3.14.2, Git 2.52, Java 25, MiKTeX con pdfLaTeX, LuaLaTeX y latexmk. No están instalados PlantUML ni Graphviz.

---

## DEC-007 — Envío de correo: simulado para la demostración

**Historial:** se propuso el 2026-11-15 con un envío configurable y SMTP externo. El mismo día se replanteó por una indicación del equipo.

**Indicación del equipo (2026-11-15):** el correo es un **dummy**. Debe haber un **botón para que el operador o el administrador envíen el correo**. No tiene que enviarlo de verdad; está ahí para la demostración. No se necesita un servidor de correo real.

**Conflicto detectado:** DEC-002 (aprobada) y RF-010 (aprobado) dicen que el correo se envía **automáticamente**, y DEC-008 (aprobada) programa ese proceso con APScheduler. Un botón manual cambia ese comportamiento, así que hay que elegir cómo se combinan.

**Alternativas:**

**A. Proceso automático simulado + botón manual simulado**
- Cómo funciona: APScheduler sigue detectando los vencimientos (DEC-008), y el "envío" se **simula**: no sale ningún correo, el sistema guarda el envío como **"simulado"** con la fecha, el destinatario y el texto, y lo muestra en pantalla. Además, en la lista de RF-009 hay un botón **"Enviar correo"** para que el operador o el administrador lo disparen a mano (también simulado), útil para mostrarlo en la demostración.
- Ventajas: respeta DEC-002, RF-010 y DEC-008 tal como se aprobaron, y agrega el botón. El envío queda detrás de una interfaz (DEC-004), así que más adelante se puede conectar un servidor real sin tocar la lógica de negocio.
- Desventajas: además de RF-010 hay que implementar el botón, que es un RF nuevo pequeño (RF-012).

**B. Solo el botón manual simulado**
- Cómo funciona: no hay proceso automático. El sistema muestra los vencidos y el personal pulsa el botón.
- Ventajas: es lo más simple.
- Desventajas: **anula** DEC-002 (automático) y vuelve innecesaria DEC-008 (APScheduler), recién aprobada; hay que modificar RN-11 y RF-010.

**Recomendación del arquitecto:** A.

**Consecuencias de A:**
- RNF-012 (credenciales de correo fuera del código) no se aplica por ahora, porque no hay credenciales; se mantiene para cuando se use un servidor real.
- RNF-013 se cumple con la simulación.
- RF-012 (nuevo): botón "Enviar correo" en RF-009 para el operador y el administrador. Registra un envío simulado y respeta la regla de un solo correo por vencimiento. Hay que definir qué pasa si ya se envió uno (P-20).

**Impacto:** RF-010, nuevo RF-012, HU-007 y HU-008, pruebas, mockups.

**Decisión seleccionada:** A. El proceso automático (APScheduler) y el botón manual "Enviar correo" existen los dos, y ambos **simulan** el envío: no sale ningún correo real.

**Justificación:** Decisión del equipo. El correo sirve para la demostración y no necesita funcionar de verdad.

**Fecha:** 2026-11-15

**Responsable de aprobación:** Equipo del proyecto.

**Artefactos afectados:** RF-010 (envío simulado), nuevo RF-012 (botón), HU-011 (borrador), Requerimientos v2.7.

**Pendiente derivado:** P-20 (qué hace el botón si ya se envió el correo de ese vencimiento).

**Estado:** Aprobada.

---

## DEC-008 — Mecanismo del proceso diario de avisos

**Problema:** RF-010 necesita revisar los vencimientos y enviar los correos sin que nadie lo dispare a mano.

**Contexto agregado (2026-11-15):** el equipo indicó que el programa **se mantendría activo 24/7**. Eso hace viable un planificador dentro de la aplicación, que antes descartaba.

**Base común de todas las alternativas:** la lógica vive en un servicio y en un comando de Django (`python manage.py enviar_avisos_vencimiento`). Es **idempotente**: si se ejecuta varias veces, nunca envía dos correos por el mismo vencimiento.

**Alternativas:**

**A. Programador de tareas de Windows**
- Cómo funciona: ejecuta el comando todos los días.
- Ventajas: no depende de que la aplicación esté abierta.
- Desventajas: hay que configurarlo en cada equipo, incluido el del profesor; depende del sistema operativo.

**B. Planificador dentro de la aplicación con APScheduler (biblioteca mantenida, licencia MIT)**
- Cómo funciona: mientras el servidor está activo, ejecuta el proceso **al iniciar** y luego **cada hora**.
- Ventajas: automático de verdad con el servidor 24/7; en la máquina del profesor funciona sin configurar nada.
- Desventajas: agrega una dependencia; hay que evitar que se inicie dos veces con la recarga automática del modo desarrollo (se controla en el código y se prueba).

**C. Hilo propio en segundo plano**
- Igual que B, pero sin dependencia.
- Desventajas: es un mecanismo hecho a mano, con más riesgo de errores de concurrencia.

**D. Verificación en el primer uso del día**
- Desventajas: depende de que alguien use el sistema. Con el servidor 24/7 ya no es la mejor opción.

**Recomendación del arquitecto (actualizada):** B. Como corre al iniciar y cada hora, el correo sale el mismo día del vencimiento mientras el servidor esté activo.

**Regla que hay que confirmar (P-19):** si el servidor estuvo apagado el día del vencimiento, al encenderse se envía el correo pendiente, siempre que el vehículo siga dentro y sin pagar. El registro guarda la fecha real de envío y el plazo de 8 días se sigue contando desde el vencimiento (RN-12).

**Impacto:** RF-010, RN-11, una dependencia nueva, pruebas y README.

**Decisión seleccionada:** B. APScheduler, que ejecuta el proceso al iniciar el servidor y cada hora.

**Justificación:** El equipo aceptó la recomendación.

**Fecha:** 2026-11-15

**Responsable de aprobación:** Equipo del proyecto.

**P-19 resuelta:** si el servidor estuvo apagado el día del vencimiento, el correo pendiente se envía al encenderlo, siempre que el vehículo siga dentro y sin pagar. El plazo de 8 días se sigue contando desde el vencimiento.

**Nota:** cómo funciona el "envío" depende de DEC-007, que se replanteó y está pendiente.

**Estado:** Aprobada.

---

## DEC-009 — Documentación LaTeX y herramienta de diagramas

**Problema:** Hay que definir el documento técnico (contenido y compilación) y la herramienta para generar los diagramas y los mockups.

**Parte 1 — Contenido obligatorio del PDF (indicado por el equipo el 2026-11-15):** portada, introducción, entregables, arquitectura del sistema, historias de usuario, mockups de las historias, MER, modelo relacional (MR), modelo físico, diagramas de casos de uso, diagrama de clases, diagrama de paquetes y conclusiones.

**Estructura propuesta**, que cubre ese contenido y agrega los requerimientos y las decisiones, ya aprobados, para la trazabilidad:

```
docs/latex/
├── main.tex
├── config/            paquetes.tex, comandos.tex, formato.tex
├── chapters/
│   ├── 00-portada.tex
│   ├── 01-introduccion.tex
│   ├── 02-entregables.tex
│   ├── 03-requerimientos.tex        (RF, RNF, RN; propuesto)
│   ├── 04-arquitectura.tex          (decisiones, capas, contexto, despliegue)
│   ├── 05-historias-usuario.tex
│   ├── 06-mockups.tex
│   ├── 07-modelo-datos.tex          (MER, MR, modelo físico)
│   ├── 08-casos-uso.tex
│   ├── 09-diagrama-clases.tex
│   ├── 10-diagrama-paquetes.tex
│   ├── 11-decisiones.tex            (registro DEC; propuesto)
│   └── 12-conclusiones.tex
└── diagrams/          .puml fuente + .png/.pdf generados
```

- **Compilación:** local con MiKTeX, que ya está instalado (confirmado por el equipo), usando **latexmk + pdfLaTeX**.
- Cada iteración agrega su contenido a los mismos capítulos.

**Parte 2 — Herramienta de diagramas y mockups:**

**A. PlantUML local (`plantuml.jar`, con el Java 25 que ya está instalado)**
- Ventajas: una sola herramienta para casos de uso, clases, paquetes, componentes, MER y **mockups** (PlantUML tiene un modo de wireframes llamado *Salt*). Funciona sin internet y todo sale de archivos de texto.
- Desventajas: requiere **descargar `plantuml.jar`** (unos 25 MB) del repositorio oficial de PlantUML en GitHub. Sin Graphviz se usa el motor de diseño integrado.

**B. Dibujar en LaTeX con TikZ**
- Ventajas: no se descarga nada; MiKTeX instala los paquetes.
- Desventajas: mucho más trabajo y más difícil de mantener, sobre todo los diagramas de clases y los mockups.

**C. Servidor web público de PlantUML**
- Desventajas: envía el texto de los diagramas a un servidor externo y depende de internet.

**Recomendación del arquitecto:** estructura propuesta + A.

**Aprobado hasta ahora:** el contenido del PDF (lo definió el equipo) y la compilación local con MiKTeX.

**Pendiente:** la autorización para descargar `plantuml.jar`, la inclusión de los capítulos 03 y 11 propuestos, y los datos de la portada (P-21).

**Decisión seleccionada:** estructura propuesta, **incluidos** los capítulos 03 (requerimientos) y 11 (registro de decisiones), compilación local con MiKTeX (latexmk + pdfLaTeX) y **PlantUML local (alternativa A)** para diagramas, MER y mockups (Salt). El equipo autorizó usar PlantUML, lo que incluye descargar `plantuml.jar` a `tools/`.

**Fecha:** 2026-11-15

**Responsable de aprobación:** Equipo del proyecto.

**Pendiente derivado:** P-21 (datos de la portada).

**Estado:** Aprobada.

---

## DEC-010 — Versiones de Python y Django

**Datos verificados el 2026-11-15** en la documentación oficial de Django (djangoproject.com/download y FAQ de instalación):
- Django **5.2 LTS** (última: 5.2.19): soporte extendido hasta **abril de 2028**; es compatible con Python 3.10 a 3.14 (Python 3.14 desde la 5.2.8).
- Django **6.1** (última: 6.1.3): soporte hasta diciembre de 2027; requiere Python 3.12 o superior.

**Alternativas:**

**A. Django 5.2 LTS, Python 3.12 o superior (probado con 3.14)**
- Ventajas: es la versión con el soporte más largo y la más estable; funciona con la versión de Python que el profesor probablemente tenga.
- Desventajas: no tiene las funciones más nuevas de 6.x, que este proyecto no necesita.

**B. Django 6.1, Python 3.12 o superior**
- Ventajas: es la más reciente.
- Desventajas: menos tiempo de soporte; no aporta nada que el proyecto requiera.

**Recomendación del arquitecto:** A. Las versiones exactas se fijan en `requirements.txt`.

**Impacto:** instalación, README y compatibilidad en la máquina del profesor.

**Decisión seleccionada:** A. Django 5.2 LTS con Python 3.12 o superior (probado con 3.14).

**Justificación:** El equipo aceptó la recomendación.

**Fecha:** 2026-11-15

**Responsable de aprobación:** Equipo del proyecto.

**Estado:** Aprobada.

---

## DEC-011 — Creación de operadores por el administrador desde la iteración 1

**Problema:** El equipo indicó (2026-11-15) que el administrador debe poder **crear operadores nuevos**. En los requerimientos aprobados eso es RF-106, que pertenece a la **iteración 2**. Hay que decidir si se adelanta.

**Contexto:** En la iteración 1 ya existen los dos roles y sus usuarios de prueba (RNF-014). Lo que falta es la función que permite al administrador crear más operadores.

**Alternativas:**

**A. Adelantar a la iteración 1 una versión básica de RF-106, con pantalla propia**
- Cómo funciona: el administrador crea un operador con nombre, usuario y contraseña, y puede activarlo o desactivarlo. Los horarios (RF-107) se quedan en la iteración 2.
- Ventajas: la capacidad existe desde la primera entrega; respeta los roles (RNF-002) y la regla de no borrar (RN-07), porque se desactiva en lugar de eliminar.
- Desventajas: agrega una historia (HU-010) y un poco más de trabajo a la iteración 1.

**B. Usar el panel de administración que trae Django (`/admin`)**
- Ventajas: casi no requiere código.
- Desventajas: es una herramienta para desarrolladores; muestra las tablas sin filtro y permite **borrar registros**, lo que va en contra de RN-07, salvo que se configure con cuidado; la interfaz no es coherente con el resto de la aplicación.

**C. Dejarlo en la iteración 2, como estaba**
- Ventajas: no cambia el alcance aprobado.
- Desventajas: en la iteración 1 solo existirían los usuarios de prueba.

**Recomendación del arquitecto:** A.

**Impacto:** Requerimientos (RF-106 pasa a la iteración 1 en su versión básica), historias de usuario (nueva HU-010), modelo de datos (sin cambios, porque el usuario y el rol ya están en el MER completo) y pruebas.

**Decisión seleccionada:** A. Se adelanta a la iteración 1 una versión básica de RF-106: el administrador crea operadores y los activa o desactiva, con pantalla propia. Los horarios (RF-107) se quedan en la iteración 2.

**Justificación:** El equipo eligió la opción A.

**Fecha:** 2026-11-15

**Responsable de aprobación:** Equipo del proyecto.

**Artefactos afectados:** Requerimientos v2.6 (RF-106 se detalla en la iteración 1) y nueva HU-010 (pendiente de aprobación).

**Estado:** Aprobada.

---

## DEC-012 — Algoritmo de hash de contraseñas

**Problema:** RNF-001 (aprobado) exige bcrypt o Argon2, pero Django usa PBKDF2 por defecto. Se detectó al redactar el documento de arquitectura.

**Alternativas:**
- **A.** Argon2 con `argon2-cffi`, soportado oficialmente por Django. Cumple RNF-001 sin cambios y agrega una dependencia pequeña.
- **B.** PBKDF2, el algoritmo por defecto de Django. Sin dependencias, pero obliga a modificar RNF-001.

**Recomendación del arquitecto:** A.

**Decisión seleccionada:** A. Argon2 como algoritmo principal (`PASSWORD_HASHERS` con `Argon2PasswordHasher` en primer lugar).

**Justificación:** Respeta RNF-001 tal como se aprobó. El equipo aceptó la recomendación.

**Fecha:** 2026-11-15

**Responsable de aprobación:** Equipo del proyecto.

**Artefactos afectados:** Arquitectura v1 (7.1, 9), `requirements.txt`.

**Estado:** Aprobada.

---

# Decisiones de la iteración 2

Las alternativas completas están en `Requerimientos_Iteracion2_v1.md`, sección 5.

## DEC-013 — Registro de "qué operador hizo qué operación"

**Problema:** P-32 pide mostrar qué operador hizo cada operación (RNF-004, RN-34).

**Alternativas:** A. Columnas `creado_por` / `modificado_por` en cada tabla (solo la última modificación). B. Bitácora de operaciones (usuario, fecha y hora, acción, entidad, identificador y detalle de los cambios).

**Recomendación del arquitecto:** B.

**Decisión seleccionada:** B. Bitácora de operaciones.

**Justificación:** Guarda todas las operaciones y permite mostrarlas por usuario, vehículo o propietario. El equipo aceptó la recomendación.

**Fecha:** 2026-11-15

**Responsable de aprobación:** Equipo del proyecto.

**Artefactos afectados:** RF-111, modelo de datos (v1.3: nueva tabla de bitácora).

**Estado:** Aprobada.

## DEC-014 — Modelo de horarios y autorizaciones fuera de turno

**Problema:** P-27, P-34, P-35 y P-37 definen turnos fijos, turnos nocturnos, varias franjas por día y autorizaciones del administrador.

**Alternativas:** A. Franjas por día de la semana (`HorarioOperador`, que puede cruzar la medianoche) más una tabla de autorizaciones fuera de turno. B. Turnos con nombre y horas fijas.

**Recomendación del arquitecto:** A.

**Decisión seleccionada:** A.

**Justificación:** Es flexible: admite varias franjas por día (P-37) y turnos nocturnos (P-35), y reutiliza la tabla que ya existe. El nombre del turno se calcula para el encabezado. El equipo aceptó la recomendación.

**Fecha:** 2026-11-15

**Responsable de aprobación:** Equipo del proyecto.

**Artefactos afectados:** RF-107, RF-110, RN-31, RN-32, RN-35, RN-36, modelo de datos (v1.3: `HorarioOperador` deja de ser provisional y se agrega la tabla de autorizaciones).

**Estado:** Aprobada.

## DEC-015 — Cambio de propietario con solicitud e historial

**Problema:** P-29: el cambio de propietario se pide al administrador y debe quedar el registro del propietario anterior.

**Alternativas:** A. Tabla de solicitudes (pendiente, aprobada o rechazada) más tabla de historial de propietarios. B. Solo el historial; el administrador hace el cambio directamente.

**Recomendación del arquitecto:** A.

**Decisión seleccionada:** A.

**Justificación:** Cumple con que la petición pase por el administrador y conserva el historial. El equipo aceptó la recomendación.

**Fecha:** 2026-11-15

**Responsable de aprobación:** Equipo del proyecto.

**Artefactos afectados:** RF-108, RF-109, RN-33, modelo de datos (v1.3: dos tablas nuevas).

**Estado:** Aprobada.
