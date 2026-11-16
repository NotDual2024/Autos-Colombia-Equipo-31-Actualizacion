# Documento técnico en LaTeX

## Requisitos
- MiKTeX (o TeX Live) con `latexmk` y `pdflatex`.
- Python 3 para regenerar los capítulos.
- Java y `tools/plantuml.jar` (PlantUML 1.2026.10) solo si se modifican los diagramas.

## Regenerar los capítulos a partir de los documentos aprobados
Los capítulos 03 (requerimientos), 05 (historias de usuario) y 11 (decisiones) **se generan** a partir de los archivos Markdown de `docs/`. No se editan a mano.

```bash
python docs/latex/scripts/generar_capitulos.py
```

## Regenerar los diagramas
```bash
java -jar tools/plantuml.jar -tpng docs/latex/diagrams/arquitectura/*.puml
```

## Compilar el PDF
```bash
cd docs/latex
latexmk -pdf main.tex
```

El resultado es `docs/latex/main.pdf`. Para limpiar los archivos auxiliares: `latexmk -c`.
