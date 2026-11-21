"""Genera las secciones LaTeX de la iteración 3 a partir de los documentos Markdown aprobados.

Uso (desde la raíz del repositorio):
    python docs/latex/scripts/generar_iteracion3.py

Escribe docs/latex/chapters/it3/*.tex (archivos generados: no editar a mano).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generar_capitulos import AVISO, DOCS, tex  # noqa: E402
from generar_iteracion2 import md_a_tex, seccion  # noqa: E402

SALIDA = DOCS / "latex" / "chapters" / "it3"


def escribir(nombre: str, contenido: str) -> None:
    (SALIDA / nombre).write_text(AVISO + contenido, encoding="utf-8")


def main() -> None:
    SALIDA.mkdir(parents=True, exist_ok=True)
    req = (DOCS / "Requerimientos_Iteracion3_v1.md").read_text(encoding="utf-8")
    hu = (DOCS / "Historias_Usuario_Iteracion3_v1.md").read_text(encoding="utf-8")
    dis = (DOCS / "Diseno_Iteracion3_v1.md").read_text(encoding="utf-8")
    mod = (DOCS / "Modelo_Datos_v1.md").read_text(encoding="utf-8")

    escribir("requerimientos.tex", r"\section{Requerimientos de la iteración 3}" + "\n"
             "Aprobados por el equipo el 2026-11-20 (versión 1.2). Las reglas RN-01 a RN-37 de las iteraciones anteriores siguen vigentes.\n\n"
             + md_a_tex(seccion(req, "## 1. Respuestas", "## 5. Impacto")))
    escribir("historias.tex", r"\section{Historias de usuario de la iteración 3}" + "\n"
             "Aprobadas por el equipo el 2026-11-20 (versión 1), con los cuatro puntos de revisión de la última subsección.\n\n"
             + md_a_tex(seccion(hu, "## Resumen")))
    escribir("mockups.tex", r"\section{Mockups de la iteración 3}" + "\n"
             + md_a_tex(seccion(dis, "## 1. Mockups", "## 2. Casos de uso")).replace(r"\subsection{Mockups (M-26 a M-35)}", "")
             + "\n" + "\n".join(
                 rf"\diagrama{{mockups/{p.stem}.png}}{{{tex(p.stem.replace('_', ' '))}}}{{fig:{p.stem}}}{{0.8}}"
                 for p in sorted((DOCS / "latex" / "diagrams" / "mockups").glob("M-*.png"))
                 if 26 <= int(p.stem[2:4]) <= 35))
    escribir("casos_uso.tex", r"\section{Casos de uso de la iteración 3}" + "\n"
             + md_a_tex(seccion(dis, "## 2. Casos de uso", "## 3. Clases")).replace(r"\subsection{Casos de uso (UC-03)}", ""))
    escribir("clases.tex", r"\section{Clases de la iteración 3}" + "\n"
             + md_a_tex(seccion(dis, "## 3. Clases", "## 4. Paquetes")).replace(r"\subsection{Clases}", ""))
    escribir("paquetes.tex", r"\section{Cambios de la iteración 3}" + "\n"
             "El diagrama PK-01 (versión 3) de este capítulo ya incluye estos cambios.\n\n"
             + md_a_tex(seccion(dis, "## 4. Paquetes", "## 5. Mecanismos")).replace(r"\subsection{Paquetes y componentes (PK-01 v3, ARQ-03 v3)}", "")
             .replace(r"\diagrama{uml/PK-01_Paquetes.png}{PK-01}{fig:PK-01_Paquetes}{1.0}", ""))
    escribir("arquitectura.tex", r"\section{Actualización de la iteración 3}" + "\n"
             + md_a_tex(seccion(dis, "## 5. Mecanismos", "## 6.")).replace(r"\subsection{Mecanismos}", ""))
    escribir("modelo.tex", r"\section{Cambios del modelo v1.4 (iteración 3)}" + "\n"
             + md_a_tex(seccion(mod, "**Base:** requerimientos de la iteración 3")))
    print("Secciones de la iteración 3 generadas en", SALIDA)


if __name__ == "__main__":
    main()
