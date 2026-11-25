"""
semaforo_tb.py · Banco de pruebas del semáforo en cocotb (lab03)
NO LO MODIFIQUES: make entrega revisa que esté igual que en el curso.

Aquí vive todo lo que NO es el test: el reloj, el reset, el checker de
"una sola luz", un modelo de referencia que corre junto al diseño y la
cobertura. Tus tests (test_semaforo.py) lo usan así:

    tb = Banco(dut)
    await tb.arranca()              # reloj de 20 ns + checker + reset
    tb.luz()                        # "verde", "amarillo", "rojo", "ninguna" o "varias"
    await tb.ticks(3)               # espera 3 ticks (flancos de bajada)
    await tb.pulso(2)               # ped_req = 1 durante 2 ticks
    await tb.reset(2)               # rst_n = 0 durante 2 ticks
    tb.T["amarillo"]                # cuántos ticks dura el amarillo
    tb.cierra()                     # resumen (y cobertura, si hay modelo)

Regla de tiempo: TODO se mueve en el flanco de BAJADA de clk. El diseño
cambia en el flanco de subida; a media vuelta ya está estable para leerlo
y es seguro cambiar sus entradas.

Escrito para cocotb 2.x (Clock(..., unit=), .value =, cocotb.start_soon).
"""
import os

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge

PERIODO_NS = 20                     # el mismo reloj del SDC del curso
COLORES = ("verde", "amarillo", "rojo")
SIGUIENTE = {"verde": "amarillo", "amarillo": "rojo", "rojo": "verde"}


def _parametro(dut, nombre):
    """Lee un parámetro del diseño; si el simulador no lo expone, del entorno."""
    try:
        return int(getattr(dut, nombre).value)
    except (AttributeError, TypeError, ValueError):
        return int(os.environ[nombre])


class Modelo:
    """Modelo de referencia: lo que el semáforo DEBERÍA hacer, en Python."""

    def __init__(self, T):
        self.T = T
        self.reinicia()

    def reinicia(self):
        self.color, self.cnt = "verde", 0

    def paso(self, ped_req):
        """Un flanco de subida con rst_n = 1."""
        if self.cnt == self.T[self.color] - 1 or (self.color == "verde" and ped_req):
            self.color, self.cnt = SIGUIENTE[self.color], 0
        else:
            self.cnt += 1


class Banco:
    def __init__(self, dut):
        self.dut = dut
        self.log = cocotb.log
        self.T = {c: _parametro(dut, p) for c, p in
                  zip(COLORES, ("T_GREEN", "T_YELLOW", "T_RED"))}
        self.modelo = None
        self.ciclos = 0
        # Cobertura del test aleatorio: ¿qué situaciones alcanzamos a probar?
        self.cob = {"boton en verde": 0, "boton en amarillo": 0, "boton en rojo": 0,
                    "resets": 0, "reset a medio estado": 0}

    # ------------------------------------------------------------------
    async def arranca(self, modelo=False):
        """Reloj, entradas en 0, checker de una sola luz y un reset inicial.

        modelo=True además arranca el modelo de referencia, el comparador
        ciclo a ciclo y la cobertura (para el test aleatorio).
        """
        self.dut.ped_req.value = 0
        self.dut.rst_n.value = 0
        Clock(self.dut.clk, PERIODO_NS, unit="ns").start(start_high=False)
        cocotb.start_soon(self._checker_una_luz())
        if modelo:
            self.modelo = Modelo(self.T)
            cocotb.start_soon(self._modelo())
            cocotb.start_soon(self._comparador())
            self.log.info("[banco] comparador contra el modelo: ACTIVO")
        self.log.info("[banco] tiempos: verde %d, amarillo %d, rojo %d ticks",
                      self.T["verde"], self.T["amarillo"], self.T["rojo"])
        await FallingEdge(self.dut.clk)
        await self.reset(2)

    async def ticks(self, n=1):
        """Espera n ticks (n flancos de bajada)."""
        for _ in range(n):
            await FallingEdge(self.dut.clk)

    async def pulso(self, n=1):
        """Aprieta el botón peatonal durante n ticks y lo suelta."""
        self.dut.ped_req.value = 1
        await self.ticks(n)
        self.dut.ped_req.value = 0

    async def reset(self, n=1):
        """rst_n = 0 durante n ticks (n >= 1) y lo suelta. Se llama en flanco de bajada."""
        if self.modelo and self.modelo.cnt > 0:
            self.cob["reset a medio estado"] += 1
        self.cob["resets"] += 1
        self.dut.rst_n.value = 0
        await self.ticks(max(1, n))
        self.dut.rst_n.value = 1

    def luz(self):
        """Qué luz está encendida AHORA: 'verde', 'amarillo', 'rojo', 'ninguna' o 'varias'."""
        r, a, v = (int(self.dut.red.value), int(self.dut.yellow.value), int(self.dut.green.value))
        if r + a + v == 0:
            return "ninguna"
        if r + a + v > 1:
            return "varias"
        return "rojo" if r else "amarillo" if a else "verde"

    def cierra(self):
        """Resumen al final del test. Con modelo, también revisa la cobertura."""
        self.log.info("[banco] %d ticks revisados por el checker de una sola luz", self.ciclos)
        if not self.modelo:
            return
        self.log.info("[banco] cobertura:")
        faltan = []
        minimo = {"resets": 3}
        for k, n in self.cob.items():
            ok = n >= minimo.get(k, 1)
            self.log.info("    %-22s %4d  %s", k, n, "ok" if ok else "FALTA")
            if not ok:
                faltan.append(k)
        assert not faltan, ("cobertura incompleta: tu estímulo nunca probó "
                            + ", ".join(faltan) + " (resets: al menos 3)")
        self.log.info("[banco] cobertura: OK")

    # ---- Lo que corre en paralelo (cocotb.start_soon) -------------------
    async def _checker_una_luz(self):
        """La propiedad de seguridad: con rst_n = 1, exactamente una luz."""
        while True:
            await FallingEdge(self.dut.clk)
            if int(self.dut.rst_n.value) == 1:
                self.ciclos += 1
                luz = self.luz()
                assert luz in COLORES, (
                    f"checker: {luz} luces encendidas (r={self.dut.red.value} "
                    f"a={self.dut.yellow.value} v={self.dut.green.value})")

    async def _modelo(self):
        """Avanza el modelo en cada flanco de subida, con las mismas entradas."""
        while True:
            await RisingEdge(self.dut.clk)
            m = self.modelo
            if int(self.dut.rst_n.value) == 0:
                m.reinicia()
                m.en_reset = True
                continue
            m.en_reset = False
            ped = int(self.dut.ped_req.value)
            if ped:
                self.cob[f"boton en {m.color}"] += 1
            m.paso(ped)

    async def _comparador(self):
        """En cada flanco de bajada, la luz del diseño contra la del modelo."""
        while True:
            await FallingEdge(self.dut.clk)
            m = self.modelo
            if int(self.dut.rst_n.value) == 0 or getattr(m, "en_reset", True):
                continue
            luz = self.luz()
            assert luz == m.color, (
                f"comparador: el modelo esperaba {m.color} (cnt={m.cnt}) "
                f"y el diseño tiene {luz}")
