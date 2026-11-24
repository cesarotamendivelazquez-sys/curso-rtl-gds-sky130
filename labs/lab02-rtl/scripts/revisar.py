#!/usr/bin/env python3
"""
revisar.py · Herramientas y revisores del lab02 (RTL sintetizable y FSM)

Se usa a través del Makefile, desde labs/lab02-rtl:
    make lint        Verilator --lint-only -Wall sobre tu semaphore.v
    make latch       ¿Yosys infiere algún latch?
    make sim         TB base + tb_ped_req (Icarus)
    make preguntas   revisa preguntas.txt
    make entrega     todo junto + git

Cada objetivo imprime el comando real que corre: cópialo y pruébalo a mano.
"""
import hashlib
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent          # labs/lab02-rtl
REPO = LAB.parent.parent
BUILD = LAB / "build"

# Rutas relativas a la carpeta del lab: así se imprimen y así se corren.
RTL = "../../common/rtl/semaphore/rtl/semaphore.v"
TB_BASE = "../../common/rtl/semaphore/tb/tb_semaphore.v"
SDC = "../../common/sdc/semaforo.sdc"
TB_PED = "tb/tb_ped_req.v"

# Huella de tb/tb_ped_req.v tal como viene en el curso (make entrega la compara).
TB_PED_SHA256 = "2a613fca175d053d520deaa337f278a1b1e02075ae22088c6fa5af1ef4393f67"

V, R, A, N = "\033[32m", "\033[31m", "\033[33m", "\033[0m"
if not sys.stdout.isatty():
    V = R = A = N = ""
OK, MAL, AV = f"{V}[ OK ]{N}", f"{R}[MAL ]{N}", f"{A}[ ?? ]{N}"


def correr(cmd, cwd=LAB, mostrar=True):
    """Corre una lista de argumentos e imprime antes el comando (en relativo)."""
    if mostrar:
        print(f"$ {' '.join(cmd)}")
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=120)
    except FileNotFoundError:
        return 127, "", f"no encuentro '{cmd[0]}': ¿estás dentro del contenedor iic-osic-tools?"
    return r.returncode, r.stdout, r.stderr


# ---------------------------------------------------------------------
#  Lint
# ---------------------------------------------------------------------
def lint_datos():
    rc, out, err = correr(["verilator", "--lint-only", "-Wall", RTL], mostrar=False)
    texto = out + err
    codigos = re.findall(r"%Warning-(\w+):", texto)
    errores = re.findall(r"%Error(?:-(\w+))?: (?!Exiting due to)", texto)
    return rc, texto, codigos, errores


def cmd_lint():
    print(f"$ verilator --lint-only -Wall {RTL}")
    rc, texto, codigos, errores = lint_datos()
    print(texto.rstrip() or "(sin mensajes)")
    print()
    if rc == 0 and not codigos:
        print(f"{V}== LINT LIMPIO: 0 warnings =={N}")
    elif errores:
        print(f"{R}== ERROR de sintaxis: Verilator no pudo leer el archivo (mira la línea que señala) =={N}")
    else:
        cuenta = {}
        for c in codigos:
            cuenta[c] = cuenta.get(c, 0) + 1
        resumen = ", ".join(f"{c} x{n}" for c, n in cuenta.items())
        print(f"{A}== {len(codigos)} warning(s): {resumen} =={N}")
    return 0


# ---------------------------------------------------------------------
#  Latches (Yosys, pase proc)
# ---------------------------------------------------------------------
def latch_datos():
    rc, out, err = correr(["yosys", "-p", f"read_verilog {RTL}; proc"], mostrar=False)
    # Yosys 0.33 imprime "Latch inferred for signal ..."; Yosys 0.69 lo imprime
    # como "Warning: Latch inferred for signal `\\semaforo.\\limit [2:0]' ...".
    lineas = [l for l in (out + err).splitlines() if "atch inferred for signal" in l]
    lineas = list(dict.fromkeys(lineas))          # sin repetidos (stdout + stderr)
    hay = [l for l in lineas if es_latch(l)]
    return rc, out + err, lineas, hay


def es_latch(linea):
    return not re.match(r"\s*No latch inferred", linea)


