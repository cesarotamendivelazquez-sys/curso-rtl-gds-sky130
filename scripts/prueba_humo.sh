#!/usr/bin/env bash
# =====================================================================
#  prueba_humo.sh  ·  ¿Está listo tu contenedor para el curso?
#  Corre dentro de iic-osic-tools:   ./scripts/prueba_humo.sh
#  Manda la captura de la salida un día antes de la sesión 1.
#
#  POR VALIDAR: nombres/flags de versión en la etiqueta de imagen del curso
#  (sobre todo librelane vs openlane).
# =====================================================================
cd "$(dirname "$0")/.." || exit 1

ok=0; fail=0
check() {   # check "<nombre>" <comando...>
  local name=$1; shift
  local out rc
  out=$("$@" 2>&1); rc=$?
  out=$(printf '%s\n' "$out" | head -1)
  if [ "$rc" -eq 0 ] && [ -n "$out" ]; then
    printf '  [OK]    %-12s %s\n' "$name" "$out"; ok=$((ok+1))
  else
    printf '  [FALLA] %-12s (no se encontró o no respondió)\n' "$name"; fail=$((fail+1))
  fi
}

echo "== Imagen =="
echo "  iic-osic-tools ${IIC_OSIC_TOOLS_VERSION:-(versión desconocida)}   <- debe ser la misma para todo el grupo"
echo "== Herramientas =="
check yosys     yosys -V
check openroad  openroad -version
check iverilog  sh -c 'iverilog -V | head -1'
check verilator verilator --version
check gtkwave   sh -c 'command -v gtkwave'
check klayout   klayout -v
check magic     sh -c 'magic --version'
check netgen    sh -c 'command -v netgen'
check sta       sta -version
check sby       sh -c 'command -v sby'
check librelane sh -c 'librelane --version 2>/dev/null || openlane --version'
check ciel      sh -c 'ciel --version 2>/dev/null || command -v ciel'
check cocotb    python3 -c "import cocotb; print('cocotb', cocotb.__version__)"
check git       git --version

echo "== PDK =="
if ENV_VERBOSE=1 source scripts/env.sh; then ok=$((ok+1)); else fail=$((fail+1)); fi

echo "== Resumen: $ok OK, $fail con falla =="
[ "$fail" -eq 0 ] && echo ">>> LISTO para el curso" || echo ">>> Revisa las fallas antes de la sesión 1"
exit "$fail"
