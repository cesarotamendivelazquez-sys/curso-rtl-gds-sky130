# Lab 03 · Verificación funcional

Al salir, tienes un **testbench que dice PASS/FAIL solo** y un **test aleatorio en cocotb** que
atrapa bugs que tú no metiste. El diseño es tu semáforo del lab02, con `ped_req`.

| Parte | Tiempo | Qué haces | Cómo sabes que quedó |
| --- | --- | --- | --- |
| 1 · El TB base y la onda | 10 min | Correr el TB base y ver `state`, `cnt` y las luces en GTKWave | `make sim` → PASS |
| 2 · Un bug a propósito | 10 min | Prender dos luces en amarillo, encontrar el ciclo en la onda, capturarla | `make respuestas` → 3/3 |
| 3 · cocotb | 30 min | Escribir un test dirigido y uno aleatorio en Python | `make cocotb`, `make mutantes` |
| 4 · Formal (opcional) | 10 min | Demostrar "nunca dos luces" con SymbiYosys y ver un contraejemplo | `make formal` |
| Cerrar | en casa | Commit, push y revisión | `make entrega` |

Las partes marcadas **[Juntos]** se hacen al mismo tiempo que el instructor en el proyector;
las marcadas **[Tú solo]** las resuelves por tu cuenta (el instructor pasa a ayudar).

**Entregable:** en tu rama `alumno/<tu-nombre>`, el test dirigido y el aleatorio en PASS (y atrapando
los mutantes), `respuestas.txt` contestado y la captura de la onda del bug en `entrega/`.

**Los archivos que vas a editar** (todos son nuevos de este lab):

| Archivo (desde esta carpeta) | Qué le haces |
| --- | --- |
| `cocotb/test_semaforo.py` | Escribir tus dos tests (TODO 1 y TODO 2) |
| `respuestas.txt` | Contestar 3 preguntas sobre el bug |
| `entrega/onda_bug.gtkw` y `entrega/onda_bug.png` | Los creas en la parte 2 |
| `../../common/rtl/semaphore/rtl/semaphore.v` | **Solo en la parte 2**: le metes un bug y lo regresas con `git restore` |

**No se tocan** (`make entrega` revisa que estén igual que en el curso): `cocotb/semaforo_tb.py`,
`cocotb/run.py`, `scripts/mutantes/` y `formal/`.

---

## Antes de empezar · [Juntos]

En Docker Desktop, *Containers* → ▶ en `TallerRTL2GDS` (**no** vuelvas a dar Run a la imagen) →
`http://localhost:8080`. En una terminal del escritorio, trae el lab nuevo **desde tu rama**:

```bash
cd /foss/designs/curso-rtl-gds-sky130
git switch alumno/<tu-nombre>
git fetch upstream
git pull upstream main          # si abre un editor con un mensaje de "Merge", guarda y cierra
cd labs/lab03-verif
make check
make help
```

`make check` debe mostrar Icarus, GTKWave, Yosys, sby y **cocotb 2.x**, y tu rama `alumno/...`.

---

## Parte 1 · El TB base y la onda (10 min) · [Juntos]

```bash
make sim
```

Corre `iverilog` con **tu** `semaphore.v` y el TB base `tb_semaphore.v`, y luego `vvp`. Debe decir
`TB base: PASS`. Ese TB tiene las tres piezas de todo testbench:

| Pieza | En `tb_semaphore.v` |
| --- | --- |
| **Estímulo** | El reloj (`always #10`) y el reset que se suelta a los 25 ns |
| **Checker** | El `always @(posedge clk)` que revisa que haya **exactamente una** luz |
| **Cobertura** | No tiene: solo deja correr 1000 ns y "espera" haber pasado por todo |

El TB también guarda la onda en `build/dump.vcd`. Ábrela:

```bash
make wave
```

En GTKWave:

1. En el panel de la izquierda (**SST**) da clic en `tb_semaphore` y luego en `dut`.
2. Abajo aparecen las señales del semáforo: selecciona `state` y `cnt` y da clic en **Append**.
3. Regresa a `tb_semaphore` y agrega `red`, `yellow` y `green`.
4. Menú **Time → Zoom → Zoom Best Fit** para ver toda la simulación.

