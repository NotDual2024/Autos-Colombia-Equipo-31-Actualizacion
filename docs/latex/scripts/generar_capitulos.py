"""Genera los capítulos LaTeX de requerimientos, historias de usuario y decisiones
a partir de los documentos Markdown aprobados (fuente única de verdad).

Uso (desde la raíz del repositorio):
    python docs/latex/scripts/generar_capitulos.py

Archivos generados (no editar a mano):
    docs/latex/chapters/03-requerimientos.tex
    docs/latex/chapters/05-historias-usuario.tex
    docs/latex/chapters/11-decisiones.tex
"""
from __future__ import annotations

import re
from pathlib import Path

DOCS = Path(__file__).resolve().parents[2]
CHAPTERS = DOCS / "latex" / "chapters"
AVISO = "% ARCHIVO GENERADO por scripts/generar_capitulos.py. No editar a mano.\n"

ESPECIALES = {
    "\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#",
    "_": r"\_", "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}",
}
UNICODE = {"≥": r"$\geq$", "≤": r"$\leq$", "→": r"$\rightarrow$", "✓": r"$\checkmark$",
           "“": "``", "”": "''", "…": "...", "×": r"$\times$", "≠": r"$\neq$", "⇔": r"$\Leftrightarrow$",
           "∈": r"$\in$", "✔": r"$\checkmark$", "‹": "<", "›": ">"}


def tex(texto: str) -> str:
    """Convierte texto Markdown en línea (negrita, código) a LaTeX escapado."""
    # La negrita se marca antes de separar el código, porque puede contenerlo: **solo `core`**
    texto = re.sub(r"\*\*(.+?)\*\*", "\x01\\1\x02", texto)
    partes = re.split(r"(`[^`]*`)", texto)
    salida = []
    for parte in partes:
        es_codigo = parte.startswith("`") and parte.endswith("`") and len(parte) > 1
        contenido = parte[1:-1] if es_codigo else parte
        contenido = "".join(ESPECIALES.get(c, c) for c in contenido)
        for k, v in UNICODE.items():
            contenido = contenido.replace(k, v)
        if es_codigo:
            salida.append(r"\texttt{" + contenido + "}")
        else:
            contenido = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"\\emph{\1}", contenido)
            contenido = re.sub(r'"([^"]+)"', r"``\1''", contenido)
            salida.append(contenido)
    return "".join(salida).replace("\x01", r"\textbf{").replace("\x02", "}")


def filas_tabla(lineas: list[str]) -> list[list[str]]:
    """Devuelve las filas de datos de una tabla Markdown (sin encabezado ni separador)."""
    filas = []
    for linea in lineas:
        if not linea.startswith("|"):
            continue
        if re.fullmatch(r"\|(\s*:?-{3,}:?\s*\|)+", linea.strip()):
            continue  # fila separadora |---|---|
        celdas = [c.strip() for c in linea.strip().strip("|").split(" | ")]
        filas.append(celdas)
    return filas[1:] if filas else []


def longtable(anchos: list[float], encabezados: list[str], filas: list[list[str]]) -> str:
    cols = "".join(rf">{{\raggedright\arraybackslash}}p{{{a}cm}}" for a in anchos)
    out = [rf"\begin{{longtable}}{{{cols}}}", r"\toprule",
           " & ".join(rf"\textbf{{{h}}}" for h in encabezados) + r"\\", r"\midrule\endhead"]
    for f in filas:
        f = (f + [""] * len(anchos))[: len(anchos)]
        out.append(" & ".join(tex(c) for c in f) + r"\\")
    out += [r"\bottomrule", r"\end{longtable}", ""]
    return "\n".join(out)


def secciones(texto: str, nivel: str) -> list[tuple[str, list[str]]]:
    """Divide el texto en secciones por encabezado ('## ' o '### ')."""
    res, actual, cuerpo = [], None, []
    for linea in texto.splitlines():
        if linea.startswith(nivel) and not linea.startswith(nivel + "#"):
            if actual is not None:
                res.append((actual, cuerpo))
            actual, cuerpo = linea[len(nivel):].strip(), []
        elif actual is not None:
            cuerpo.append(linea)
    if actual is not None:
        res.append((actual, cuerpo))
    return res


