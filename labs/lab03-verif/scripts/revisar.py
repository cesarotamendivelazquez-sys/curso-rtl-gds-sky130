#!/usr/bin/env python3
"""
revisar.py · Herramientas y revisores del lab03 (verificación funcional)

Se usa a través del Makefile, desde labs/lab03-verif:
    make guardado    paso 0: ¿todo tu RTL está en un commit?
    make sim         TB base (Icarus) con tu RTL -> PASS/FAIL + build/dump.vcd
    make respuestas  revisa respuestas.txt
    make mutantes    ¿tus tests de cocotb atrapan los 6 mutantes?
    make entrega     todo junto + onda + git

Cada objetivo imprime el comando real que corre: cópialo y pruébalo a mano.
"""
import contextlib
import hashlib
import io
import re
import struct
import subprocess
import sys
import unicodedata
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent          # labs/lab03-verif
BUILD = LAB / "build"

# Rutas relativas a la carpeta del lab: así se imprimen y así se corren.
RTL = "../../common/rtl/semaphore/rtl/semaphore.v"
TB_BASE = "../../common/rtl/semaphore/tb/tb_semaphore.v"
BUG = "formal/semaforo_bug.v"
TEST = "cocotb/test_semaforo.py"
GTKW = "entrega/onda_bug.gtkw"
PNG = "entrega/onda_bug.png"
MUTANTES = sorted((LAB / "scripts" / "mutantes").glob("m*.v"))

# Qué mutantes DEBE atrapar cada test (make entrega lo exige).
DEBE = {"test_dirigido": {"m1_amarillo_largo", "m2_secuencia", "m6_dos_luces"},
        "test_aleatorio": {m.stem for m in MUTANTES}}
SEMILLAS = (1, 2)                     # el aleatorio debe pasar con estas dos

# Huellas de los archivos del curso que no se tocan (make entrega las compara).
HUELLAS = {
    "cocotb/semaforo_tb.py": "7d208acef632d4d5ebbd1fc0c31b0196fc2d39565fbdd43b28671978be201c59",
    "cocotb/run.py": "d68211b6dde97dcf2a39bb17a0fb6c402eb5d94ffcf5da61e37833cee0164d04",
    "formal/semaforo_bug.v": "631c7ad22918f964833d232abfeb3e54eed98539644bce1fa3b1bbdd6dc91dc0",
    "formal/formal_top.v": "6229db614cc6030c340eaf88c81dd4d8d516d807f8830ec5d80c752f323945e8",
}

# Huella conjunta de los mutantes (nombre + contenido de cada uno).
HUELLA_MUTANTES = "8676220f5594e954534f8bb525cc1761492eea9e7217c359af64573f3012ef79"


def huella_mutantes():
    h = hashlib.sha256()
    for m in MUTANTES:
        h.update(m.name.encode() + b"\0" + m.read_bytes())
    return h.hexdigest()


V, R, A, N = "\033[32m", "\033[31m", "\033[33m", "\033[0m"
if not sys.stdout.isatty():
    V = R = A = N = ""
OK, MAL, AV = f"{V}[ OK ]{N}", f"{R}[MAL ]{N}", f"{A}[ ?? ]{N}"


def correr(cmd, cwd=LAB, mostrar=True, timeout=300):
    """Corre una lista de argumentos e imprime antes el comando (en relativo)."""
    if mostrar:
        print(f"$ {' '.join(map(str, cmd))}")
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError:
        return 127, "", f"no encuentro '{cmd[0]}': ¿estás dentro del contenedor iic-osic-tools?"
    except subprocess.TimeoutExpired:
        return 124, "", "se tardó demasiado (¿un while que nunca termina?)"
    return r.returncode, r.stdout, r.stderr


def git(*args):
    r = subprocess.run(["git", *args], cwd=LAB, capture_output=True, text=True)
    return r.returncode, r.stdout.strip()


