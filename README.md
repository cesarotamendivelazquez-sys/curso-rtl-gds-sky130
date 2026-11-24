# Curso: Diseño de un chip del RTL al GDSII (12 h)

Material del curso de **EELCCOM / CINVESTAV**: 6 sesiones de 2 h (1 h de teoría + 1 h de práctica)
en las que cada alumno lleva **el mismo diseño**, un semáforo Moore, del RTL al GDSII
con SKY130 y herramientas open source. Al final tiene DRC/LVS limpios y el timing firmado.

> **Idea rectora:** la salida de cada lab es la entrada del siguiente.
> RTL → verificación → netlist → layout → timing firmado.

## Arranque rápido

Todo corre dentro del contenedor [`hpretl/iic-osic-tools`](https://github.com/iic-jku/IIC-OSIC-TOOLS)
con Docker Desktop.

**Antes de la sesión 1:** cuenta de GitHub **y un token** (*Settings → Developer settings →
Personal access tokens → Tokens (classic)*, permiso `repo`). GitHub ya no acepta tu contraseña para `git push`.

1. Docker Desktop → *Images* → `hpretl/iic-osic-tools` → **Run** → *Optional settings*:
   nombre `TallerRTL2GDS` y host port `8080` para `:80/tcp`.
2. Abre `http://localhost:8080` (contraseña `abc123`) y una terminal en ese escritorio.
3. Haz fork de este repo en GitHub y clona **tu** fork:

   ```bash
   cd /foss/designs
   git clone https://github.com/<tu-usuario>/curso-rtl-gds-sky130.git
   cd curso-rtl-gds-sky130
   make humo                  # herramientas + PDK: debe decir LISTO
   ```

Las siguientes veces inicia el **mismo** contenedor desde *Containers* (▶). Nunca lo borres:
tu trabajo vive ahí, y tu respaldo es el `git push` de cada lab.

## Orden de los labs

| Sesión | Lab | Teoría | Práctica | Lo que te llevas |
| --- | --- | --- | --- | --- |
| 1 | [`labs/lab01-linux-pdk`](labs/lab01-linux-pdk) | PDKs y Linux para VLSI | Linux, rutas relativas, git, PDK con `ciel` | Rama propia + `notas_pdk.md` |
| 2 | [`labs/lab02-rtl`](labs/lab02-rtl) | RTL sintetizable y FSM | Lint y botón peatonal `ped_req` | Semáforo con lint limpio |
| 3 | [`labs/lab03-verif`](labs/lab03-verif) | Verificación funcional | TB autocomprobante + cocotb + 10 min de formal | PASS + onda + test aleatorio |
| 4 | [`labs/lab04-sintesis`](labs/lab04-sintesis) | Síntesis, `.lib` y SDC | Yosys + SKY130, área vs `CW`, GLS | `netlist.v` + GLS PASS |
| 5 | [`labs/lab05-pnr`](labs/lab05-pnr) | Place and Route | OpenROAD por etapas + LibreLane | GDS del semáforo |
| 6 | [`labs/lab06-sta`](labs/lab06-sta) | STA y signoff | OpenSTA con SPEF, fmax, corners, DRC/LVS | Checklist de signoff |

Cada lab se corre con `make` **desde su propia carpeta** (`make help` lista los objetivos).
El [proyecto final](proyecto-final) (opcional, evaluable) repite el flujo con un diseño propio.

## Estructura

```
common/rtl/semaphore/   Diseño guía: RTL + testbench del semáforo
common/sdc/             SDC único del curso (reloj de 20 ns = 50 MHz)
scripts/                env.sh (detecta el PDK) y prueba_humo.sh
labs/labNN-*/           README + Makefile + scripts de cada sesión
slides/                 Fuente de las diapositivas (.md + Mermaid) y su build a .pptx
proyecto-final/         Plantilla, menú de diseños y rúbrica
```

Las soluciones de los labs viven en la rama `soluciones`; `main` solo trae los esqueletos.

## Convenciones del curso

- **Reloj único:** 20 ns (50 MHz) en todos los SDC, testbenches y slides.
- **Rutas relativas siempre**: el repo funciona igual en cualquier máquina.
- **PDK:** SKY130 (`sky130A`), librería `sky130_fd_sc_hd`. Nunca se sube a git.
- **Nada bajo NDA** ni resultados pesados en git (ver `.gitignore`).

## Origen del material

Este repo es autocontenido, pero parte de
[`galletas-y-postres-chips`](https://github.com/Misterio12947/galletas-y-postres-chips)
(evento "Galletas y Postres: el camino de diseñar chips"). De ahí se copiaron:

- `common/rtl/semaphore/` (RTL y testbench del semáforo; el TB se ajustó al reloj de 20 ns).
- Los scripts de `flows/opensource/` en los que se basan los labs 3 a 6 (se citan en cada lab).
- La identidad visual y las metáforas de postres de las slides `ParteDigital`.

## Licencia

Código bajo [MIT](LICENSE). Slides y documentación: libres de reutilizar citando la fuente.
© 2026 Cesar Otamendi Velázquez / EELCCOM.