def vinetas(lineas: list[str], desde: str) -> list[str]:
    try:
        i = next(k for k, l in enumerate(lineas) if l.strip() == desde)
    except StopIteration:
        return []
    items = []
    for l in lineas[i + 1:]:
        if l.startswith("- "):
            items.append(l[2:].strip())
        elif l.startswith("#") or l.strip() == "---":
            break
    return items


def itemize(items: list[str]) -> str:
    if not items:
        return ""
    return "\\begin{itemize}\n" + "\n".join(r"  \item " + tex(i) for i in items) + "\n\\end{itemize}\n"


# ---------------------------------------------------------------- Requerimientos
def capitulo_requerimientos() -> str:
    md = (DOCS / "Requerimientos_v2.md").read_text(encoding="utf-8")
    version = re.search(r"\*\*Versión:\*\* ([\d.]+)", md).group(1)
    secs = dict(secciones(md, "## "))
    out = [AVISO, r"\chapter{Requerimientos}\label{cap:requerimientos}", "",
           f"Este capítulo reproduce los requerimientos de la iteración 1 aprobados por el equipo "
           f"(versión {version} del documento de requerimientos). Etiquetas de origen: "
           r"\textbf{[E]} enunciado, \textbf{[U]} indicado por el equipo, \textbf{[I]} inferido y confirmado. "
           r"Prioridad según MoSCoW (Must, Should, Could, Won't).", ""]

    clave = next(k for k in secs if k.startswith("1. Actores"))
    out += [r"\section{Actores}", longtable([3.4, 8.2, 2.8], ["Actor", "Descripción", "Origen"], filas_tabla(secs[clave]))]

    clave = next(k for k in secs if k.startswith("2. Reglas de negocio"))
    reglas = [l for l in secs[clave]]
    filas_rn = sorted(filas_tabla(reglas), key=lambda f: int(re.sub(r"\D", "", f[0]) or 0))
    out += [r"\section{Reglas de negocio}", longtable([1.5, 9.6, 3.3], ["ID", "Regla", "Origen"], filas_rn)]
    notas = [l for l in reglas if l.startswith("**Cómo se relacionan")]
    out += [tex(n) + "\n" for n in notas]

    clave = next(k for k in secs if k.startswith("3. Requerimientos funcionales"))
    out += [r"\section{Requerimientos funcionales de la iteración 1}", ""]
    for titulo, cuerpo in secciones("\n".join(secs[clave]), "### "):
        out.append(r"\subsection{" + tex(titulo) + "}")
        out.append(longtable([3.2, 11.2], ["Campo", "Detalle"], filas_tabla(cuerpo)))
        for l in cuerpo:
            if l.startswith("> "):
                out.append(r"\textit{" + tex(l[2:].strip()) + "}\n")
        crit = vinetas(cuerpo, "**Criterios de aceptación**")
        if crit:
            out += [r"\textbf{Criterios de aceptación}", itemize(crit)]

    clave = next(k for k in secs if k.startswith("4. Requerimientos no funcionales"))
    out += [r"\section{Requerimientos no funcionales}",
            longtable([1.7, 2.3, 5.3, 3.6, 1.5], ["ID", "Categoría", "Descripción", "Métrica o condición", "Prioridad"],
                      filas_tabla(secs[clave]))]

    clave = next((k for k in secs if k.startswith("Anexo A")), None)
    if clave:
        out += [r"\section{Requerimientos de iteraciones futuras (referencia)}",
                "Estos requerimientos solo se identifican para diseñar el modelo de datos completo (DEC-001). "
                "Se detallan y aprueban en su propia iteración.", ""]
        for titulo, cuerpo in secciones("\n".join(secs[clave]), "### "):
            out += [r"\subsection*{" + tex(titulo) + "}",
                    longtable([1.6, 3.6, 6.8, 2.4], ["ID", "Nombre", "Descripción", "Origen"], filas_tabla(cuerpo))]
    return "\n".join(out)


