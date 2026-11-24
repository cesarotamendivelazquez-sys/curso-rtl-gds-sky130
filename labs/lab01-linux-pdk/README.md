# Lab 01 · PDKs y Linux para VLSI

Al salir, sabes **dónde vive cada vista del PDK** y te mueves en Linux y git **sin rutas absolutas**.
Todo se hace dentro del contenedor `iic-osic-tools`. Cada parte se autocomprueba con `make`.

| Parte | Tiempo | Qué haces | Cómo sabes que quedó |
| --- | --- | --- | --- |
| 1 · Arranque | 10 min | Contenedor, escritorio, tu copia del repo | `make check` |
| 2 · Linux y rutas | 15 min | 8 retos en `respuestas_rutas.txt` | `make rutas` |
| 3 · Git | 15 min | Tu rama, tu primer commit, push a tu fork | `make git-check` |
| 4 · PDK | 20 min | Ver qué PDK tienes, explorarlo, completar `pdk_info.sh`, ver una celda | `make celda`, `make entrega` |

**Entregable:** commit en tu rama `alumno/<tu-nombre>` con `notas_pdk.md` lleno
(área y tamaño de 3 celdas, corners disponibles), `pdk_info.sh` completo y `respuestas_rutas.txt`.

---

## Parte 1 · Arranque (10 min)

1. **Levanta el contenedor en Docker Desktop.** La primera vez: *Images* → `hpretl/iic-osic-tools` → **Run** →
   despliega *Optional settings* y llena:

   | Campo | Valor |
   | --- | --- |
   | Container name | `TallerRTL2GDS` |
   | Host port para `:80/tcp` | `8080` |

   Lo demás se queda vacío. Da **Run**.

2. **Abre el escritorio** en tu navegador: `http://localhost:8080` → *Connect* → contraseña `abc123`.
   Abre una terminal en ese escritorio: todo el curso se trabaja ahí.

3. **Tu trabajo vive dentro del contenedor.** Las siguientes veces **no vuelvas a dar Run** a la imagen
   (eso crea otro contenedor, vacío): ve a *Containers* y usa ▶ y ■ en `TallerRTL2GDS`.

   > **Nunca borres el contenedor** (🗑). Detenerlo e iniciarlo no pierde nada; borrarlo, sí.
   > Tu respaldo de verdad es GitHub: al final de cada lab haces `git push` (parte 3).

4. Haz **fork** del repo del curso en GitHub (botón *Fork* en
   `github.com/Misterio12947/curso-rtl-gds-sky130`) y, en la terminal del escritorio, clona **tu** fork:

   ```bash
   cd /foss/designs
   git clone https://github.com/<tu-usuario>/curso-rtl-gds-sky130.git
   cd curso-rtl-gds-sky130/labs/lab01-linux-pdk
   git remote -v               # debe decir TU usuario, no Misterio12947
   make check
   ```

   En la parte 3 vemos qué acabas de hacer. Por ahora basta con que `make check` diga `LISTO`.

---

## Parte 2 · Linux y rutas relativas (15 min)

Los comandos que vas a usar:

| Comando | Para qué | Ejemplo |
| --- | --- | --- |
| `pwd` | ¿dónde estoy? | `pwd` |
| `ls -la` | ¿qué hay aquí? (con ocultos) | `ls -la ../..` |
| `cd` | moverse | `cd ../../common` · `cd -` regresa |
| `mkdir -p` | crear carpetas (y sus padres) | `mkdir -p prueba/a/b` |
| `cp` / `mv` / `rm` | copiar / mover / borrar | `cp a.txt b.txt` |
| `less` | leer un archivo largo (`q` para salir) | `less ../../README.md` |
| `find` | buscar archivos por nombre | `find ../.. -name "*.v"` |
| `grep` | buscar texto dentro de archivos | `grep -n module ../../common -r` |
| `wc -l` | contar líneas | `wc -l archivo` |
| `which` | ¿dónde está un programa? | `which klayout` |
| `echo $VAR` / `export` | ver / fijar variables | `echo $PDK_ROOT` |

`.` es "aquí", `..` es "un nivel arriba" y `~` es tu home. Una ruta **absoluta** empieza en `/`
(`/foss/designs/...`); una **relativa** empieza desde donde estás (`../../common/...`).

**Retos:** abre `respuestas_rutas.txt`, responde los 8 retos (cada respuesta en una sola línea) y revisa:

```bash
make rutas
```

> **Para discutir:** todos los Makefiles del curso usan `../../common/...` y nunca `/foss/designs/...`.
> ¿Qué pasaría si tu compañero clonó el repo en otra carpeta?

---

## Parte 3 · Git, la bitácora del chip (15 min)

En la parte 1 hiciste dos cosas: un **fork** (tu copia del repo en GitHub, donde sí puedes escribir)
y un **clone** (la copia de tu fork en el contenedor). Ahora:

