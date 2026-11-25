"""
test_semaforo.py · Tus tests del semáforo en cocotb (lab03, parte 3)
ESTE es el archivo que editas. Lo corre:  make cocotb

Herramientas que te da el banco (cocotb/semaforo_tb.py, no se toca):
    tb = Banco(dut)
    await tb.arranca()          reloj de 20 ns + checker de una sola luz + reset
    await tb.arranca(modelo=True)   lo mismo + modelo de referencia + cobertura
    tb.luz()                    "verde", "amarillo", "rojo", "ninguna" o "varias"
    tb.T["verde"]               cuántos ticks dura el verde (también "amarillo", "rojo")
    await tb.ticks(n)           espera n ticks
    await tb.pulso(n)           ped_req = 1 durante n ticks
    await tb.reset(n)           rst_n = 0 durante n ticks
    tb.cierra()                 resumen (y revisa la cobertura si hay modelo)

Para que un test falle cuando el diseño está mal: assert condicion, "mensaje".
"""
import random

import cocotb

from semaforo_tb import Banco


@cocotb.test()
async def test_dirigido(dut):
    """Dirigido: verde -> amarillo -> rojo, con la duración de cada estado (2 vueltas)."""
    tb = Banco(dut)
    await tb.arranca()          # sin modelo: aquí el que revisa eres tú

    # TODO 1 (parte 3.2): justo después de arranca() el semáforo acaba de salir
    # del reset. Durante 2 vueltas completas, revisa que:
    #   - los colores salgan en el orden verde -> amarillo -> rojo, y
    #   - cada color dure exactamente tb.T[color] ticks.
    # Pista: lee la luz con tb.luz(), avanza con await tb.ticks(1) y cuenta.
    raise NotImplementedError("TODO 1: escribe el test dirigido")

    tb.cierra()


@cocotb.test()
async def test_aleatorio(dut):
    """Aleatorio: pulsos de ped_req y resets al azar; checker y modelo siempre activos."""
    tb = Banco(dut)
    await tb.arranca(modelo=True)   # el comparador revisa cada tick contra el modelo

    # TODO 2 (parte 3.3): durante unos cientos de pasos, elige al azar qué hacer:
    #   - apretar el botón (tb.pulso) un número de ticks al azar,
    #   - dar un reset (tb.reset) de duración al azar (de vez en cuando, no siempre),
    #   - o solo esperar (tb.ticks) un número de ticks al azar.
    # Usa el módulo random (cocotb le pone la semilla: sale en el log como "seed").
    # Al final, tb.cierra() revisa la COBERTURA: si tu estímulo nunca apretó el
    # botón en algún color, o dio menos de 3 resets, el test falla.
    raise NotImplementedError("TODO 2: escribe el test aleatorio")

    tb.cierra()