Mira cómo `cnt` cuenta 0, 1, 2 en verde y cómo cambia `state` cuando el contador llega al final.
**No cierres GTKWave**: lo vuelves a usar en la parte 2.

> **Para discutir:** el checker dice PASS, pero ¿qué casos *no* probó este TB? ¿Alguien apretó el botón?

---

## Parte 2 · Un bug a propósito (10 min)

### 2.0 Paso 0: confirma que todo está guardado · [Juntos]

Vas a romper tu `semaphore.v` y a regresarlo con `git restore`, que regresa **al último commit**. Si
algo de tu lab02 no está en un commit, `git restore` lo borra. Antes de tocar nada:

```bash
make guardado
```

Debe decir **`GUARDADO`** y mostrarte el commit donde está tu RTL. Si dice **`NO SIGAS`**, haz lo que
te indica (normalmente un `git add` y un `git commit`) y repite `make guardado`.

### 2.1 Mete el bug (edición a mano) · [Juntos]

Abre tu RTL con `gedit ../../common/rtl/semaphore/rtl/semaphore.v &`. En el `case` de las
**salidas** (pieza D), cambia el renglón del amarillo:

```verilog
            S_YELLOW: yellow = 1'b1;
```

por este (en amarillo **también** se prende el verde):

```verilog
            S_YELLOW: begin yellow = 1'b1; green = 1'b1; end   // BUG a propósito
```

Guarda el archivo (`Ctrl+S`).

### 2.2 El checker lo atrapa · [Juntos]

```bash
make sim
```

Ahora dice `TB base: FAIL` y cada violación sale como `[tiempo] FAIL: luces invalidas r=0 y=1 g=1`.
El tiempo sale en **ps**: el TB lo imprime con `%t`, que usa la precisión del `timescale` (1 ps).

### 2.3 Encuentra el ciclo en la onda · [Tú solo]

En GTKWave (el que dejaste abierto):

1. **File → Reload Waveform**: carga la onda nueva y conserva tus señales.
2. Busca la **primera** vez que `yellow` y `green` están en 1 al mismo tiempo.
3. Da **clic** en la onda justo ahí: aparece el marcador (una línea vertical) y arriba su tiempo.
4. Lee cuánto vale `state` en ese punto.
5. **File → Write Save File As**, entra a `labs/lab03-verif/entrega/` y guárdalo como `onda_bug.gtkw`.

### 2.4 Captura la onda · [Tú solo]

Maximiza GTKWave, con el marcador y las 5 señales a la vista, y en la terminal:

```bash
make captura
```

Tienes 5 segundos para poner GTKWave al frente; la foto queda en `entrega/onda_bug.png`.
Si `make captura` falla, en GTKWave usa **File → Grab To File** y guárdala con ese mismo nombre.

### 2.5 Contesta · [Tú solo]

Abre `respuestas.txt` (`gedit respuestas.txt &`), contesta R1, R2 y R3 y guarda. Luego:

```bash
make respuestas
```

### 2.6 Regresa tu RTL · [Juntos]

Si `gedit` tiene abierto `semaphore.v`, ciérralo primero (sin guardar). Luego:

```bash
git restore ../../common/rtl/semaphore/rtl/semaphore.v
git status --short ../../common     # no debe salir NADA
make sim                            # otra vez TB base: PASS
```

### 2.7 Commit de la parte 2 · [Tú solo]

```bash
git add respuestas.txt entrega/onda_bug.gtkw entrega/onda_bug.png
git commit -m "lab03: bug en la onda"
```

> **La lección:** el TB no "se ve": **se lee solo**. El checker dijo FAIL y el tiempo exacto; la onda
> sirvió para entender *por qué*, no para descubrir *que* falló.

---

## Parte 3 · cocotb (30 min)

cocotb escribe el testbench en **Python** mientras Icarus simula tu Verilog. Tu archivo es
`cocotb/test_semaforo.py`; todo lo demás (reloj, reset, checker, modelo y cobertura) ya está en
`cocotb/semaforo_tb.py`.

### 3.1 El banco de pruebas · [Juntos]

Abre los dos archivos (`gedit cocotb/semaforo_tb.py cocotb/test_semaforo.py &`). Esto es lo que
te da el banco:

