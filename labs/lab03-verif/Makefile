# =====================================================================
#  Lab 03 · Verificación funcional (Flan) + formal opcional (Gelatina)
#  Se corre DESDE ESTA CARPETA:  cd labs/lab03-verif && make help
#  Regla del curso: solo rutas relativas.
# =====================================================================
SHELL := /bin/bash
ROOT  := ../..
RTL   := $(ROOT)/common/rtl/semaphore/rtl/semaphore.v
PY    := python3 scripts/revisar.py
TEST  ?=
SEED  ?=

.DEFAULT_GOAL := help
.PHONY: help humo check guardado sim wave respuestas captura cocotb wave-cocotb mutantes \
        formal formal-bug formal-wave entrega clean

help:
	@echo "Lab 03 · Verificación funcional   (tu RTL: $(RTL))"
	@echo "  Parte 1  make sim          TB base con tu RTL (Icarus) -> PASS/FAIL y build/dump.vcd"
	@echo "           make wave         abre la onda en GTKWave"
	@echo "  Parte 2  make guardado     PASO 0: ¿todo tu RTL está en un commit?"
	@echo "           make captura      foto de la pantalla -> entrega/onda_bug.png"
	@echo "           make respuestas   revisa respuestas.txt"
	@echo "  Parte 3  make cocotb       tus tests de cocotb (TEST=test_dirigido, SEED=7)"
	@echo "           make wave-cocotb  onda de la última corrida de cocotb"
	@echo "           make mutantes     ¿tus tests atrapan los 6 bugs a propósito?"
	@echo "  Parte 4  make formal       SymbiYosys: la propiedad sobre TU RTL (opcional)"
	@echo "           make formal-bug   la misma propiedad sobre el RTL con bug"
	@echo "           make formal-wave  abre el contraejemplo en GTKWave"
	@echo "  Final    make entrega      ¿está lista tu entrega?"
	@echo "           make check        herramientas y rama"
	@echo "           make clean        borra build/ y los directorios de sby"

check humo:
	@ver() { if command -v $$1 >/dev/null; then printf '  [ OK ] %-9s %s\n' $$1 "$$($$@ 2>&1 | head -1)"; \
	         else printf '  [MAL ] %-9s no está: ¿estás dentro del contenedor?\n' $$1; fi; }; \
	 ver iverilog -V; ver gtkwave --version; ver yosys -V; ver sby --help; ver git --version
	@v=$$(python3 -c "import cocotb; print(cocotb.__version__)" 2>/dev/null); case "$$v" in \
	  2.*) echo "  [ OK ] cocotb    $$v";; "") echo "  [MAL ] cocotb    no está";; \
	  *) echo "  [MAL ] cocotb    $$v (el lab usa la API de cocotb 2.x)";; esac
	@r=$$(git branch --show-current); case "$$r" in alumno/?*) echo "  [ OK ] rama      $$r";; \
	  *) echo "  [ ?? ] rama      $$r  (trabaja en tu rama: git switch alumno/<tu-nombre>)";; esac

guardado:
	@$(PY) guardado

sim:
	@$(PY) sim

wave:
	@test -f build/dump.vcd || { echo "No hay onda todavía: corre  make sim"; exit 1; }
	@echo '$$ gtkwave build/dump.vcd &'
	@(gtkwave build/dump.vcd >/dev/null 2>&1 &)

respuestas:
	@$(PY) respuestas

captura:
	@./scripts/captura.sh entrega/onda_bug.png 5

cocotb:
	@python3 cocotb/run.py $(if $(TEST),--test $(TEST)) $(if $(SEED),--seed $(SEED))

wave-cocotb:
	@test -f build/cocotb/semaforo.fst || { echo "No hay onda de cocotb: corre  make cocotb"; exit 1; }
	@echo '$$ gtkwave build/cocotb/semaforo.fst &'
	@(gtkwave build/cocotb/semaforo.fst >/dev/null 2>&1 &)

mutantes:
	@$(PY) mutantes

formal:
	@echo '$$ cd formal && sby -f prueba.sby'
	@cd formal && sby -f prueba.sby | tail -n 8; s=$${PIPESTATUS[0]}; echo; \
	 if [ $$s -eq 0 ]; then echo "== PASS: la propiedad se cumple para CUALQUIER número de ciclos =="; \
	 else echo "== FAIL: el solver rompió la propiedad en TU RTL · contraejemplo en formal/prueba/engine_0/ =="; fi

formal-bug:
	@echo '$$ cd formal && sby -f bug.sby'
	@cd formal && sby -f bug.sby | tail -n 8; s=$${PIPESTATUS[0]}; echo; \
	 if [ $$s -ne 0 ]; then echo "== FAIL esperado: contraejemplo en formal/bug/engine_0/trace.vcd · make formal-wave =="; \
	 else echo "== PASS: ¿?, el bug debía romper la propiedad =="; fi

formal-wave:
	@test -f formal/bug/engine_0/trace.vcd || { echo "No hay contraejemplo: corre  make formal-bug"; exit 1; }
	@echo '$$ gtkwave formal/bug/engine_0/trace.vcd &'
	@(gtkwave formal/bug/engine_0/trace.vcd >/dev/null 2>&1 &)

entrega:
	@$(PY) entrega

clean:
	rm -rf build formal/prueba formal/bug