# ---------------------------------------------------------------------
#  Paso 0 · guardado
# ---------------------------------------------------------------------
def cmd_guardado():
    print("== Paso 0: ¿tu trabajo está en un commit? ==")
    print("$ git status --short ../../common")
    _, cambios = git("status", "--short", "--", "../../common")
    _, rama = git("branch", "--show-current")
    rtl = (LAB / RTL).read_text(encoding="utf-8")
    bien = True
    if rama.startswith("alumno/"):
        print(f"  {OK} rama {rama}")
    else:
        bien = False
        print(f"  {MAL} rama {rama}\n         -> git switch alumno/<tu-nombre>")
    if re.search(r"\binput\s+(wire\s+)?ped_req\b", rtl):
        print(f"  {OK} tu semaforo tiene ped_req (lab02)")
    else:
        bien = False
        print(f"  {MAL} tu semaforo no tiene ped_req: ¿hiciste git pull upstream main desde tu rama?")
    if cambios:
        bien = False
        print(f"  {MAL} hay cambios SIN commit:")
        print("\n".join("         " + l for l in cambios.splitlines()))
        print("         -> git add ../../common && git commit -m \"lab02: cambios pendientes\"")
    else:
        _, ult = git("log", "--oneline", "-1", "--", RTL)
        print(f"  {OK} nada sin commit en ../../common")
        print(f"         tu RTL está guardado en: {ult}")
    print()
    if bien:
        print(f"{V}== GUARDADO: ya puedes romper semaphore.v; git restore lo regresa a ese commit =={N}")
        return 0
    print(f"{R}== NO SIGAS: arregla lo de arriba antes de meter el bug =={N}")
    return 1


# ---------------------------------------------------------------------
#  Simulación del TB base
# ---------------------------------------------------------------------
def sim_tb(rtl, carpeta, mostrar=True):
    """Compila y corre el TB base con un RTL. Regresa (estado, líneas, vcd)."""
    out_dir = BUILD / carpeta
    out_dir.mkdir(parents=True, exist_ok=True)
    rel = out_dir.relative_to(LAB)
    rc, out, err = correr(["iverilog", "-g2012", "-o", f"{rel}/sim_semaforo", rtl, TB_BASE],
                          mostrar=mostrar)
    msgs = list(dict.fromkeys((out + err).strip().splitlines()))     # Icarus 14 repite errores
    if rc != 0:
        return "no compila", msgs, None
    rc, out, err = correr(["vvp", "-n", "sim_semaforo"], cwd=out_dir, mostrar=False)
    if mostrar:
        print(f"$ cd {rel} && vvp -n sim_semaforo")
    sal = [l for l in (out + err).splitlines() if "$finish called" not in l]
    if any(">>> PASS" in l for l in sal):
        estado = "PASS"
    else:
        estado = "FAIL"
    return estado, msgs + sal, out_dir / "dump.vcd"


def cmd_sim():
    estado, lineas, _ = sim_tb(RTL, ".")
    fails = [l for l in lineas if "FAIL:" in l and not l.startswith(">>>")]
    for l in lineas[:12]:
        print("  " + l)
    if len(lineas) > 12:
        print(f"  ... ({len(lineas) - 12} líneas más)")
    print()
    if estado == "PASS":
        print(f"{V}== TB base: PASS · onda en build/dump.vcd (make wave) =={N}")
    elif estado == "FAIL":
        print(f"{R}== TB base: FAIL · {len(fails)} violación(es) · ábrela con  make wave =={N}")
        print(f"   El TB imprime el tiempo con %t: sale en ps (precisión 1ps). 1 ns = 1000 ps.")
    else:
        print(f"{R}== TB base: NO COMPILA (error arriba) =={N}")
    return 0


# ---------------------------------------------------------------------
#  Respuestas (parte 2)
# ---------------------------------------------------------------------
#  Las respuestas no están aquí: solo su huella.
PREGUNTAS = {
    "R1": ("numero", "c56658e158fcbbea",
           "es el primer [tiempo] FAIL de make sim, pero en ns (el TB lo imprime en ps)"),
    "R2": ("numero", "09ba59145457ccc4",
           "lee state en GTKWave donde pusiste el marcador (es un número de 0 a 3)"),
    "R3": ("letra", "c20978e21f09dab0",
           "mira la instancia dut en tb_semaphore.v: ¿qué le conectaste a ped_req en el lab02?"),
}


def normaliza(tipo, texto):
    t = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()
    if tipo == "letra":
        m = re.fullmatch(r"\W*([a-d])\W*", t)
        return m.group(1) if m else t.strip()
    m = re.search(r"\d+", t)
    return str(int(m.group(0))) if m else ""          # "01" (binario de GTKWave) -> "1"


def huella(clave, valor):
    return hashlib.sha256(f"lab03:{clave}:{valor}".encode()).hexdigest()[:16]


