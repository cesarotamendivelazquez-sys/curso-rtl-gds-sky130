# Lab 02 · RTL sintetizable y FSM

Al salir, escribes una **FSM sintetizable sin latches** y la pasas por **lint** en cero warnings.
El diseño es el semáforo del curso: le agregas un **botón peatonal** (`ped_req`).

> **POR VALIDAR** en `hpretl/iic-osic-tools:2026.09`. Se probó con Verilator 5.020, Yosys 0.33 e Icarus 12;
> la imagen trae versiones más nuevas y los mensajes pueden cambiar un poco.

| Parte | Tiempo | Qué haces | Cómo sabes que quedó |
| --- | --- | --- | --- |
| 1 · Leer | 10 min | Ubicar las 4 piezas en `semaphore.v` | `make preguntas` |
| 2 · Lint y esquemático | 10 min | Ver qué dice Verilator y qué "ve" Yosys | `make lint`, `make show` |
| 3 · Botón peatonal | 25 min | Agregar `ped_req`, conectar el TB y el SDC, commit | `make sim` |
| 4 · Un latch a propósito | 7 min | Quitar un `default` y ver quién se queja | `make lint`, `make latch` |
| 5 · Cerrar | 8 min | Lint en cero, commit y push | `make entrega` |

Las partes marcadas **[Juntos]** se hacen al mismo tiempo que el instructor en el proyector;
las marcadas **[Tú solo]** las resuelves por tu cuenta (el instructor pasa a ayudar).

**Entregable:** commit en tu rama `alumno/<tu-nombre>` con el semáforo con `ped_req`, lint limpio,
sin latches, los dos testbenches en PASS y `preguntas.txt` contestado.

**Los archivos que vas a editar** (todos los labs siguientes usan estos mismos):

| Archivo (desde esta carpeta) | Qué le haces |
| --- | --- |
| `../../common/rtl/semaphore/rtl/semaphore.v` | El RTL: botón y lint en cero |
| `../../common/rtl/semaphore/tb/tb_semaphore.v` | Conectar el nuevo puerto |
| `../../common/sdc/semaforo.sdc` | Descomentar la línea de `ped_req` |
| `preguntas.txt` | Contestar 5 preguntas |

`tb/tb_ped_req.v` **no se toca**: es el revisor del botón.

---

## Antes de empezar · [Juntos]

En Docker Desktop, *Containers* → ▶ en `TallerRTL2GDS` (**no** vuelvas a dar Run a la imagen) →
`http://localhost:8080`. En una terminal del escritorio, trae el lab nuevo **desde tu rama**:

```bash
cd /foss/designs/curso-rtl-gds-sky130
git switch alumno/<tu-nombre>
git fetch upstream
git pull upstream main          # si abre un editor con un mensaje de "Merge", guarda y cierra
cd labs/lab02-rtl
make check
make help
```

---

## Parte 1 · Leer: las 4 piezas (10 min) · [Juntos]

```bash
gedit ../../common/rtl/semaphore/rtl/semaphore.v &
```

Todo FSM sintetizable tiene las mismas 4 piezas. Encuéntralas en el archivo:

| Pieza | Qué es | Cómo la reconoces |
| --- | --- | --- |
| **A** · Codificación | Un número para cada estado | `localparam` |
| **B** · Siguiente estado | A qué estado se va desde cada estado | `always @(*)` con un `case` |
| **C** · Registro + contador | Lo que **recuerda**: el estado y cuántos ticks lleva | `always @(posedge clk or negedge rst_n)` |
| **D** · Salidas | Qué luz se prende en cada estado | `always @(*)` con un `case` |

Un **tick** es un ciclo de reloj: cada flanco de subida de `clk`. Con el reloj del curso (20 ns),
el verde dura `T_GREEN` = 5 ticks = 100 ns. En la tarjeta MinyPLD el reloj pasa antes por un
divisor y cada tick dura lo suficiente para verlo con los ojos.

Contesta `preguntas.txt` (`gedit preguntas.txt &`) y revisa:

```bash
make preguntas
```

---

## Parte 2 · Lint y esquemático (10 min) · [Juntos]

**Lint** es revisar el código sin simularlo, buscando lo que compila pero huele mal:

```bash
make lint
```