| Lo que escribes | Qué hace |
| --- | --- |
| `tb = Banco(dut)` | Prepara el banco para tu semáforo (`dut`) |
| `await tb.arranca()` | Reloj de 20 ns, checker de **una sola luz** siempre activo y un reset |
| `await tb.arranca(modelo=True)` | Lo mismo + un **modelo de referencia** que compara cada tick, y la **cobertura** |
| `tb.luz()` | `"verde"`, `"amarillo"`, `"rojo"`, `"ninguna"` o `"varias"` |
| `tb.T["verde"]` | Cuántos ticks dura el verde (también `"amarillo"` y `"rojo"`) |
| `await tb.ticks(n)` | Espera `n` ticks |
| `await tb.pulso(n)` | Aprieta `ped_req` durante `n` ticks |
| `await tb.reset(n)` | `rst_n = 0` durante `n` ticks |
| `tb.cierra()` | Resumen; con modelo, revisa que la cobertura esté completa |

Dos reglas: todo lo que espera lleva **`await`**, y todo se mueve en el **flanco de bajada** de `clk`
(el diseño cambia en el de subida; a media vuelta ya está estable). Corre el esqueleto:

```bash
make cocotb
```

Los dos tests salen **FAIL** con `NotImplementedError: TODO`: todavía no los escribes. Fíjate en el
renglón `tiempos: verde 4, amarillo 3, rojo 5 ticks`: cocotb usa tiempos distintos a los del TB base.

### 3.2 TODO 1 · El test dirigido · [Tú solo]

**Especificación:** justo después de `arranca()`, durante **2 vueltas completas**, los colores salen
en el orden verde → amarillo → rojo y **cada color dura exactamente** `tb.T[color]` ticks.

En `test_dirigido`, borra el renglón `raise NotImplementedError(...)` y escribe la revisión en su lugar.
Pistas:

- Justo después de `arranca()` el semáforo ya está en verde: **ese tick cuenta como el primero**.
- Para cada vuelta y cada color: revisa con `assert` que `tb.luz()` sea ese color, cuenta cuántos
  ticks se queda con `await tb.ticks(1)` y compara la cuenta con `tb.T[color]`.
- El mensaje del `assert` es lo que vas a leer cuando falle: que diga vuelta, color, cuánto duró y cuánto debía.
- Aquí **no** uses `modelo=True`: en el dirigido el que revisa eres tú.

```bash
make cocotb TEST=test_dirigido
```

### 3.3 TODO 2 · El test aleatorio · [Tú solo]

**Especificación:** unos cientos de pasos donde, en cada uno, se elige **al azar** entre apretar el
botón (`tb.pulso`) unos ticks, dar un reset (`tb.reset`) de vez en cuando, o solo esperar
(`tb.ticks`) unos ticks. El checker de una sola luz y el modelo revisan **cada tick** por su cuenta.

En `test_aleatorio`, borra el `raise NotImplementedError(...)` y escribe el estímulo. Usa
`random.random()` y `random.randint(a, b)`. Al final, `tb.cierra()` imprime la **cobertura** y falla
si tu estímulo nunca apretó el botón en algún color o dio menos de 3 resets.

```bash
make cocotb TEST=test_aleatorio
make cocotb TEST=test_aleatorio SEED=7      # otra semilla: otros casos al azar
```

La semilla sale en el log (`Seeding Python random module with ...`): con `SEED=` repites exactamente
una corrida que falló.

### 3.4 ¿Tus tests sirven? Los mutantes · [Tú solo]

Un test que siempre dice PASS no sirve. `scripts/mutantes/` tiene 6 copias del semáforo, cada una con
**un** bug distinto. Tus tests deben atraparlos (decir FAIL):

```bash
make mutantes
```

El dirigido debe atrapar m1, m2 y m6; el aleatorio, los 6. Si alguno sale **SE ESCAPA**, mejora el
test correspondiente y repite. Luego, el commit:

```bash
git add cocotb/test_semaforo.py
git commit -m "lab03: tests dirigido y aleatorio en cocotb"
```

Si quieres ver la onda de cocotb: `make wave-cocotb` (las señales están en `semaforo`).

> **Para discutir:** ¿por qué el dirigido no atrapa m3 ni m5, si están igual de mal? ¿Quién decide
> cuándo ya probaste suficiente? (Pista: la tabla de cobertura.)