# ---------------------------------------------------------------- Historias
def capitulo_historias() -> str:
    md = (DOCS / "Historias_Usuario_v1.md").read_text(encoding="utf-8")
    secs = secciones(md, "## ")
    out = [AVISO, r"\chapter{Historias de usuario}\label{cap:historias}", "",
           "Las historias de usuario se derivan de los requerimientos funcionales aprobados. "
           "Siguen el formato ``Como [rol], quiero [funcionalidad], para [beneficio]'' y sus criterios de aceptación "
           "usan la forma Dado / Cuando / Entonces, que sirve de base para las pruebas funcionales.", ""]
    resumen = next(c for t, c in secs if t.startswith("Resumen"))
    out += [r"\section{Resumen}", longtable([1.5, 5.2, 2.6, 3.0, 1.9], ["ID", "Título", "Actor", "RF", "Prioridad"], filas_tabla(resumen))]
    out += [r"\section{Detalle de las historias}"]
    for titulo, cuerpo in secs:
        if not titulo.startswith("HU-"):
            continue
        out.append(r"\subsection{" + tex(titulo) + "}")
        en_codigo, bloque = False, []
        for l in cuerpo:
            if l.startswith("```"):
                if en_codigo:
                    out += [r"\begin{lstlisting}[style=gherkin]", *bloque, r"\end{lstlisting}"]
                    bloque = []
                en_codigo = not en_codigo
                continue
            if en_codigo:
                bloque.append(l)
            elif l.startswith("> "):
                out.append(r"\textit{" + tex(l[2:].strip()) + "}\n")
            elif l.startswith("**Criterios de aceptación**"):
                out.append(r"\textbf{Criterios de aceptación}" + "\n")
            elif l.startswith("**") and l.strip() != "---":
                out.append(tex(l.strip()) + r"\\")
            elif l.strip() and l.strip() != "---":
                out.append(tex(l.strip()) + "\n")
        out.append("")
    matriz = next((c for t, c in secs if t.startswith("Matriz de trazabilidad")), None)
    if matriz:
        out += [r"\section{Matriz de trazabilidad RF $\rightarrow$ HU}", longtable([9.0, 5.4], ["Requerimiento", "Historia"], filas_tabla(matriz))]
    return "\n".join(out)


# ---------------------------------------------------------------- Decisiones
def capitulo_decisiones() -> str:
    md = (DOCS / "Registro_Decisiones.md").read_text(encoding="utf-8")
    tabla = [l for l in md.splitlines() if l.startswith("| DEC-") or l.startswith("| ID |")]
    out = [AVISO, r"\chapter{Registro de decisiones}\label{cap:decisiones}", "",
           "Cada decisión significativa se presentó con su problema, alternativas, ventajas, desventajas y una "
           "recomendación, y se registró solo después de la aprobación explícita del equipo del proyecto.", "",
           r"\section{Resumen}", longtable([1.8, 7.0, 5.6], ["ID", "Tema", "Estado"], filas_tabla(tabla)),
           r"\section{Detalle}"]
    for titulo, cuerpo in secciones(md, "## "):
        if not titulo.startswith("DEC-"):
            continue
        texto = "\n".join(cuerpo)

        def campo(nombre: str) -> str | None:
            m = re.search(r"\*\*" + nombre + r":\*\*\s*(.+)", texto)
            return m.group(1).strip() if m else None

        out.append(r"\subsection{" + tex(titulo) + "}")
        out.append(r"\begin{description}[style=nextline]")
        for nombre in ["Problema", "Decisión seleccionada", "Justificación", "Fecha", "Estado"]:
            valor = campo(nombre)
            if valor:
                out.append(r"  \item[" + nombre + "] " + tex(valor))
        out.append(r"\end{description}")
    return "\n".join(out)


def main() -> None:
    CHAPTERS.mkdir(parents=True, exist_ok=True)
    (CHAPTERS / "03-requerimientos.tex").write_text(capitulo_requerimientos(), encoding="utf-8")
    (CHAPTERS / "05-historias-usuario.tex").write_text(capitulo_historias(), encoding="utf-8")
    (CHAPTERS / "11-decisiones.tex").write_text(capitulo_decisiones(), encoding="utf-8")
    print("Capítulos generados en", CHAPTERS)


if __name__ == "__main__":
    main()