def cmd_latch():
    print(f'$ yosys -p "read_verilog {RTL}; proc" | grep -i "latch inferred"')
    rc, texto, lineas, hay = latch_datos()
    if rc != 0:
        print(texto[-1500:])
        print(f"{R}== Yosys no pudo leer el diseño (error arriba) =={N}")
        return 0
    # Yosys 0.69 parte una señal en tramos (limit [2:0], limit [7:3]): se agrupa por señal.
    senales = {}
    for l in lineas:
        senal = re.search(r"signal `\\[^.]+\.\\([^']+)'", l)
        nombre = re.sub(r"\s*\[[^\]]*\]$", "", senal.group(1)) if senal else l
        senales[nombre] = senales.get(nombre, False) or es_latch(l)
    for nombre, latch in senales.items():
        print(f"  {R}LATCH    {N}  {nombre}" if latch else f"  {V}sin latch{N}  {nombre}")
    hay = [n for n, latch in senales.items() if latch]
    print()
    if hay:
        print(f"{R}== LATCH en: {', '.join(hay)} · una señal combinacional no tiene valor en todos los caminos =={N}")
    else:
        print(f"{V}== SIN LATCHES: toda señal combinacional tiene valor en todos los caminos =={N}")
    return 0


# ---------------------------------------------------------------------
#  Simulación
# ---------------------------------------------------------------------
def sim_una(nombre, tb, exe, marca_pass):
    """Compila y corre un TB. Regresa (ok, avisos_de_puertos, resumen)."""
    BUILD.mkdir(exist_ok=True)
    print(f"--- {nombre} ---")
    rc, out, err = correr(["iverilog", "-g2012", "-Wportbind", "-o", f"build/{exe}", RTL, tb])
    msgs = list(dict.fromkeys((out + err).strip().splitlines()))   # Icarus 14 repite errores
    avisos = [l for l in msgs if "dangling" in l or "warning" in l.lower()]
    for l in msgs:
        print("  " + l)
    if rc != 0:
        if "is not a port of" in err and "ped_req" in err:
            print(f"  {A}pista:{N} tu módulo semaforo todavía no tiene la entrada ped_req (parte 3, paso 1)")
        return False, avisos, "no compila"
    rc, out, err = correr(["vvp", "-n", exe], cwd=BUILD)
    sal = [l for l in (out + err).splitlines() if not l.startswith("VCD info") and "$finish called" not in l]
    print("\n".join("  " + l for l in sal))
    ok = any(marca_pass in l for l in sal)
    return ok, avisos, "PASS" if ok else "FAIL"


def sim_todo():
    base = sim_una("TB base (tb_semaphore.v)", TB_BASE, "sim_semaforo", ">>> PASS")
    ped = sim_una("Revisor del botón (tb_ped_req.v)", TB_PED, "sim_ped_req", ">>> PASS")
    return base, ped


def cmd_sim():
    (ok_b, av_b, _), (ok_p, _, _) = sim_todo()
    print()
    if av_b:
        print(f"{A}Ojo:{N} Icarus avisa de un puerto sin conectar en el TB base: conecta .ped_req(1'b0) en {TB_BASE}")
    print(f"== TB base: {'PASS' if ok_b else 'FAIL'} · tb_ped_req: {'PASS' if ok_p else 'FAIL'} ==")
    return 0


# ---------------------------------------------------------------------
#  Preguntas (parte 1)
# ---------------------------------------------------------------------
#  Las respuestas no están aquí: solo su huella. Normalización por tipo:
#    letra -> la letra A-D · numero -> los dígitos · palabra -> 4 primeras letras
PREGUNTAS = {
    "P1": ("letra", "8fe9b2a7e0c810d2",
           "es la pieza donde un case dice a qué color sigue cada color"),
    "P2": ("letra", "24152af2c224832d",
           "busca dónde está la condición que hoy dice 'se acabó el tiempo'"),
    "P3": ("numero", "0b65e36f07ac749d",
           "solo cuentan los reg que se escriben en el always @(posedge clk); suma sus anchos"),
    "P4": ("palabra", "6728dad4826621a3",
           "¿se escribe en un always @(*) o en un always @(posedge clk)?"),
    "P5": ("palabra", "3bfbe06e44cedf63",
           "¿las luces dependen solo del estado, o también de la entrada en ese momento?"),
}


def normaliza(tipo, texto):
    t = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()
    t = re.sub(r"\bpieza\b", "", t)
    if tipo == "letra":
        m = re.fullmatch(r"\W*([a-d])\W*", t)
        return m.group(1) if m else t.strip()
    if tipo == "numero":
        return "".join(re.findall(r"\d", t))
    return re.sub(r"[^a-z]", "", t)[:4]


def huella(clave, valor):
    return hashlib.sha256(f"lab02:{clave}:{valor}".encode()).hexdigest()[:16]


def preguntas_datos():
    texto = (LAB / "preguntas.txt").read_text(encoding="utf-8")
    resp = dict(re.findall(r"^(P\d):[ \t]*(.*)$", texto, re.M))
    res = []
    for k, (tipo, h, pista) in PREGUNTAS.items():
        r = resp.get(k, "").strip()
        res.append((k, r, bool(r) and huella(k, normaliza(tipo, r)) == h, pista))
    return res