```bash
# 1) Quién eres (una sola vez por contenedor)
git config --global user.name  "Tu Nombre"
git config --global user.email "tu@correo.com"

# 2) De dónde viene el material del curso (para traer los labs nuevos)
git remote add upstream https://github.com/Misterio12947/curso-rtl-gds-sky130.git

# 3) Tu rama de trabajo: aquí van todos tus labs
git switch -c alumno/<tu-nombre>

```

4) Abre `notas_pdk.md`, escribe tu nombre después de `**Nombre:**`, guarda y cierra:

```bash
gedit notas_pdk.md &        # el aviso "Gtk-WARNING ... Inhibit" se puede ignorar
```

5) Guarda el cambio en git y súbelo a **tu** fork:

```bash
git status                  # ¿qué cambió?
git diff                    # ¿qué cambió exactamente? (si no sale nada, no guardaste el archivo)
git add notas_pdk.md
git commit -m "lab01: empiezo mis notas del PDK"
git log --oneline -5
git push -u origin alumno/<tu-nombre>
```

Para el `push`, GitHub pide tu usuario y, **como contraseña, tu token** (lo creaste en la preparación
previa). Tu contraseña normal **no funciona**: GitHub responde `Password authentication is not supported`.
Para no teclearlo en cada push durante la sesión (córrelo **antes** del primer push):

```bash
git config --global credential.helper "cache --timeout=7200"   # lo recuerda 2 horas
```

¿No tienes token? En GitHub: tu foto → *Settings* → *Developer settings* → *Personal access tokens* →
*Tokens (classic)* → *Generate new token (classic)*. Marca el permiso **repo**, ponle 90 días de vigencia
y copia el token en ese momento (GitHub no lo vuelve a mostrar).

```bash
make git-check
```

**Qué NO se sube nunca:** el PDK, nada bajo NDA, ni resultados que se regeneran (`.gds`, `.vcd`, `runs/`...).
Revisa el `.gitignore` de la raíz: ya los excluye.

---

## Parte 4 · El PDK por dentro (20 min)

### 4.1 ¿Qué PDK tengo?

El contenedor ya trae SKY130 instalado con `ciel`, el gestor de versiones de PDKs. Pregúntale cuál:

```bash
ciel ls --pdk-family sky130 --pdk-root /foss/pdks
# └── 1689ac3f2dc763876eaf967227c7dfe831b031ae (2026.08.27) (enabled)
```

Ese hash identifica **exactamente** qué versión del PDK usas: es lo que anotas en tus notas y lo que
pondrías en el README de un proyecto para que otro reproduzca tus resultados.

Ahora fija las variables del curso:

```bash
source ../../scripts/env.sh          # dice qué PDK encontró
echo $PDK_ROOT $PDK
ENV_VERBOSE=1 source ../../scripts/env.sh   # y todas las rutas que fijó
```

> **Cómo se baja un PDK (lo ve el instructor en el proyector; tú, opcional en casa).**
> `ciel` consulta la API de GitHub, que sin cuenta permite 60 consultas por hora por red:
> si todo el salón lo corre a la vez, nadie termina. Fuera de clase:
>
> ```bash
> ciel ls-remote --pdk-family sky130 | head          # versiones publicadas
> ciel enable --pdk-family sky130 --pdk-root /foss/designs/pdks \
>     1689ac3f2dc763876eaf967227c7dfe831b031ae       # la misma versión del curso
> ```
>
> Ocupa varios GB. Si existe `/foss/designs/pdks`, `env.sh` lo prefiere sobre el del contenedor.

### 4.2 Explorar

Responde con `ls`, `find`, `grep` y `less` (las respuestas van a `notas_pdk.md`):

```bash
ls $PDK_ROOT/$PDK                        # libs.ref  vs  libs.tech
ls $SCL_DIR                              # las vistas de la librería de celdas
ls $SCL_DIR/lib                          # un .lib por corner (los .lib.gz son copias comprimidas)
grep -c 'cell ("sky130' $LIB_TT          # ¿cuántas celdas hay?
grep -A3 'cell ("sky130_fd_sc_hd__nand2_1")' $LIB_TT | less
grep -A8 "MACRO sky130_fd_sc_hd__nand2_1" $CELLLEF
```

- ¿Qué diferencia hay entre `libs.ref/` y `libs.tech/`?
- ¿Qué vista usa síntesis? ¿Cuál usa PnR? ¿Cuál termina en el GDS final?

Compara con la radiografía: `make pdk`.

### 4.3 Tu script: `pdk_info.sh`

`pdk_info.sh` imprime la ficha de una celda: **área** (del `.lib`), **tamaño** y **pines** (del `.lef`).
El reporte ya está hecho. Tú llenas 3 líneas, `AREA=$( )`, `TAMANO=$( )` y `PINES=$( )`, con un comando
que **armas en la terminal pieza por pieza**: agregas un `|` y un comando, miras la salida, y repites
hasta que sale justo el dato.

