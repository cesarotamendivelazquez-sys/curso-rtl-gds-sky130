#!/usr/bin/env python3
"""
run.py · Corre los tests de cocotb del lab03 con Icarus (SIM=icarus)
NO LO MODIFIQUES: make entrega revisa que esté igual que en el curso.

Se usa a través del Makefile (make cocotb), desde labs/lab03-verif:
    python3 cocotb/run.py                          los dos tests, tu RTL
    python3 cocotb/run.py --test test_dirigido     solo uno
    python3 cocotb/run.py --seed 7                 repite una corrida aleatoria
    python3 cocotb/run.py --rtl otro.v --build build/x --quiet   (lo usa el revisor)

Imprime una línea por test:  RESULTADO <test> PASS|FAIL|SKIP
"""
import argparse
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
RTL = "../../common/rtl/semaphore/rtl/semaphore.v"
TESTS = ("test_dirigido", "test_aleatorio")
# Tiempos distintos a los del TB base, a los de tb_ped_req y a los del RTL.
PARAMETROS = {"T_GREEN": 4, "T_YELLOW": 3, "T_RED": 5, "CW": 8}


def resultados(xml):
    """{test: PASS|FAIL|SKIP} leído del results.xml de cocotb."""
    res = {}
    if not xml.exists():
        return res
    for caso in ET.parse(xml).iter("testcase"):
        nombre = caso.get("name")
        if caso.find("skipped") is not None:
            res[nombre] = "SKIP"
        elif caso.find("failure") is not None or caso.find("error") is not None:
            res[nombre] = "FAIL"
        else:
            res[nombre] = "PASS"
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rtl", default=RTL)
    ap.add_argument("--test", choices=TESTS, action="append")
    ap.add_argument("--seed", type=int)
    ap.add_argument("--build", default="build/cocotb")
    ap.add_argument("--quiet", action="store_true", help="sin el log de la simulación")
    a = ap.parse_args()

    os.chdir(LAB)
    try:
        from cocotb_tools.runner import get_runner
    except ImportError:
        print("no encuentro cocotb 2.x (cocotb_tools): ¿estás dentro del contenedor?")
        return 2

    build = Path(a.build)
    build.mkdir(parents=True, exist_ok=True)
    xml = build / "results.xml"
    xml.unlink(missing_ok=True)
    log = build / "sim.log"

    sim = get_runner("icarus")
    print(f"$ iverilog ... {a.rtl}   (cocotb, SIM=icarus, parámetros {PARAMETROS})")
    try:
        sim.build(sources=[a.rtl], hdl_toplevel="semaforo", parameters=PARAMETROS,
                  build_dir=build, always=True, waves=True, timescale=("1ns", "1ps"),
                  log_file=log if a.quiet else None)
    except Exception as e:                       # no compila: lo dice el log
        if a.quiet:
            print(log.read_text(errors="replace")[-1500:] if log.exists() else e)
        print(f"RESULTADO compilacion FAIL ({e.__class__.__name__})")
        return 1

    # La simulación corre dentro de build/ (ahí queda la onda semaforo.fst);
    # los tests se importan desde cocotb/.
    env = {k: str(v) for k, v in PARAMETROS.items()}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(LAB / "cocotb"), os.environ.get("PYTHONPATH")]))
    try:
        sim.test(test_module="test_semaforo", hdl_toplevel="semaforo",
                 test_dir=build, build_dir=build, results_xml=str(xml.resolve()),
                 testcase=a.test, seed=a.seed, waves=True, extra_env=env,
                 log_file=log if a.quiet else None)
    except Exception as e:
        print(f"(cocotb terminó con {e.__class__.__name__})")

    res = resultados(xml)
    for t in (a.test or TESTS):
        print(f"RESULTADO {t} {res.get(t, 'FAIL')}")
    return 0 if res and all(res.get(t) == "PASS" for t in (a.test or TESTS)) else 1


if __name__ == "__main__":
    sys.exit(main())
