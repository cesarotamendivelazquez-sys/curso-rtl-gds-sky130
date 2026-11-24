# =====================================================================
#  Lab 02 · RTL sintetizable y FSM
#  Se corre DESDE ESTA CARPETA:  cd labs/lab02-rtl && make help
#  Regla del curso: solo rutas relativas.
# =====================================================================
SHELL := /bin/bash
ROOT  := ../..
RTL   := $(ROOT)/common/rtl/semaphore/rtl/semaphore.v
PY    := python3 scripts/revisar.py

.DEFAULT_GOAL := help
.PHONY: help humo check preguntas lint show latch sim entrega clean

help:
	@echo "Lab 02 · RTL sintetizable y FSM   (tu archivo: $(RTL))"
	@echo "  Parte 1  make preguntas   revisa preguntas.txt (las 4 piezas)"
	@echo "  Parte 2  make lint        Verilator --lint-only -Wall"
	@echo "           make show        esquemático RTL con Yosys (build/semaforo_rtl.svg)"
	@echo "  Parte 3  make sim         TB base + revisor del botón ped_req (Icarus)"
	@echo "  Parte 4  make latch       ¿Yosys infiere algún latch?"
	@echo "  Final    make entrega     ¿está lista tu entrega?"
	@echo "           make check       herramientas y rama"
	@echo "           make clean       borra build/"

check humo:
	@ver() { if command -v $$1 >/dev/null; then printf '  [ OK ] %-9s %s\n' $$1 "$$($$@ 2>&1 | head -1)"; \
	         else printf '  [MAL ] %-9s no está: ¿estás dentro del contenedor?\n' $$1; fi; }; \
	 ver verilator --version; ver yosys -V; ver iverilog -V; ver git --version
	@r=$$(git branch --show-current); case "$$r" in alumno/?*) echo "  [ OK ] rama      $$r";; \
	  *) echo "  [ ?? ] rama      $$r  (trabaja en tu rama: git switch alumno/<tu-nombre>)";; esac

preguntas:
	@$(PY) preguntas

lint:
	@$(PY) lint

# Elabora el RTL (proc; opt) SIN celdas del PDK y dibuja el esquemático.
show:
	@mkdir -p build
	@echo '$$ yosys -p "read_verilog $(RTL); proc; opt; show -width -format svg -prefix build/semaforo_rtl"'
	@yosys -q -p "read_verilog $(RTL); proc; opt; show -width -format svg -prefix build/semaforo_rtl"
	@echo "Listo: build/semaforo_rtl.svg"
	@if command -v xdot >/dev/null; then (xdot build/semaforo_rtl.dot >/dev/null 2>&1 &); \
	 elif command -v firefox >/dev/null; then (firefox build/semaforo_rtl.svg >/dev/null 2>&1 &); \
	 elif command -v xdg-open >/dev/null; then (xdg-open build/semaforo_rtl.svg >/dev/null 2>&1 &); \
	 else echo "Ábrelo con el navegador del escritorio."; fi

sim:
	@$(PY) sim

latch:
	@$(PY) latch

entrega:
	@$(PY) entrega

clean:
	rm -rf build
