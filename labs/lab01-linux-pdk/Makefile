# =====================================================================
#  Lab 01 · PDKs y Linux para VLSI
#  Se corre DESDE ESTA CARPETA:  cd labs/lab01-linux-pdk && make help
#  Regla del curso: solo rutas relativas.
# =====================================================================
SHELL := /bin/bash
ROOT  := ../..
ENV   := source $(ROOT)/scripts/env.sh >/dev/null &&
CELDA ?= nand2_1

.DEFAULT_GOAL := help
.PHONY: help humo check rutas git-check pdk celda klayout entrega clean

help:
	@echo "Lab 01 · PDKs y Linux para VLSI"
	@echo "  Parte 1  make check                 herramientas + PDK"
	@echo "  Parte 2  make rutas                 revisa respuestas_rutas.txt"
	@echo "  Parte 3  make git-check             revisa tu configuración de git, rama y push"
	@echo "  Parte 4  make pdk                   radiografía del PDK (compárala con lo que exploraste)"
	@echo "           make celda CELDA=nand2_1   corre tu pdk_info.sh"
	@echo "           make klayout CELDA=nand2_1 abre esa celda en KLayout"
	@echo "  Final    make entrega               ¿está lista tu entrega?"
	@echo "           make clean"

# ---- Parte 1 ---------------------------------------------------------
check humo:
	@$(ROOT)/scripts/prueba_humo.sh

# ---- Parte 2 ---------------------------------------------------------
rutas:
	@$(ENV) python3 scripts/revisar_rutas.py

# ---- Parte 3 ---------------------------------------------------------
git-check:
	@bash scripts/revisar_git.sh

# ---- Parte 4 ---------------------------------------------------------
pdk:
	@$(ENV) bash scripts/resumen_pdk.sh

celda:
	@$(ENV) ./pdk_info.sh $(CELDA)

# Saca la celda del GDS de la librería y la abre con los colores de SKY130.
klayout:
	@$(ENV) n=$$( [[ "$(CELDA)" == sky130_fd_sc_hd__* ]] && echo "$(CELDA)" || echo "sky130_fd_sc_hd__$(CELDA)" ); \
	  klayout -b -r scripts/extraer_celda.py -rd gds="$$CELLGDS" -rd celda="$$n" -rd salida="$$n.gds" && \
	  (klayout -l "$$KLAYOUT_LYP" "$$n.gds" >/dev/null 2>&1 &)

# ---- Final -----------------------------------------------------------
entrega:
	@$(ENV) python3 scripts/revisar_entrega.py

clean:
	rm -f sky130_fd_sc_hd__*.gds