Las piezas que vas a usar:

| Pieza | Qué hace |
| --- | --- |
| `grep -A500 "texto" archivo` | la línea con ese texto **y las 500 siguientes** |
| `grep "texto"` | deja pasar solo las líneas que tienen ese texto |
| `head -1` | deja pasar solo la primera línea |
| `awk '{print $3}'` | imprime la 3a palabra de cada línea (`$2, $4` = la 2a y la 4a) |
| `tr -d ';'` | borra los `;` |

#### TODO 1 · Área

```bash
grep -A500 'cell ("sky130_fd_sc_hd__nand2_1")' $LIB_TT | less        # tu celda y lo que sigue (q = salir)
grep -A500 'cell ("sky130_fd_sc_hd__nand2_1")' $LIB_TT | grep "area :"
#        area : 3.7536000000;          <- la de tu celda
#        area : ...                    <- y las de las celdas que siguen
grep -A500 'cell ("sky130_fd_sc_hd__nand2_1")' $LIB_TT | grep "area :" | head -1
grep -A500 'cell ("sky130_fd_sc_hd__nand2_1")' $LIB_TT | grep "area :" | head -1 | awk '{print $3}'
#  3.7536000000;
grep -A500 'cell ("sky130_fd_sc_hd__nand2_1")' $LIB_TT | grep "area :" | head -1 | awk '{print $3}' | tr -d ';'
#  3.7536000000                        <- ¡listo!
```

#### TODO 2 · Tamaño

```bash
grep -A8 "MACRO sky130_fd_sc_hd__nand2_1" $CELLLEF
grep -A8 "MACRO sky130_fd_sc_hd__nand2_1" $CELLLEF | grep SIZE
#   SIZE 1.380 BY 2.720 ;
```

Termina tú: quédate con la primera línea y luego con la 2a y la 4a palabra. Debe salir `1.380 2.720`.

#### TODO 3 · Pines

Este comando ya recorta del `.lef` **solo el bloque de tu celda**:

```bash
sed -n '/^MACRO sky130_fd_sc_hd__nand2_1$/,/^END sky130_fd_sc_hd__nand2_1$/p' $CELLLEF
```

Termina tú: deja solo las líneas que dicen `PIN` y luego imprime solo el nombre del pin (la 2a palabra).
Deben salir `A`, `B`, `Y`, `VGND`, `VNB`, `VPB` y `VPWR`, uno por línea.

#### Pasa tus comandos al script

Abre `pdk_info.sh` (`gedit pdk_info.sh &`) y pega cada comando entre `$(` y `)`. El script debe funcionar
con **cualquier** celda, así que cambia lo que escribiste para `nand2_1` por las variables que el script ya
tiene listas:

| En la terminal escribiste… | En el script va… |
| --- | --- |
| `'cell ("sky130_fd_sc_hd__nand2_1")'` | `"$PATRON_LIB"` |
| `"MACRO sky130_fd_sc_hd__nand2_1"` | `"$PATRON_LEF"` |
| `sed -n '/^MACRO …/p' $CELLLEF` | `echo "$BLOQUE"` |
| `$LIB_TT` | `"$LIB"` |
| `$CELLLEF` | `"$LEF"` |

Por ejemplo, el TODO 1 queda así:

```bash
AREA=$(grep -A500 "$PATRON_LIB" "$LIB" | grep "area :" | head -1 | awk '{print $3}' | tr -d ';')
```

Pruébalo con varias celdas:

```bash
make celda CELDA=nand2_1
make celda CELDA=dfrtp_1        # el flip-flop que usará el semáforo
make celda CELDA=inv_1          # ojo: también existen inv_12 e inv_16 (para eso es el head -1)
```

Con `pdk_info.sh` llena la tabla de `notas_pdk.md` (la tercera celda la eliges tú).

### 4.4 Ver la celda

```bash
make klayout CELDA=nand2_1
```

Saca la celda del GDS de la librería y la abre en KLayout con los colores de SKY130.
Busca: los rieles de alimentación arriba y abajo (`met1`), el polisilicio de las compuertas
y los pines `A`, `B`, `Y`. ¿Coincide el ancho con lo que dijo `pdk_info.sh`?

---

## Final

```bash
git add notas_pdk.md pdk_info.sh respuestas_rutas.txt
git commit -m "lab01: notas del PDK y pdk_info.sh"
git push
make entrega                # debe decir "LISTO para entregar"
```

## ¿Te atoraste?

Las soluciones están en la rama `soluciones` del repo del curso. Úsalas para **comparar**, no para copiar:

```bash
git fetch upstream
git diff alumno/<tu-nombre> upstream/soluciones -- pdk_info.sh
```

## Origen

Lab nuevo del curso. La estructura del repo y el `.gitignore` vienen de `galletas-y-postres-chips`.
