#!/usr/bin/env bash
# =====================================================================
#  pdk_info.sh · Ficha técnica de una celda estándar de SKY130
#
#  Uso:   ./pdk_info.sh <celda> [corner]
#         ./pdk_info.sh nand2_1
#         ./pdk_info.sh sky130_fd_sc_hd__dfrtp_1 ss_100C_1v60
#
#  Lee dos vistas del PDK:
#    .lib  (libs.ref/sky130_fd_sc_hd/lib/)  -> área            (la usa síntesis)
#    .lef  (libs.ref/sky130_fd_sc_hd/lef/)  -> tamaño y pines  (los usa PnR)
#
#  Requiere haber hecho:  source ../../scripts/env.sh
#
#  TU TAREA: llenar los 3 TODO (AREA, TAMANO, PINES) con los comandos que
#  armes en la terminal siguiendo la parte 4.3 del README. Pruébalo con:
#     make celda CELDA=nand2_1
# =====================================================================
set -u

if [ $# -lt 1 ]; then
  echo "Uso: $0 <celda> [corner]      p.ej.  $0 nand2_1" >&2
  exit 1
fi
if [ -z "${SCL_DIR:-}" ]; then
  echo "ERROR: primero fija el PDK:  source ../../scripts/env.sh" >&2
  exit 1
fi

CELDA=$1
case "$CELDA" in
  sky130_fd_sc_hd__*) ;;                     # ya viene con el prefijo
  *) CELDA="sky130_fd_sc_hd__$CELDA" ;;      # nand2_1 -> sky130_fd_sc_hd__nand2_1
esac
CORNER=${2:-tt_025C_1v80}

LIB="$SCL_DIR/lib/sky130_fd_sc_hd__${CORNER}.lib"
LEF="$SCL_DIR/lef/sky130_fd_sc_hd.lef"
for f in "$LIB" "$LEF"; do
  [ -f "$f" ] || { echo "ERROR: no existe $f" >&2; exit 1; }
done
if ! grep -q "^MACRO $CELDA\$" "$LEF"; then
  echo "No encontré la celda '$CELDA'. Lista de celdas:  grep '^MACRO' \$CELLLEF | less" >&2
  exit 2
fi

# ---- Lo que vas a usar en tus comandos (ya está listo) ------------------
PATRON_LIB="cell (\"$CELDA\")"      # así empieza tu celda en el .lib
PATRON_LEF="MACRO $CELDA"           # así empieza tu celda en el .lef
BLOQUE=$(sed -n "/^MACRO $CELDA\$/,/^END $CELDA\$/p" "$LEF")   # solo el bloque de tu celda en el .lef

# ---- TODO 1 · ÁREA (del .lib) -------------------------------------------
#  Arma el comando en la terminal (README, parte 4.3) y pégalo entre $( y )
AREA=$( )

# ---- TODO 2 · TAMAÑO (del .lef): debe dar "ancho alto", p.ej. "1.380 2.720"
TAMANO=$( )

# ---- TODO 3 · PINES (del .lef): un nombre de pin por línea ---------------
PINES=$( )

# =====================================================================
#  Reporte (ya está hecho: no hay que tocarlo)
# =====================================================================
read -r ANCHO ALTO <<< "${TAMANO:-}"
num() { awk -v x="$1" 'BEGIN { if (x == "") print "TODO"; else printf "%g", x }'; }
SITIOS=$(awk -v w="${ANCHO:-0}" 'BEGIN { printf "%d", w / 0.46 + 0.5 }')   # sitio unithd = 0.46 µm

echo "Celda   : $CELDA"
echo "Corner  : $CORNER"
echo "Área    : $(num "$AREA") µm²                (.lib)"
echo "Tamaño  : $(num "${ANCHO:-}") x $(num "${ALTO:-}") µm  = $SITIOS sitios unithd   (.lef)"
echo "Pines   : $(echo ${PINES:-TODO})         (.lef)"