def respuestas_datos():
    texto = (LAB / "respuestas.txt").read_text(encoding="utf-8")
    resp = dict(re.findall(r"^(R\d):[ \t]*(.*)$", texto, re.M))
    res = []
    for k, (tipo, h, pista) in PREGUNTAS.items():
        r = resp.get(k, "").strip()
        n = normaliza(tipo, r)
        ok = bool(r) and huella(k, n) == h
        if k == "R1" and not ok and n.endswith("000") and huella(k, n[:-3]) == h:
            pista = "ese número está en ps: pásalo a ns (divide entre 1000)"
        res.append((k, r, ok, pista))
    return res


def cmd_respuestas():
    res = respuestas_datos()
    print("== Respuestas del lab03 ==")
    for k, r, ok, pista in res:
        if not r:
            print(f"  {AV} {k}: sin respuesta")
        elif ok:
            print(f"  {OK} {k}: {r}")
        else:
            print(f"  {MAL} {k}: {r}\n         -> pista: {pista}")
    bien = sum(1 for _, _, ok, _ in res if ok)
    print(f"== {bien}/{len(res)} ==")
    return 0


# ---------------------------------------------------------------------
#  cocotb: tus tests, con tu RTL y con los mutantes
# ---------------------------------------------------------------------
def cocotb(rtl=RTL, carpeta="cocotb", tests=None, semilla=1):
    """Corre run.py en silencio. Regresa ({test: PASS|FAIL|SKIP}, log)."""
    cmd = [sys.executable, "cocotb/run.py", "--rtl", rtl, "--build", f"build/{carpeta}",
           "--quiet", "--seed", str(semilla)]
    for t in tests or ():
        cmd += ["--test", t]
    rc, out, err = correr(cmd, mostrar=False)
    res = dict(re.findall(r"^RESULTADO (\w+) (\w+)", out, re.M))
    log = BUILD / carpeta / "sim.log"
    return res, (log.read_text(errors="replace") if log.exists() else out + err)


def descripcion(mutante):
    m = re.search(r"MUTANTE \w+: (.*)", mutante.read_text(encoding="utf-8"))
    return m.group(1) if m else ""


def mutantes_datos(mostrar=True):
    """{mutante: {test: FAIL|PASS}}; FAIL quiere decir que el test lo atrapó."""
    datos = {}
    if mostrar:
        print(f"  ... corriendo {len(MUTANTES)} mutantes con tus dos tests")
    for m in MUTANTES:
        res, _ = cocotb(str(m.relative_to(LAB)), f"mutantes/{m.stem}")
        datos[m.stem] = res
    return datos


def cmd_mutantes():
    print("== Mutantes: ¿tus tests atrapan estos bugs? ==")
    print("$ python3 cocotb/run.py --rtl scripts/mutantes/<mutante>.v ...   (uno por mutante)")
    base, _ = cocotb()
    if any(base.get(t) != "PASS" for t in DEBE):
        print(f"  {R}Primero tus dos tests deben pasar con TU RTL{N} "
              f"(dirigido: {base.get('test_dirigido', 'FAIL')}, aleatorio: {base.get('test_aleatorio', 'FAIL')}).")
        print("  Un test que falla siempre 'atrapa' todo y no sirve. Corre  make cocotb.")
        return 0
    datos = mutantes_datos()
    print(f"  {'mutante':<20} {'qué rompe':<52} {'dirigido':<11} aleatorio")
    faltan = 0
    for m in MUTANTES:
        celdas = []
        for t in DEBE:
            atrapo = datos[m.stem].get(t) == "FAIL"
            debe = m.stem in DEBE[t]
            if atrapo:
                celdas.append(f"{V}{'ATRAPADO':<11}{N}")
            elif debe:
                faltan += 1
                celdas.append(f"{R}{'SE ESCAPA':<11}{N}")
            else:
                celdas.append(f"{'(no aplica)':<11}")
        print(f"  {m.stem:<20} {descripcion(m):<52} {celdas[0]} {celdas[1]}")
    print()
    if faltan:
        print(f"{R}== {faltan} mutante(s) se escapan de un test que debía atraparlos =={N}")
        print("   Dirigido: debe revisar el ORDEN y la DURACIÓN (m1, m2, m6).")
        print("   Aleatorio: su estímulo debe apretar el botón en todos los colores y dar resets a medio estado.")
    else:
        print(f"{V}== Tus tests atrapan todos los mutantes =={N}")
    return 0


