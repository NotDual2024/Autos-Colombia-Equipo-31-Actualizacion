"""Genera las secciones LaTeX de la iteración 2 a partir de los documentos Markdown aprobados.

Uso (desde la raíz del repositorio):
    python docs/latex/scripts/generar_iteracion2.py

Escribe docs/latex/chapters/it2/*.tex (archivos generados: no editar a mano).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generar_capitulos import AVISO, DOCS, tex  # noqa: E402

SALIDA = DOCS / "latex" / "chapters" / "it2"
ANCHO_TOTAL = 14.4


def _celdas(linea: str) -> list[str]:
    return [c.strip() for c in linea.strip().strip("|").split(" | ")]


def _tabla(lineas: list[str]) -> str:
    filas = [_celdas(l) for l in lineas if not re.fullmatch(r"\|(\s*:?-{2,}:?\s*\|)+", l.strip())]
    n = max(len(f) for f in filas)
    filas = [(f + [""] * n)[:n] for f in filas]
    largos = [max(6, sum(len(f[i]) for f in filas) / len(filas)) for i in range(n)]
    # ancho mínimo: que quepa la palabra más larga de la columna (≈0.2 cm por carácter)
    minimos = [max(1.5, 0.2 * max((len(p) for f in filas for p in re.sub(r"[*`]", "", f[i]).split()), default=0))
               for i in range(n)]
    total = sum(largos)
    anchos = [max(minimos[i], round(ANCHO_TOTAL * largos[i] / total, 1)) for i in range(n)]
    exceso = sum(anchos) - ANCHO_TOTAL
    if exceso > 0:
        i = anchos.index(max(anchos))
        anchos[i] = round(anchos[i] - exceso, 1)
    cols = "".join(rf">{{\raggedright\arraybackslash}}p{{{a}cm}}" for a in anchos)
    alinea = lambda c: tex(c).replace("✔", r"$\checkmark$").replace("—", "---")  # noqa: E731
    out = [rf"\begin{{longtable}}{{{cols}}}", r"\toprule",
           " & ".join(r"\textbf{" + alinea(c) + "}" for c in filas[0]) + r"\\", r"\midrule\endhead"]
    out += [" & ".join(alinea(c) for c in f) + r"\\" for f in filas[1:]]
    out += [r"\bottomrule", r"\end{longtable}", ""]
    return "\n".join(out)


def md_a_tex(texto: str, encabezados=("subsection", "subsubsection", "paragraph")) -> str:
    """Conversor sencillo de Markdown a LaTeX para los documentos del proyecto."""
    lineas = texto.splitlines()
    out: list[str] = []
    i = 0
    while i < len(lineas):
        l = lineas[i]
        s = l.strip()
        if s.startswith("```"):
            estilo = "gherkin" if "gherkin" in s else None
            bloque = []
            i += 1
            while i < len(lineas) and not lineas[i].strip().startswith("```"):
                bloque.append(lineas[i])
                i += 1
            opcion = "[style=gherkin]" if estilo else "[basicstyle=\\ttfamily\\small,frame=single,breaklines=true]"
            out += [r"\begin{lstlisting}" + opcion, *bloque, r"\end{lstlisting}"]
        elif s.startswith("|"):
            tabla = []
            while i < len(lineas) and lineas[i].strip().startswith("|"):
                tabla.append(lineas[i])
                i += 1
            out.append(_tabla(tabla))
            continue
        elif re.match(r"^#{2,4} ", s):
            nivel = len(s.split(" ")[0]) - 2
            titulo = re.sub(r"^\d+(\.\d+)*\.\s+", "", s.split(" ", 1)[1])  # quita "1. " (LaTeX ya numera)
            out.append("\\" + encabezados[min(nivel, 2)] + "{" + tex(titulo) + "}")
        elif m := re.match(r"^!\[(.*?)\]\((.*?)\)", s):
            ruta = m.group(2).replace("latex/diagrams/", "")
            nombre = Path(ruta).stem
            ancho = "1.0" if any(k in nombre for k in ("CL-", "UC-", "PK-", "MR-", "MER-")) else "0.85"
            out.append(rf"\diagrama{{{ruta}}}{{{tex(m.group(1))}}}{{fig:{nombre}}}{{{ancho}}}")
        elif re.match(r"^\s*([-*]|\d+\.) ", l):
            entorno = "enumerate" if re.match(r"^\s*\d+\. ", l) else "itemize"
            out.append(rf"\begin{{{entorno}}}")
            while i < len(lineas) and re.match(r"^\s*([-*]|\d+\.) ", lineas[i]):
                actual = lineas[i]
                sangria = len(actual) - len(actual.lstrip())
                item = re.sub(r"^\s*([-*]|\d+\.) ", "", actual)
                if sangria >= 2:
                    out.append(r"  \begin{itemize}\item " + tex(item) + r"\end{itemize}")
                else:
                    out.append(r"  \item " + tex(item))
                i += 1
            out.append(rf"\end{{{entorno}}}")
            continue
        elif s.startswith("> "):
            out.append(r"\textit{" + tex(s[2:]) + "}\n")
        elif s and s != "---":
            out.append(tex(s) + "\n")
        else:
            out.append("")
        i += 1
    return "\n".join(out)


def seccion(md: str, desde: str, hasta: str | None = None) -> str:
    """Texto entre el encabezado que empieza con 'desde' y el que empieza con 'hasta'."""
    i = md.index(desde)
    j = md.index(hasta, i + len(desde)) if hasta else len(md)
    return md[i:j]


def escribir(nombre: str, contenido: str) -> None:
    (SALIDA / nombre).write_text(AVISO + contenido, encoding="utf-8")


def main() -> None:
    SALIDA.mkdir(parents=True, exist_ok=True)
    req = (DOCS / "Requerimientos_Iteracion2_v1.md").read_text(encoding="utf-8")
    hu = (DOCS / "Historias_Usuario_Iteracion2_v1.md").read_text(encoding="utf-8")
    dis = (DOCS / "Diseno_Iteracion2_v1.md").read_text(encoding="utf-8")
    mod = (DOCS / "Modelo_Datos_v1.md").read_text(encoding="utf-8")

    def chg003(desde: str, hasta: str | None, mockups: tuple[int, ...] = ()) -> str:
        """Subsección de la solicitud de cambio CHG-003 (sección 7 del diseño de la iteración 2)."""
        titulo = desde.split(". ", 1)[1]
        cuerpo = md_a_tex(seccion(dis, desde, hasta), ("subsubsection", "paragraph", "paragraph"))
        cuerpo = cuerpo.replace(r"\subsubsection{" + tex(titulo) + "}", "", 1)
        imagenes = "\n".join(
            rf"\diagrama{{mockups/{p.stem}.png}}{{{tex(p.stem.replace('_', ' '))}}}{{fig:{p.stem}}}{{0.8}}"
            for p in sorted((DOCS / "latex" / "diagrams" / "mockups").glob("M-*.png")) if int(p.stem[2:4]) in mockups)
        return ("\n" + r"\subsection{CHG-003: gestión de celdas (" + tex(titulo.lower()) + ")}" + "\n"
                + "Solicitud de cambio aprobada el 2026-11-22, a partir de la observación del profesor.\n\n"
                + cuerpo + "\n" + imagenes + "\n")

    escribir("requerimientos.tex", r"\section{Requerimientos de la iteración 2}" + "\n"
             "Aprobados por el equipo el 2026-11-15 (versión 1.4) y actualizados a la versión 1.5 por la solicitud de cambio CHG-003 (2026-11-22). Las reglas RN-01 a RN-24 de la iteración 1 siguen vigentes.\n\n"
             + md_a_tex(seccion(req, "## 1. Respuestas", "## 5. Decisiones")))
    escribir("historias.tex", r"\section{Historias de usuario de la iteración 2}" + "\n"
             "Aprobadas por el equipo el 2026-11-15 (versión 1.1). La versión 1.2 agrega HU-033 a HU-036 por la solicitud de cambio CHG-003 (2026-11-22).\n\n"
             + md_a_tex(seccion(hu, "## Resumen", "## Puntos revisados")))
    escribir("mockups.tex", r"\section{Mockups de la iteración 2}" + "\n"
             + md_a_tex(seccion(dis, "## 1. Mockups", "## 2. Casos de uso"), ("subsection", "subsubsection", "paragraph")).replace(
                 r"\subsection{Mockups (M-13 a M-25)}", "")
             + "\n" + "\n".join(
                 rf"\diagrama{{mockups/{p.stem}.png}}{{{tex(p.stem.replace('_', ' '))}}}{{fig:{p.stem}}}{{0.8}}"
                 for p in sorted((DOCS / "latex" / "diagrams" / "mockups").glob("M-*.png"))
                 if 13 <= int(p.stem[2:4]) <= 25)
             + "\n" + chg003("### 7.1. Mockups", "### 7.2.", (36, 37)))
    escribir("casos_uso.tex", r"\section{Casos de uso de la iteración 2}" + "\n"
             + md_a_tex(seccion(dis, "## 2. Casos de uso", "## 3. Clases")).replace(r"\subsection{Casos de uso (UC-02)}", "")
             + chg003("### 7.2. Casos de uso", "### 7.3."))
    escribir("clases.tex", r"\section{Clases de la iteración 2}" + "\n"
             + md_a_tex(seccion(dis, "## 3. Clases", "## 4. Paquetes")).replace(r"\subsection{Clases}", "")
             + chg003("### 7.3. Clases", "### 7.4."))
    escribir("paquetes.tex", r"\section{Cambios de la iteración 2}" + "\n"
             + md_a_tex(seccion(dis, "## 4. Paquetes", "## 5. Mecanismo")).replace(r"\subsection{Paquetes y componentes (PK-01 v2, ARQ-03 v2)}", "")
             .replace(r"\diagrama{uml/PK-01_Paquetes.png}{PK-01}{fig:PK-01_Paquetes}{1.0}", "")
             + chg003("### 7.4. Paquetes y secuencias", None))
    escribir("arquitectura.tex", r"\section{Actualización de la iteración 2}" + "\n"
             + md_a_tex(seccion(dis, "## 5. Mecanismo", "## 6.")).replace(r"\subsection{Mecanismo de control de turno (RN-31, RN-35, RN-36)}", r"\subsection{Mecanismo de control de turno}"))
    escribir("modelo.tex", r"\section{Cambios del modelo v1.3 (iteración 2)}" + "\n"
             + md_a_tex(seccion(mod, "**Base:** requerimientos de la iteración 2", "## 8.")))
    print("Secciones de la iteración 2 generadas en", SALIDA)


if __name__ == "__main__":
    main()