Por dentro corre `verilator --lint-only -Wall ../../common/rtl/semaphore/rtl/semaphore.v`.
Cada aviso tiene la forma `%Warning-CÓDIGO: archivo:línea:columna: mensaje`. Te van a salir
dos códigos:

- **DECLFILENAME**: el archivo se llama `semaphore.v` pero el módulo se llama `semaforo`.
- **WIDTHTRUNC**: a una señal de 8 bits le asignas algo de 32 bits; los bits de arriba se tiran.

**Todavía no los arregles**: lo haces en la parte 5. Ahora mira qué entiende Yosys de tu RTL:

```bash
make show
```

Corre `yosys -p "read_verilog ...; proc; opt; show ..."` y abre `build/semaforo_rtl.svg`.
Busca en el dibujo:

- Las cajas **`$adff`** y **`$adffe`**: flip-flops con reset asíncrono. Los números `<2>` y `<8>`
  de sus cables son su ancho en bits.
- Las cajas **`$mux`**, **`$pmux`** y **`$eq`**: la lógica combinacional de tus `case` y comparaciones.
- Que **no hay ninguna celda del PDK** todavía: es la estructura que *describiste*. Las celdas
  `sky130_fd_sc_hd__...` llegan en la síntesis (lab04).

> **Para discutir:** ¿`limit` y `next_state` aparecen como flip-flops? ¿Por qué no, si están declarados `reg`?

---

## Parte 3 · El botón peatonal (25 min) · [Tú solo]

**Especificación:**

| Si el semáforo está en… | y en un flanco de reloj `ped_req = 1`… |
| --- | --- |
| Verde | en **ese mismo flanco** pasa a amarillo (lo ves en el siguiente tick) y el contador vuelve a 0 |
| Amarillo | no pasa nada: sigue su tiempo normal |
| Rojo | no pasa nada: sigue su tiempo normal |

Sin botón (`ped_req = 0`) todo se comporta exactamente como antes.

1. **El puerto.** Agrega a la lista de puertos de `semaforo` una entrada de 1 bit llamada `ped_req`,
   con un comentario que diga qué es.

2. **La condición.** Hoy el estado avanza por **una** razón: se acabó el tiempo
   (`cnt == limit - 1'b1`). Agrega la **segunda** razón. Pregúntate en qué pieza (A, B, C o D)
   va y por qué no hace falta tocar el `case` de la pieza B.

3. **Simula:**

   ```bash
   make sim
   ```

   Corre dos testbenches: el TB base de siempre y `tb/tb_ped_req.v`, que compara tu diseño ciclo a
   ciclo contra un modelo de referencia en 8 casos (sin botón, botón al inicio y al final del verde,
   en amarillo, en rojo, sostenido, con reset y al azar). Si un caso sale `[MAL ]`, te dice cuándo,
   qué luz esperaba y cuál salió.

4. **Conecta el TB base.** `make sim` te avisa que el TB base deja `ped_req` **sin conectar**
   (Icarus: `dangling input port`). Una entrada flotante en simulación vale `z` y el TB puede
   pasar *de suerte*. En `../../common/rtl/semaphore/tb/tb_semaphore.v`, en la instancia `dut`,
   agrega la conexión `.ped_req(1'b0)` (en este TB nadie aprieta el botón). Repite `make sim`:
   los dos en PASS y sin el aviso.

   > Cambiar los puertos de un módulo afecta a **todos** los que lo instancian: por eso Icarus y
   > Verilator (`PINMISSING`) te avisan.

5. **El SDC.** Toda entrada del chip necesita decirle a STA cuándo llega. En
   `../../common/sdc/semaforo.sdc` descomenta la línea de `set_input_delay` de `ped_req`
   (borra el `#` del inicio). La usan los labs 4, 5 y 6.

6. **Commit** (el botón ya funciona; guárdalo antes de romper algo a propósito en la parte 4):

   ```bash
   git status
   git add ../../common/rtl/semaphore/rtl/semaphore.v ../../common/rtl/semaphore/tb/tb_semaphore.v \
           ../../common/sdc/semaforo.sdc preguntas.txt
   git commit -m "lab02: boton peatonal ped_req"
   ```

> **Para discutir:** un botón real no está sincronizado con `clk`. Si cambia justo en el flanco, el
> flip-flop puede quedar **metaestable**. En un chip real la entrada pasa antes por un
> **sincronizador** de 2 flip-flops, y el botón se atiende 2 ticks después. Aquí no lo ponemos para
> que la especificación sea "en el siguiente tick".

