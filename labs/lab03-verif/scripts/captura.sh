#!/usr/bin/env bash
# =====================================================================
#  captura.sh · Toma una foto de la pantalla del escritorio (noVNC)
#  Uso (lo llama make captura):  scripts/captura.sh entrega/onda_bug.png [segundos]
#  Cuenta hacia atrás para que pongas GTKWave al frente, maximizado.
# =====================================================================
set -u
OUT=${1:-entrega/onda_bug.png}
SEG=${2:-5}
mkdir -p "$(dirname "$OUT")"

if [ -z "${DISPLAY:-}" ]; then
    echo "No hay pantalla (DISPLAY vacío): corre  make captura  desde una terminal del escritorio (noVNC)."
    exit 1
fi

for i in $(seq "$SEG" -1 1); do
    printf '\r  Pon GTKWave al frente (maximizado). Foto en %d s... ' "$i"; sleep 1
done
printf '\r  Tomando la foto...                                      \n'

rm -f "$OUT"
if command -v import >/dev/null; then
    echo "  \$ import -window root $OUT"; import -window root "$OUT"
elif command -v xfce4-screenshooter >/dev/null; then
    echo "  \$ xfce4-screenshooter -f -s $OUT"; xfce4-screenshooter -f -s "$OUT"
elif command -v scrot >/dev/null; then
    echo "  \$ scrot -o $OUT"; scrot -o "$OUT"
elif command -v gnome-screenshot >/dev/null; then
    echo "  \$ gnome-screenshot -f $OUT"; gnome-screenshot -f "$OUT"
else
    echo "  \$ python3 (PIL.ImageGrab)"
    python3 -c "from PIL import ImageGrab; ImageGrab.grab().save('$OUT')" 2>/dev/null
fi

if [ -s "$OUT" ]; then
    echo "Listo: $OUT ($(du -h "$OUT" | cut -f1)). Revísala:  firefox $OUT &"
else
    echo "No pude tomar la foto con las herramientas de la imagen."
    echo "Plan B: en GTKWave, File -> Grab To File, y guárdala como $OUT"
    exit 1
fi
