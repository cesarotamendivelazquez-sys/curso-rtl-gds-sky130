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

    # Solución: en cada vuelta, cada color debe salir en orden y durar tb.T[color].
    for vuelta in range(1, 3):
        for color in ("verde", "amarillo", "rojo"):
            luz = tb.luz()
            assert luz == color, f"vuelta {vuelta}: esperaba {color} y está {luz}"
            dura = 0
            while tb.luz() == color:
                dura += 1
                await tb.ticks(1)
                assert dura <= tb.T[color], f"vuelta {vuelta}: {color} dura más de {tb.T[color]} ticks"
            assert dura == tb.T[color], f"vuelta {vuelta}: {color} duró {dura} ticks y debía durar {tb.T[color]}"
            tb.log.info("vuelta %d: %-8s %d ticks  ok", vuelta, color, dura)

    tb.cierra()


@cocotb.test()
async def test_aleatorio(dut):
    """Aleatorio: pulsos de ped_req y resets al azar; checker y modelo siempre activos."""
    tb = Banco(dut)
    await tb.arranca(modelo=True)   # el comparador revisa cada tick contra el modelo
    
    for _ in range(300):
    	dado = random.random()
    	if dado < 0.30:
    		await tb.pulso(random.randint(1, 3))     # botón de 1 a 3 ticks
    	elif dado < 0.35:
    		await tb.reset(random.randint(1, 3))     # reset de 1 a 3 ticks
    	else:
    		await tb.ticks(random.randint(1, 6))     # solo esperar

    tb.cierra()