---

## Parte 4 · Formal en 10 min (opcional) · [Juntos]

La simulación prueba **los casos que se te ocurren**. La verificación formal **demuestra** una propiedad
para **todos** los casos, o te da un contraejemplo. No hay testbench: solo
`formal/formal_top.v`, que instancia tu semáforo, deja `ped_req` **libre** y escribe la propiedad como
`assert (red + yellow + green == 1)`.

```bash
make formal          # sby -f prueba.sby sobre TU semaphore.v -> PASS
make formal-bug      # sby -f bug.sby sobre formal/semaforo_bug.v -> FAIL + contraejemplo
make formal-wave     # abre el contraejemplo en GTKWave
```

En el contraejemplo agrega `ped_req`, `state` y las luces.

> **Para discutir:** ¿en cuántos ciclos llegó el solver al fallo? ¿Qué hizo con `ped_req` para llegar
> más rápido que el TB base?

---

## Cerrar · [Tú solo]

```bash
git status                  # ¿algo sin commit?
git push
make entrega                # debe decir "LISTO para entregar"
```

`make entrega` revisa todo junto: respuestas, el TB base en PASS con tu RTL (sin el bug), los
archivos que no se tocan, tus dos tests con tu RTL (el aleatorio con dos semillas), la cobertura,
los mutantes, la onda (`.gtkw` con las 5 señales y el marcador en el primer ciclo con dos luces, y el
`.png`), tu rama, los commits y el push. Tarda menos de un minuto.

## ¿Te atoraste?

Las soluciones están en la rama `soluciones` del repo del curso. Úsalas para **comparar**, no para copiar:

```bash
git fetch upstream
git diff HEAD upstream/soluciones -- cocotb/test_semaforo.py
```

| Síntoma | Qué pasa |
| --- | --- |
| `make guardado` dice `NO SIGAS` | Tienes cambios sin commit en `../../common`: haz el commit que te indica |
| `make guardado`: tu semaforo no tiene `ped_req` | No trajiste tu lab02: `git switch alumno/<tu-nombre>` y `git pull upstream main` |
| Después del `git restore`, `make sim` no compila o falta `ped_req` | Te saltaste el paso 0. Si `gedit` sigue abierto, `Ctrl+Z`; si no, recupéralo de GitHub: `git restore --source=origin/alumno/<tu-nombre> ../../common` |
| `make sim` sigue en FAIL al final | Quedó el bug: `git restore ../../common/rtl/semaphore/rtl/semaphore.v` |
| En GTKWave no cambia nada tras `make sim` | Falta **File → Reload Waveform** |
| `make respuestas`: R1 en MAL con un número muy grande | Ese número está en ps: pásalo a ns |
| `make captura`: `No hay pantalla` | La corriste fuera del escritorio: usa una terminal de noVNC |
| `make cocotb`: `NotImplementedError: TODO` | Te falta borrar el `raise NotImplementedError(...)` de ese test |
| `make cocotb`: `SyntaxError` o `IndentationError` | Python usa la sangría: los renglones dentro del test van con 4 espacios |
| `RuntimeWarning: coroutine ... was never awaited` | Te faltó `await` antes de `tb.ticks`, `tb.pulso` o `tb.reset` |
| El dirigido dice que el verde duró un tick de menos | El tick justo después de `arranca()` también cuenta |
| `cobertura incompleta` | Tu estímulo casi no aprieta el botón o casi no da resets: sube la probabilidad o los pasos |
| `comparador: el modelo esperaba ...` en el aleatorio | Tu RTL no cumple la especificación del botón en algún caso. Revísalo con `make cocotb TEST=test_aleatorio SEED=<la del log>` y `make wave-cocotb` |
| `make mutantes`: m1 o m2 `SE ESCAPA` del dirigido | Tu dirigido no revisa la duración o el orden de los colores |
| `make entrega`: `test_dirigido revisa sin el modelo` en MAL | Usaste `modelo=True` en el dirigido |

## Origen

Basado en `galletas-y-postres-chips`: `common/rtl/semaphore/tb` (el TB base),
`flows/opensource/03-verif-funcional` (Icarus y GTKWave) y `flows/opensource/04-verif-formal`
(el envoltorio formal, ahora con `ped_req`, y el bug de las dos luces).
