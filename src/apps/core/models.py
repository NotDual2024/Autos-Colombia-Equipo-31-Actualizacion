"""core no tiene modelos propios; importa los lookups para que estén
registrados cuando se cargan los modelos de los demás módulos."""
from . import lookups  # noqa: F401