---

## Parte 4 · Un latch a propósito (7 min) · [Juntos]

Un **latch** aparece cuando una señal de un `always @(*)` no recibe valor en **todos** los caminos:
el hardware tiene que "recordar" el valor anterior. En un ASIC eso complica el timing y casi siempre
es un error.

1. En `semaphore.v`, **borra el renglón `default:` del `case` que calcula `limit`** y guarda.
   `state` tiene 2 bits (4 valores) y el `case` solo cubre 3.

   ```bash
   make lint       # ¿cuál warning es nuevo?
   make latch      # ¿qué señal se volvió latch?
   make show       # opcional: busca la caja $dlatch
   ```

2. **Regresa ese `default`** (`git restore ../../common/rtl/semaphore/rtl/semaphore.v`) y ahora
   **borra el `default:` del `case` de las salidas** (pieza D). Repite `make lint` y `make latch`.
   Verilator se sigue quejando… ¿y Yosys? ¿Por qué esta vez no hay latch?
   (Pista: mira la primera línea dentro de ese `always`.)

3. Regresa todo a tu commit y confirma:

   ```bash
   git restore ../../common/rtl/semaphore/rtl/semaphore.v
   git status          # semaphore.v ya no aparece como modificado
   make latch          # SIN LATCHES
   ```

> **La lección:** Verilator te avisa del **riesgo** (un `case` incompleto). Yosys te dice lo que
> **construyó** (un latch o no). Por eso se revisan las dos cosas.

---

## Parte 5 · Cerrar: lint en cero (8 min)

### 5.1 DECLFILENAME · [Juntos]

El archivo se queda como `semaphore.v` (así se llama en el repo del evento y en los 6 labs), así que
este aviso no se "arregla": se documenta una **excepción**. Pega esto en la línea 2 de `semaphore.v`,
justo debajo de `` `timescale ``:

```verilog
// El archivo se llama semaphore.v por compatibilidad con el repo del evento;
// el módulo se llama semaforo. Excepción de lint revisada y aceptada:
/* verilator lint_off DECLFILENAME */
```

Las reglas de una excepción: se escribe en el código, dice **por qué** y apaga **solo ese** código
de aviso. `make entrega` rechaza cualquier otro `lint_off`.

### 5.2 WIDTHTRUNC · [Tú solo]

Este sí se arregla en el código. Verilator dice que `T_GREEN` mide 32 bits (es `parameter integer`)
y `limit` mide `CW` bits. Dile explícitamente **qué bits quieres**: los `CW` de abajo. Un parámetro
también se puede rebanar con `[ : ]`, igual que una señal. Arregla los 4 renglones y:

```bash
make lint           # == LINT LIMPIO: 0 warnings ==
make latch          # SIN LATCHES
make sim            # los dos en PASS
```

### 5.3 Entrega · [Tú solo]

```bash
git add ../../common/rtl/semaphore/rtl/semaphore.v
git commit -m "lab02: lint en cero warnings"
git push
make entrega        # debe decir "LISTO para entregar"
```

`make entrega` revisa todo junto: preguntas, puerto, lint, excepciones, latches, los dos testbenches,
que no hayas tocado `tb/tb_ped_req.v`, el SDC, tu rama, los commits y el push.

## ¿Te atoraste?

Las soluciones están en la rama `soluciones` del repo del curso. Úsalas para **comparar**, no para copiar:

```bash
git fetch upstream
git diff HEAD upstream/soluciones -- ../../common/rtl/semaphore/rtl/semaphore.v
```

| Síntoma | Qué pasa |
| --- | --- |
| `port ``ped_req'' is not a port of dut` | Tu `semaforo` aún no tiene la entrada `ped_req` |
| `dangling input port ... (ped_req) floating` | Falta `.ped_req(1'b0)` en el TB base |
| `[MAL ] boton en amarillo (ignorar)` | El botón también actúa fuera del verde |
| `[MAL ] boton al inicio del verde`, sale verde | El botón no adelanta el cambio, o lo hace un tick tarde |
| `make latch` dice LATCH después de la parte 4 | Te faltó el `git restore` |

## Origen

Basado en `galletas-y-postres-chips`: `common/rtl/semaphore` (el RTL y el TB base) y
`flows/opensource/02-rtl` (el esquemático con Yosys `show`).