# ---------------------------------------------------------------------
#  La onda: entrega/onda_bug.gtkw y entrega/onda_bug.png
# ---------------------------------------------------------------------
def vcd_intervalos_dos_luces(vcd):
    """Intervalos [ini, fin) del VCD con más de una luz encendida (en unidades del VCD)."""
    ids, val, t, ivs, ini = {}, {}, 0, [], None
    for l in vcd.read_text(errors="replace").splitlines():
        l = l.strip()
        p = l.split()
        if l.startswith("$var") and len(p) >= 5 and p[4] in ("red", "yellow", "green"):
            ids.setdefault(p[3], p[4])
        elif l.startswith("#"):
            nuevo = int(l[1:])
            if nuevo != t:
                n = sum(val.values())
                if n > 1 and ini is None:
                    ini = t
                elif n <= 1 and ini is not None:
                    ivs.append((ini, t)); ini = None
            t = nuevo
        elif l and l[0] in "01xz" and l[1:] in ids:
            val[ids[l[1:]]] = 1 if l[0] == "1" else 0
    if ini is not None:
        ivs.append((ini, t + 1))
    return ivs


def gtkw_datos(texto):
    """(señales, marcador) de un archivo de GTKWave (File -> Write Save File)."""
    senales = [l.strip() for l in texto.splitlines()
               if l.strip() and not l.startswith(("[", "*", "@", "-"))]
    m = re.search(r"^\*[-\d.e]+ (-?\d+)", texto, re.M)
    marcador = int(m.group(1)) if m else -1
    return senales, marcador


def png_tamano(ruta):
    datos = ruta.read_bytes()[:32]
    if datos[:8] != b"\x89PNG\r\n\x1a\n" or datos[12:16] != b"IHDR":
        return None
    return struct.unpack(">II", datos[16:24])


def onda_revisa():
    """Lista de (bien, mensaje, pista) sobre la captura de la onda."""
    res = []
    g = LAB / GTKW
    if not g.exists():
        res.append((False, f"{GTKW} no existe",
                    "parte 2: en GTKWave, File -> Write Save File, guárdalo con ese nombre"))
    else:
        senales, marcador = gtkw_datos(g.read_text(errors="replace"))
        faltan = [s for s in ("state", "cnt", "red", "yellow", "green")
                  if not any(re.search(rf"(^|\.){s}(\[|$)", x) for x in senales)]
        res.append((not faltan, "onda_bug.gtkw: state, cnt y las 3 luces" if not faltan
                    else f"onda_bug.gtkw: faltan {', '.join(faltan)}",
                    "agrégalas en GTKWave (doble clic o Append) y vuelve a guardar"))
        with contextlib.redirect_stdout(io.StringIO()):
            estado, _, vcd = sim_tb(BUG, "revisor_bug", mostrar=False)
        ivs = vcd_intervalos_dos_luces(vcd) if vcd and vcd.exists() else []
        if marcador < 0:
            res.append((False, "onda_bug.gtkw: sin marcador",
                        "clic en la onda en el primer ciclo con dos luces y vuelve a guardar"))
        elif not ivs:
            res.append((False, "no pude simular el bug de referencia", f"revisa que {BUG} esté igual que en el curso"))
        else:
            ini, fin = ivs[0]
            dentro = ini <= marcador < fin
            res.append((dentro, f"marcador en {marcador / 1000:g} ns" +
                        (": en el primer intervalo con dos luces" if dentro else ": fuera del primer intervalo con dos luces"),
                        "pon el marcador donde amarillo y verde están en 1 a la vez, la PRIMERA vez"))
    p = LAB / PNG
    tam = png_tamano(p) if p.exists() else None
    if not p.exists():
        res.append((False, f"{PNG} no existe", "parte 2: make captura con GTKWave al frente"))
    else:
        bien = bool(tam) and tam[0] >= 400 and tam[1] >= 300
        res.append((bien, f"onda_bug.png: {tam[0]}x{tam[1]}" if tam else "onda_bug.png no es un PNG",
                    "repite  make captura  (o en GTKWave: File -> Grab To File)"))
    return res


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


