#!/usr/bin/env python3
"""
revisar_entrega.py · ¿Está lista la entrega del lab01?
Se corre con:  make entrega   (desde labs/lab01-linux-pdk)

Revisa: notas_pdk.md lleno, pdk_info.sh terminado y todo con commit + push.
"""
import re
import subprocess
import sys
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
OK, MAL, AV = "\033[32m[ OK ]\033[0m", "\033[31m[MAL ]\033[0m", "\033[33m[ ?? ]\033[0m"
if not sys.stdout.isatty():
    OK, MAL, AV = "[ OK ]", "[MAL ]", "[ ?? ]"

fallas = 0


def rep(bien, msg, pista=""):
    global fallas
    if bien:
        print(f"  {OK} {msg}")
    else:
        fallas += 1
        print(f"  {MAL} {msg}" + (f"\n         -> {pista}" if pista else ""))


def git(*args):
    r = subprocess.run(["git", *args], cwd=LAB, capture_output=True, text=True)
    return r.returncode, r.stdout.strip()


print("== Entrega lab01 ==")

# ---- notas_pdk.md ------------------------------------------------------
notas = (LAB / "notas_pdk.md").read_text(encoding="utf-8")
filas = [l for l in notas.splitlines() if l.startswith("| sky130_fd_sc_hd__") or l.startswith("| (elige")]
llenas = 0
for f in filas:
    celdas = [c.strip() for c in f.strip().strip("|").split("|")]
    if len(celdas) >= 5 and all(celdas) and not celdas[0].startswith("(elige"):
        llenas += 1
rep(llenas >= 3, f"Tabla de celdas: {llenas}/3 renglones completos",
    "usa ./pdk_info.sh <celda>; la tercera celda la eliges tú")

sec = notas.split("## 2.")[1].split("## 3.")[0] if "## 2." in notas else ""
corners = set(re.findall(r"\b(?:tt|ss|ff|sf|fs)_n?\d+C_\dv\d\d(?:_ccsnoise)?\b", sec))
rep(len(corners) >= 3, f"Corners listados: {len(corners)}", "lista los .lib de libs.ref/sky130_fd_sc_hd/lib/")

def campo(k):
    """Valor después de '**k:**', aunque lo hayan escrito dentro de las negritas: '**k: valor**'."""
    m = re.search(rf"^\*\*{re.escape(k)}:?\s*(.*)$", notas, re.M)
    return re.sub(r"[*\s]", "", m.group(1)) if m else ""


cab = {k: campo(k) for k in ("Nombre", "PDK_ROOT que usé")}
rep(all(cab.values()), "Encabezado (nombre y PDK_ROOT)", "llena las primeras líneas de notas_pdk.md")

resp = re.findall(r"^\s+- (.*)$", notas.split("## 3.")[1], re.M) if "## 3." in notas else []
rep(sum(1 for r in resp if r.strip()) >= 3, "Las 3 preguntas tienen respuesta")

# ---- retos de rutas ----------------------------------------------------
r = subprocess.run([sys.executable, str(LAB / "scripts/revisar_rutas.py")], cwd=LAB, capture_output=True, text=True)
m = re.search(r"== (\d+)/(\d+) ==", r.stdout)
bien_rutas, total = (int(m.group(1)), int(m.group(2))) if m else (0, 8)
rep(bien_rutas == total, f"Retos de rutas: {bien_rutas}/{total}", "corre  make rutas  para ver cuáles faltan")

# ---- pdk_info.sh -------------------------------------------------------
script = (LAB / "pdk_info.sh").read_text(encoding="utf-8")
vacios = len(re.findall(r"^(AREA|TAMANO|PINES)=\$\(\s*\)", script, re.M))
rep(vacios == 0, f"pdk_info.sh: {3 - vacios}/3 TODO llenos", "llena AREA, TAMANO y PINES (README, parte 4.3)")
r = subprocess.run(["bash", "-c", "./pdk_info.sh nand2_1"], cwd=LAB, capture_output=True, text=True)
rep(r.returncode == 0 and "TODO" not in r.stdout, "pdk_info.sh nand2_1 imprime área, tamaño y pines",
    r.stderr.strip()[:120] or "aún imprime TODO")

# ---- git ---------------------------------------------------------------
for f in ("notas_pdk.md", "pdk_info.sh", "respuestas_rutas.txt"):
    rc, _ = git("ls-files", "--error-unmatch", f)
    _, cambios = git("status", "--porcelain", f)
    rep(rc == 0 and not cambios, f"{f} con commit", f"git add {f} && git commit")
rc, _ = git("rev-parse", "-q", "--verify", "@{u}")
if rc == 0:
    _, pend = git("rev-list", "--count", "@{u}..HEAD")
    rep(pend == "0", "Todo subido a GitHub", "git push")
else:
    rep(False, "Tu rama no está en GitHub", "git push -u origin $(git branch --show-current)")

print(f"== {'LISTO para entregar' if fallas == 0 else f'{fallas} punto(s) por corregir'} ==")
sys.exit(1 if fallas else 0)