def cmd_preguntas():
    res = preguntas_datos()
    print("== Preguntas del lab02 ==")
    for k, r, ok, pista in res:
        if not r:
            print(f"  {AV} {k}: sin respuesta")
        elif ok:
            print(f"  {OK} {k}: {r}")
        else:
            print(f"  {MAL} {k}: {r}\n         -> pista: {pista}")
    bien = sum(1 for *_, ok, _ in res if ok)
    print(f"== {bien}/{len(res)} ==")
    return 0


# ---------------------------------------------------------------------
#  Entrega
# ---------------------------------------------------------------------
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


def cmd_entrega():
    print("== Entrega lab02 ==")
    rtl = (LAB / RTL).read_text(encoding="utf-8")

    bien = sum(1 for *_, ok, _ in preguntas_datos() if ok)
    rep(bien == len(PREGUNTAS), f"Preguntas: {bien}/{len(PREGUNTAS)}", "corre  make preguntas  para ver cuáles faltan")

    rep(re.search(r"\binput\s+(wire\s+)?ped_req\b", rtl), "semaforo tiene la entrada ped_req",
        "agrégala a la lista de puertos (parte 3, paso 1)")

    rc, _, codigos, errores = lint_datos()
    rep(rc == 0 and not codigos and not errores, f"Lint con -Wall: {len(codigos)} warning(s)",
        "corre  make lint  y arréglalos (parte 5)")

    apagados = re.findall(r"lint_off(?:\s+(\w+))?", rtl)
    otros = sorted({a or "(todos)" for a in apagados if a != "DECLFILENAME"})
    rep(not otros, "Solo se apaga DECLFILENAME" if not otros else f"Apagaste: {', '.join(otros)}",
        "esos warnings se arreglan en el código, no se apagan")

    rc, _, _, hay = latch_datos()
    rep(rc == 0 and not hay, "Sin latches (Yosys)" if not hay else "Yosys infiere latch(es)",
        "corre  make latch ; ¿dejaste un case sin default? (git restore lo regresa)")

    print("  ... simulando (make sim muestra el detalle)")
    import io, contextlib
    with contextlib.redirect_stdout(io.StringIO()):
        (ok_b, av_b, est_b), (ok_p, _, est_p) = sim_todo()
    rep(ok_b and not av_b, f"TB base: {est_b}" + (" con un puerto sin conectar" if av_b else ""),
        f"conecta .ped_req(1'b0) en {TB_BASE} y corre  make sim")
    rep(ok_p, f"tb_ped_req: {est_p}", "corre  make sim  y lee qué caso falla")

    actual = hashlib.sha256((LAB / TB_PED).read_bytes()).hexdigest()
    rep(actual == TB_PED_SHA256, "tb/tb_ped_req.v sin cambios",
        "regrésalo al original:  git restore --source=upstream/main tb/tb_ped_req.v")

    sdc = (LAB / SDC).read_text(encoding="utf-8")
    rep(re.search(r"^\s*set_input_delay\b.*\bped_req\b", sdc, re.M),
        "SDC: set_input_delay de ped_req activo", f"descomenta esa línea en {SDC}")

    _, rama = git("branch", "--show-current")
    rep(rama.startswith("alumno/"), f"Rama: {rama}", "git switch alumno/<tu-nombre>")
    for f in (RTL, TB_BASE, SDC, "preguntas.txt"):
        _, cambios = git("status", "--porcelain", "--", f)
        rep(not cambios, f"{Path(f).name} con commit", f"git add {f} && git commit")
    rc, _ = git("rev-parse", "-q", "--verify", "@{u}")
    if rc == 0:
        _, pend = git("rev-list", "--count", "@{u}..HEAD")
        rep(pend == "0", "Todo subido a GitHub", "git push")
    else:
        rep(False, "Tu rama no está en GitHub", "git push -u origin $(git branch --show-current)")

    print(f"== {'LISTO para entregar' if fallas == 0 else f'{fallas} punto(s) por corregir'} ==")
    return 1 if fallas else 0


if __name__ == "__main__":
    acciones = {"lint": cmd_lint, "latch": cmd_latch, "sim": cmd_sim,
                "preguntas": cmd_preguntas, "entrega": cmd_entrega}
    if len(sys.argv) != 2 or sys.argv[1] not in acciones:
        print(f"uso: {sys.argv[0]} {{{'|'.join(acciones)}}}")
        sys.exit(2)
    sys.exit(acciones[sys.argv[1]]())
