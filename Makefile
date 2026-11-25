# Curso RTL → GDSII · objetivos globales
# Los labs se corren desde su carpeta (cd labs/labNN-... && make help).

PY ?= python3
S  ?=

.DEFAULT_GOAL := help
.PHONY: help humo slides slides-forzar clean-slides
LAB_TARGETS := check rutas git-check pdk celda klayout entrega preguntas lint show sim latch \
               guardado wave respuestas captura cocotb wave-cocotb mutantes formal formal-bug formal-wave
.PHONY: $(LAB_TARGETS)

help:
	@echo "Curso RTL -> GDSII (SKY130)"
	@echo "  make humo               prueba de humo del contenedor (herramientas + PDK)"
	@echo "  make slides             construye todas las presentaciones en slides/out/"
	@echo "  make slides S=sesion1   construye solo una (S=ejemplo para la de referencia)"
	@echo "  make slides-forzar S=.. igual, pero re-renderiza todos los diagramas Mermaid"
	@echo "  make clean-slides       borra slides/out y los renders de Mermaid"
	@echo "Labs: cd labs/lab02-rtl && make help   (cada lab tiene su carpeta)"

humo:
	@./scripts/prueba_humo.sh

slides:
	$(PY) slides/build/build.py $(if $(S),$(S),--all)

slides-forzar:
	$(PY) slides/build/build.py $(if $(S),$(S),--all) --force-mermaid

clean-slides:
	rm -rf slides/out slides/*/_render

# Objetivos que viven en los labs: si alguien los corre aquí, se le dice dónde.
$(LAB_TARGETS):
	@echo "'make $@' se corre desde la carpeta del lab, no desde la raíz del repo:"
	@echo "    cd labs/lab0N-... && make $@      (por ejemplo: cd labs/lab02-rtl)"
	@exit 2