def cmd_entrega():
    print("== Entrega lab03 ==")
    bien = sum(1 for _, _, ok, _ in respuestas_datos() if ok)
    rep(bien == len(PREGUNTAS), f"Respuestas: {bien}/{len(PREGUNTAS)}", "corre  make respuestas")

    with contextlib.redirect_stdout(io.StringIO()):
        estado, _, _ = sim_tb(RTL, "revisor_base", mostrar=False)
    rep(estado == "PASS", f"TB base con tu RTL: {estado}",
        "¿quedó el bug? git restore ../../common/rtl/semaphore/rtl/semaphore.v y make sim")

    for f, h in HUELLAS.items():
        p = LAB / f
        actual = hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else ""
        rep(actual == h, f"{f} sin cambios", f"regrésalo al original:  git restore --source=upstream/main {f}")
    rep(huella_mutantes() == HUELLA_MUTANTES, f"scripts/mutantes sin cambios ({len(MUTANTES)} mutantes)",
        "regrésalos al original:  git restore --source=upstream/main scripts/mutantes")

    print("  ... corriendo tus tests de cocotb (make cocotb muestra el detalle)")
    res, log_d = cocotb(tests=["test_dirigido"], carpeta="revisor_dirigido")
    rep(res.get("test_dirigido") == "PASS", f"test_dirigido con tu RTL: {res.get('test_dirigido', 'FAIL')}",
        "corre  make cocotb TEST=test_dirigido  y lee el error")
    rep("comparador contra el modelo: ACTIVO" not in log_d, "test_dirigido revisa sin el modelo",
        "en el dirigido usa  await tb.arranca()  sin modelo=True: ahí el que revisa eres tú")
    for s in SEMILLAS:
        res, log_a = cocotb(tests=["test_aleatorio"], carpeta=f"revisor_aleatorio_{s}", semilla=s)
        rep(res.get("test_aleatorio") == "PASS", f"test_aleatorio con tu RTL, semilla {s}: {res.get('test_aleatorio', 'FAIL')}",
            f"corre  make cocotb TEST=test_aleatorio SEED={s}  y lee el error")
    rep("cobertura: OK" in log_a, "test_aleatorio: cobertura completa",
        "¿llamas a tb.cierra() al final? ¿el estímulo aprieta el botón en los 3 colores y da 3+ resets?")

    print("  ... corriendo los mutantes (make mutantes muestra la tabla)")
    datos = mutantes_datos(mostrar=False)
    for t, deben in DEBE.items():
        escapan = sorted(m for m in deben if datos.get(m, {}).get(t) != "FAIL")
        rep(not escapan, f"{t} atrapa {len(deben) - len(escapan)}/{len(deben)} mutantes",
            f"se escapan: {', '.join(escapan)} · corre  make mutantes")

    for bien_o, msg, pista in onda_revisa():
        rep(bien_o, msg, pista)

    _, rama = git("branch", "--show-current")
    rep(rama.startswith("alumno/"), f"Rama: {rama}", "git switch alumno/<tu-nombre>")
    for f in (TEST, "respuestas.txt", GTKW, PNG):
        rc, _ = git("ls-files", "--error-unmatch", f)
        _, cambios = git("status", "--porcelain", "--", f)
        rep(rc == 0 and not cambios, f"{Path(f).name} con commit", f"git add {f} && git commit")
    _, comun = git("status", "--porcelain", "--", "../../common")
    rep(not comun, "../../common sin cambios pendientes", "git status ../../common")
    rc, _ = git("rev-parse", "-q", "--verify", "@{u}")
    if rc == 0:
        _, pend = git("rev-list", "--count", "@{u}..HEAD")
        rep(pend == "0", "Todo subido a GitHub", "git push")
    else:
        rep(False, "Tu rama no está en GitHub", "git push -u origin $(git branch --show-current)")

    print(f"== {'LISTO para entregar' if fallas == 0 else f'{fallas} punto(s) por corregir'} ==")
    return 1 if fallas else 0


if __name__ == "__main__":
    acciones = {"guardado": cmd_guardado, "sim": cmd_sim, "respuestas": cmd_respuestas,
                "mutantes": cmd_mutantes, "entrega": cmd_entrega}
    if len(sys.argv) != 2 or sys.argv[1] not in acciones:
        print(f"uso: {sys.argv[0]} {{{'|'.join(acciones)}}}")
        sys.exit(2)
    sys.exit(acciones[sys.argv[1]]())
