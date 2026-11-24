#!/usr/bin/env bash
# =====================================================================
#  prueba_humo.sh  ·  ¿Está listo tu contenedor para el curso?
#  Corre dentro de iic-osic-tools:   ./scripts/prueba_humo.sh
#  Manda la captura de la salida un día antes de la sesión 1.
#
#  Validado con hpretl/iic-osic-tools:2026.09 (LibreLane 3.1, Ciel 2.6).
# =====================================================================
VERSION_CURSO=2026.09
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
if [ "${IIC_OSIC_TOOLS_VERSION:-}" = "$VERSION_CURSO" ]; then
  printf '  [OK]    %-12s %s\n' "imagen" "iic-osic-tools $IIC_OSIC_TOOLS_VERSION"; ok=$((ok+1))
else
  printf '  [FALLA] %-12s tienes %s; el curso usa %s\n' "imagen" "${IIC_OSIC_TOOLS_VERSION:-desconocida}" "$VERSION_CURSO"
  printf '          -> en PowerShell: docker pull hpretl/iic-osic-tools:%s  y crea el contenedor con esa imagen\n' "$VERSION_CURSO"
  fail=$((fail+1))
fi
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
