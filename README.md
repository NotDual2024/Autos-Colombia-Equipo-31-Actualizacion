# Parqueadero "Autos Colombia"

Sistema web local para la gestión de un parqueadero por mensualidad: entradas y salidas de vehículos, celdas, novedades, avisos de vencimiento (simulados) y operadores.

Proyecto académico de Ingeniería de Software (IU Digital). **Iteración 1: Gestión de la entrada y salida de vehículos.**

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
| Operadores (HU-010) | Como `admin`: Operadores → crear, desactivar o reactivar |

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

Resultado actual: **100 pruebas, todas aprobadas**. Cubren los criterios de aceptación de HU-001 a HU-011, las reglas de negocio y las restricciones del modelo de datos.

## Copia de seguridad (RNF-009)

La base de datos es el archivo `src/db.sqlite3`. Para respaldarla, detenga el servidor y copie el archivo. Para restaurarla, reemplace el archivo por la copia.

> El proyecto puede estar dentro de OneDrive. Si OneDrive sincroniza `db.sqlite3` mientras el servidor está en uso, puede bloquear el archivo. En ese caso, pause la sincronización. La base de datos no se sube a Git.

## Estructura

```
docs/            Documentación (Markdown, LaTeX, SQL, diagramas PlantUML)
src/config/      Configuración de Django
src/apps/        Módulos: core, cuentas, usuarios_celdas, pagos, entradas_salidas,
                 novedades, notificaciones, demo
src/templates/   Plantillas comunes      src/static/  Estilos
tools/           plantuml.jar (no se versiona; solo para regenerar diagramas)
```

## Limitaciones conocidas

- El servidor de desarrollo de Django es adecuado para la demostración local, no para producción.
- Las pantallas de propietarios, vehículos y celdas (iteración 2) y de pagos (iteración 3) aún no existen. Sus datos se cargan con `cargar_datos_demo`.
