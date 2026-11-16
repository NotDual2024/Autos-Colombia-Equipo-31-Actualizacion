# Parqueadero "Autos Colombia"

Sistema web local para la gestión de un parqueadero por mensualidad: entradas y salidas de vehículos, novedades, avisos de vencimiento (simulados), propietarios, vehículos, celdas, operadores con horarios y bitácora de operaciones.

Proyecto académico de Ingeniería de Software (IU Digital). **Iteración 1:** gestión de la entrada y salida de vehículos. **Iteración 2:** gestión de usuarios y celdas.

- Documentación técnica completa: [`docs/latex/main.pdf`](docs/latex/main.pdf)
- Requerimientos, decisiones y diseño: carpeta [`docs/`](docs/)

## Requisitos

- **Python 3.12 o superior** (probado con 3.14.2)
- Windows, Linux o macOS. No se necesita ningún otro servicio: la base de datos es SQLite y el correo es simulado.

## Instalación

Desde la carpeta raíz del proyecto:

```bash
python -m venv .venv
```

Activar el entorno virtual:

- Windows (PowerShell): `.venv\Scripts\Activate.ps1`
- Windows (Git Bash): `source .venv/Scripts/activate`
- Linux / macOS: `source .venv/bin/activate`

```bash
pip install -r requirements.txt
```

```bash
cd src
python manage.py migrate
python manage.py cargar_datos_demo
```

## Ejecución

```bash
cd src
python manage.py runserver
```

Abrir <http://127.0.0.1:8000> en el navegador.

### Usuarios de demostración

Credenciales **solo para pruebas locales**, creadas por `cargar_datos_demo`:

| Rol | Usuario | Contraseña |
|---|---|---|
| Administrador | `admin` | `AdminDemo2026` |
| Operador | `operador` | `OperadorDemo2026` |
| Operador | `operador2` | `OperadorDemo2026` |

Horarios de demostración: `operador` tiene turno de **24 horas todos los días** (se puede probar a cualquier hora). `operador2` trabaja de **lunes a viernes de 06:00 a 07:00**, para mostrar el bloqueo fuera de turno y la autorización del administrador. El administrador no tiene horario.

### Qué se puede probar con los datos de demostración

Las fechas se calculan a partir del día en que se ejecuta el comando.

| Escenario | Cómo probarlo |
|---|---|
| Entrada válida (HU-001) | Registrar entrada → placa `JTR625` → elegir una celda libre |
| Vehículo ya dentro | Registrar entrada → placa `KLM482` |
| Cliente inactivo (RN-24) | Registrar entrada → placa `MNP913` |
| Mensualidad no vigente | Registrar entrada → placa `ZXC456` |
| Moto y celdas de moto | Registrar entrada → placa `XQH73F` (ya dentro) o registrar una salida y volver a entrar |
| Salida con novedades (HU-002) | Registrar salida → placa `KLM482` |
| Sin entrada abierta | Registrar salida → placa `BCD740` |
| Novedad con dos vehículos (HU-005) | Registrar salida → `KLM482` → Agregar novedad → otras placas: `RSD508` |
| Ocupación y consulta de celda (HU-003) | Vehículos dentro → consultar `A-003` |
| Historial (HU-004) | Historial → placa `KLM482` → clic en el número de novedades |
| Vencidos (HU-007/008) | Vencidos: `ABC123` vence hoy, `QWE852` venció hace 3 días, `JKL987` hace 9 (plazo vencido). Al iniciar el servidor, el planificador "envía" el primer correo de cada uno. |
| Reenvío con confirmación (HU-011) | Vencidos → Enviar correo → confirmar. Un segundo reenvío no se permite. |
| Contacto con autoridades (HU-009) | Como `admin`: Vencidos → `JKL987` → Registrar contacto |
| Operadores (HU-010, HU-019) | Como `admin`: Operadores → crear, editar, restablecer contraseña, desactivar o reactivar |
| Propietarios (HU-012, HU-014, HU-015) | Clientes → Propietarios → registrar, buscar, modificar, inactivar o activar |
| Vehículos (HU-013 a HU-015) | Clientes → Vehículos → registrar (la placa se valida según el tipo) o abrir la ficha de `JTR625` |
| Teléfono celular (HU-012) | Registrar un propietario con teléfono `3001234` → se rechaza; `3001234567` → se acepta |
| Cambio de propietario (HU-016, HU-017) | Como `operador`: ficha de un vehículo → Solicitar cambio. Como `admin`: Solicitudes → `JTR625` (de Laura Méndez a Andrés Gómez) → aprobar o rechazar con observación |
| Historial de propietarios (HU-017) | Ficha de `BGT219`: Paula Ríos aparece como propietaria anterior |
| Mapa de celdas (HU-018) | Clientes → Mapa de celdas: ocupación por zona y placa de cada celda ocupada |
| Horario de un operador (HU-020) | Como `admin`: Operadores → Horario → agregar una franja (las que se cruzan se rechazan) |
| Ingreso fuera de turno (HU-021) | Iniciar sesión como `operador2` fuera de lunes a viernes 06:00–07:00 → mensaje de fuera de turno |
| Autorización fuera de turno (HU-022) | Como `admin`: Autorizaciones → `operador2` → hasta dentro de una hora → `operador2` ya puede ingresar |
| Fin del turno (HU-021, RN-35) | Al terminar el turno aparece un aviso y la sesión se cierra a los 5 minutos; un registro empezado se puede terminar |
| Bitácora (HU-023) | Como `admin`: Bitácora → filtrar por usuario, acción o fechas |

Para empezar de cero: `python manage.py cargar_datos_demo --reiniciar` (**borra todos los datos**).

## Correo simulado y planificador

- El correo es **simulado** (DEC-007): no se envía nada. El contenido se ve en *Vencidos → Ver correos*.
- El planificador (APScheduler, DEC-008) revisa los vencimientos **al iniciar el servidor y cada hora**. También se puede ejecutar a mano:

```bash
python manage.py enviar_avisos_vencimiento
```

- Para desactivarlo, se define la variable de entorno `AVISOS_PLANIFICADOR=0`.

## Pruebas automatizadas

```bash
cd src
python manage.py test apps
```

Resultado actual: **154 pruebas, todas aprobadas**. Cubren los criterios de aceptación de HU-001 a HU-023, las reglas de negocio y las restricciones del modelo de datos.

## Copia de seguridad (RNF-009)

La base de datos es el archivo `src/db.sqlite3`. Para respaldarla, detenga el servidor y copie el archivo. Para restaurarla, reemplace el archivo por la copia.

> El proyecto puede estar dentro de OneDrive. Si OneDrive sincroniza `db.sqlite3` mientras el servidor está en uso, puede bloquear el archivo. En ese caso, pause la sincronización. La base de datos no se sube a Git.

## Estructura

```
docs/            Documentación (Markdown, LaTeX, SQL, diagramas PlantUML)
src/config/      Configuración de Django
src/apps/        Módulos: core, bitacora, cuentas, usuarios_celdas, pagos, entradas_salidas,
                 novedades, notificaciones, demo
src/templates/   Plantillas comunes      src/static/  Estilos y turno.js
tools/           plantuml.jar (no se versiona; solo para regenerar diagramas)
```

## Limitaciones conocidas

- El servidor de desarrollo de Django es adecuado para la demostración local, no para producción.
- Las pantallas de pagos (iteración 3) aún no existen. Los pagos de demostración se cargan con `cargar_datos_demo`.
- El aviso de fin de turno y el cierre por inactividad en el navegador (`turno.js`) se probaron solo de forma manual. El servidor aplica el cierre de sesión aunque el script no funcione.
