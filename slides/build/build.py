#!/usr/bin/env python3
"""
build.py · Slides del curso: Markdown + Mermaid  ->  PowerPoint (plantilla EELCCOM)

Uso (desde la raíz del repo o desde slides/):
    python3 slides/build/build.py sesion1        # una presentación
    python3 slides/build/build.py --all          # todas las slides/<deck>/<deck>.md
    python3 slides/build/build.py sesion1 --force-mermaid   # re-renderiza todos los .mmd

Entrada : slides/<deck>/<deck>.md   (+ slides/<deck>/diagramas/*.mmd, imágenes)
Salida  : slides/out/<deck>.pptx
Formato del .md: ver slides/README.md

Requisitos: python-pptx (pip) y, para los diagramas, mermaid-cli (`mmdc`, npm).
Si falta `mmdc`, se usa el último PNG renderizado o se pone un recuadro de aviso.
"""
import argparse
import math
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from lxml import etree
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

HERE = Path(__file__).resolve().parent          # slides/build
SLIDES = HERE.parent                            # slides
ASSETS = HERE / "assets"
OUT = SLIDES / "out"

# =====================================================================
#  TEMA EELCCOM  (cámbialo aquí y se regenera todo)
# =====================================================================
COLORES = {                      # barras de título (los de ParteDigital)
    "negro": "000000",
    "morado": "9933FF",
    "rosa": "FF3399",
    "cian": "61CBF4",
    "verde": "00B050",
    "amarillo": "FFC000",
}
TEXTO_SOBRE = {"cian": "FFFFFF", "amarillo": "000000"}   # color de texto de la barra (default blanco)
TINTA = "1A1A1A"          # texto normal
GRIS = "7F7F7F"           # pie de página
BORDE = "595959"          # cajitas de viñeta
CALLOUT = "C2F1C8"        # recuadro verde de "la idea clave"
TERMINAL = "F2F2F2"       # fondo de bloques de código
COMENTARIO = "E46C0A"     # comentarios dentro del código

F_TITULO = "Comic Sans MS"          # barras de título
F_PORTADA = "Berlin Sans FB Demi"   # título de portada/sección/cierre
F_TEXTO = "Comic Sans MS"
F_CODIGO = "Consolas"

W, H = 13.333, 7.5                  # 16:9 como ParteDigital (960x540 pt)
SIDEBAR_X = 11.38                   # barra negra de logos en portada/sección/cierre
MARGEN = 0.6
Y_CUERPO, Y_FIN = 1.2, 6.85         # zona útil bajo la barra de título

LAYOUTS = ("portada", "seccion", "contenido", "diagrama", "codigo", "cierre")


def rgb(h):
    return RGBColor.from_string(h)


# =====================================================================
#  PARSER DEL MARKDOWN
# =====================================================================
class Slide:
    def __init__(self):
        self.dir = {}            # directivas <!-- clave: valor -->
        self.notas = ""
        self.titulo = ""
        self.subtitulo = ""      # línea "## ..."
        self.bloques = []        # [("bullets", [(nivel, texto)]), ("callout", txt), ("img", ruta),
                                 #  ("code", lang, etiqueta, txt), ("tabla", filas), ("parrafo", txt)]


def leer_deck(md_path):
    txt = Path(md_path).read_text(encoding="utf-8")
    meta = {}
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", txt, re.S)
    if m:
        for linea in m.group(1).splitlines():
            if ":" in linea:
                k, v = linea.split(":", 1)
                meta[k.strip()] = v.strip()
        txt = txt[m.end():]

    # separar slides por líneas '---' fuera de bloques de código
    trozos, actual, en_code = [], [], False
    for linea in txt.splitlines():
        if linea.strip().startswith("```"):
            en_code = not en_code
        if not en_code and linea.strip() == "---":
            trozos.append("\n".join(actual))
            actual = []
        else:
            actual.append(linea)
    trozos.append("\n".join(actual))
    slides = [parse_slide(t) for t in trozos if t.strip()]
    return meta, slides


def parse_slide(t):
    s = Slide()
    # directivas y notas en comentarios HTML
    for m in re.finditer(r"<!--\s*([\wñ]+)\s*:\s*(.*?)\s*-->", t, re.S):
        k, v = m.group(1).lower(), m.group(2)
        if k == "notas":
            s.notas = "\n".join(l.strip() for l in v.strip().splitlines())
        else:
            s.dir[k] = v.strip()
    t = re.sub(r"<!--.*?-->", "", t, flags=re.S)

    lineas = t.splitlines()
    i = 0
    bullets = []

    def cerrar_bullets():
        nonlocal bullets
        if bullets:
            s.bloques.append(("bullets", bullets))
            bullets = []

    while i < len(lineas):
        l = lineas[i]
        st = l.strip()
        if st.startswith("```"):
            cerrar_bullets()
            info = st[3:].strip().split(None, 1)
            lang = info[0] if info else ""
            etiqueta = info[1] if len(info) > 1 else ""
            cuerpo = []
            i += 1
            while i < len(lineas) and not lineas[i].strip().startswith("```"):
                cuerpo.append(lineas[i])
                i += 1
            s.bloques.append(("code", lang, etiqueta, "\n".join(cuerpo)))
        elif st.startswith("## "):
            cerrar_bullets()
            s.subtitulo = st[3:].strip()
        elif st.startswith("# "):
            cerrar_bullets()
            s.titulo = st[2:].strip()
        elif re.match(r"^\s*[-*] ", l):
            nivel = 1 if (len(l) - len(l.lstrip())) >= 2 else 0
            bullets.append((nivel, re.sub(r"^\s*[-*] ", "", l).strip()))
        elif st.startswith(">"):
            cerrar_bullets()
            txt = [st.lstrip("> ").strip()]
            while i + 1 < len(lineas) and lineas[i + 1].strip().startswith(">"):
                i += 1
                txt.append(lineas[i].strip().lstrip("> ").strip())
            s.bloques.append(("callout", " ".join(txt)))
        elif re.match(r"^!\[.*?\]\(.+?\)", st):
            cerrar_bullets()
            ruta = re.match(r"^!\[.*?\]\((.+?)\)", st).group(1)
            s.bloques.append(("img", ruta))
        elif st.startswith("|"):
            cerrar_bullets()
            filas = []
            while i < len(lineas) and lineas[i].strip().startswith("|"):
                celdas = [c.strip() for c in lineas[i].strip().strip("|").split("|")]
                if not all(re.match(r"^:?-+:?$", c) for c in celdas):
                    filas.append(celdas)
                i += 1
            i -= 1
            s.bloques.append(("tabla", filas))
        elif st:
            cerrar_bullets()
            s.bloques.append(("parrafo", st))
        i += 1
    cerrar_bullets()
    return s


def inferir_layout(s, idx):
    if s.dir.get("layout"):
        lay = s.dir["layout"].lower()
        if lay not in LAYOUTS:
            sys.exit(f"ERROR: layout '{lay}' no existe. Usa uno de: {', '.join(LAYOUTS)}")
        return lay
    tipos = {b[0] for b in s.bloques}
    if idx == 0:
        return "portada"
    if "code" in tipos:
        return "codigo"
    if "img" in tipos:
        return "diagrama"
    return "contenido"


# =====================================================================
#  MERMAID
# =====================================================================
def render_mermaid(mmd, deck_dir, forzar=False):
    """Renderiza .mmd -> _render/<nombre>.png (solo si cambió). Devuelve la ruta o None."""
    out_dir = deck_dir / "_render"
    out_dir.mkdir(exist_ok=True)
    png = out_dir / (mmd.stem + ".png")
    cfg = HERE / "mermaid-config.json"
    pup = HERE / "puppeteer-config.json"
    al_dia = png.exists() and png.stat().st_mtime >= max(mmd.stat().st_mtime, cfg.stat().st_mtime)
    if al_dia and not forzar:
        return png
    mmdc = shutil.which("mmdc")
    if not mmdc:
        print(f"  !! falta mmdc: no puedo renderizar {mmd.name}" + (" (uso el PNG anterior)" if png.exists() else ""))
        return png if png.exists() else None
    cmd = [mmdc, "-i", str(mmd), "-o", str(png), "-c", str(cfg), "-p", str(pup),
           "-b", "transparent", "-w", "2000", "-s", "2", "-q"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  !! mmdc falló con {mmd.name}:\n{r.stderr.strip()[-800:]}")
        return png if png.exists() else None
    print(f"  mermaid -> {png.relative_to(SLIDES)}")
    return png


def resolver_imagen(ruta, deck_dir, forzar):
    p = (deck_dir / ruta).resolve()
    if not p.exists():
        print(f"  !! no existe la imagen {ruta}")
        return None
    if p.suffix == ".mmd":
        return render_mermaid(p, deck_dir, forzar)
    return p


# =====================================================================
#  PRIMITIVAS DE DIBUJO
# =====================================================================
def sombra(shape):
    """Sombra suave abajo-derecha (python-pptx no la expone)."""
    spPr = shape._element.spPr
    eff = etree.SubElement(spPr, qn("a:effectLst"))
    sh = etree.SubElement(eff, qn("a:outerShdw"), blurRad="38100", dist="25400", dir="2700000",
                          algn="tl", rotWithShape="0")
    clr = etree.SubElement(sh, qn("a:srgbClr"), val="000000")
    etree.SubElement(clr, qn("a:alpha"), val="35000")


def caja(slide, x, y, w, h, relleno=None, borde=None, grosor=1.0, redondeo=None, nombre=None):
    forma = MSO_SHAPE.ROUNDED_RECTANGLE if redondeo is not None else MSO_SHAPE.RECTANGLE
    sp = slide.shapes.add_shape(forma, Inches(x), Inches(y), Inches(w), Inches(h))
    if redondeo is not None:
        sp.adjustments[0] = redondeo
    if relleno:
        sp.fill.solid()
        sp.fill.fore_color.rgb = rgb(relleno)
    else:
        sp.fill.background()
    if borde:
        sp.line.color.rgb = rgb(borde)
        sp.line.width = Pt(grosor)
    else:
        sp.line.fill.background()
    sp.shadow.inherit = False
    if nombre:
        sp.name = nombre
    return sp


def runs_inline(p, texto, size, color=TINTA, fuente=F_TEXTO, negrita=False, cursiva=False):
    """**negrita**, *cursiva* y `código` dentro de un párrafo (se pueden anidar: **`x`**)."""
    for parte in re.split(r"(\*\*.+?\*\*|`.+?`|\*.+?\*)", texto):
        if not parte:
            continue
        if parte.startswith("**") and len(parte) > 4:
            runs_inline(p, parte[2:-2], size, color, fuente, True, cursiva)
            continue
        if parte.startswith("*") and not parte.startswith("**") and len(parte) > 2:
            runs_inline(p, parte[1:-1], size, color, fuente, negrita, True)
            continue
        r = p.add_run()
        f = r.font
        f.size = Pt(size)
        f.color.rgb = rgb(color)
        f.name = fuente
        f.bold = negrita
        f.italic = cursiva
        if parte.startswith("`"):
            r.text, f.name = parte[1:-1], F_CODIGO
        else:
            r.text = parte


def texto(slide, x, y, w, h, contenido, size=18, color=TINTA, fuente=F_TEXTO, negrita=False,
          alinear=PP_ALIGN.LEFT, ancla=MSO_ANCHOR.TOP, margen=0.08, nombre=None, italica=False):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = ancla
    for lado in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
        setattr(tf, lado, Inches(margen))
    lineas = contenido if isinstance(contenido, list) else [contenido]
    for k, l in enumerate(lineas):
        p = tf.paragraphs[0] if k == 0 else tf.add_paragraph()
        p.alignment = alinear
        runs_inline(p, l, size, color, fuente, negrita)
        if italica:
            for r in p.runs:
                r.font.italic = True
    if nombre:
        tb.name = nombre
    return tb


def limpiar_md(t):
    return re.sub(r"\*\*|`|\*", "", t)


def lineas_est(t, ancho_in, size, ch=0.55):
    """Estimación de cuántas líneas ocupa un texto (Comic Sans ~0.55 em por carácter)."""
    cpl = max(1, int(ancho_in * 72 / (size * ch)))
    return max(1, math.ceil(len(limpiar_md(t)) / cpl))


def ancho_est(t, size, ch=0.55):
    return len(limpiar_md(t)) * size * ch / 72


def imagen_ajustada(slide, png, x, y, w, h, nombre=None):
    from PIL import Image
    with Image.open(png) as im:
        iw, ih = im.size
    esc = min(w / iw, h / ih)
    pw, ph = iw * esc, ih * esc
    pic = slide.shapes.add_picture(str(png), Inches(x + (w - pw) / 2), Inches(y + (h - ph) / 2),
                                   Inches(pw), Inches(ph))
    if nombre:
        pic.name = nombre
    return pic


def aviso_imagen(slide, x, y, w, h, ruta):
    c = caja(slide, x, y, w, h, relleno="FFF2CC", borde="BF9000", redondeo=0.05)
    texto(slide, x, y, w, h, f"Falta el render de {ruta}\n(instala mermaid-cli: npm i -g @mermaid-js/mermaid-cli)",
          size=16, alinear=PP_ALIGN.CENTER, ancla=MSO_ANCHOR.MIDDLE)
    return c


# =====================================================================
#  PIEZAS DE LA PLANTILLA
# =====================================================================
def fondo(slide):
    slide.shapes.add_picture(str(ASSETS / "fondo_circuito.png"), 0, 0, Inches(W), Inches(H)).name = "fondo"


def barra_logos(slide):
    slide.shapes.add_picture(str(ASSETS / "sidebar.png"), Inches(SIDEBAR_X), 0,
                             Inches(W - SIDEBAR_X), Inches(H)).name = "logos"


def barra_titulo(slide, titulo, color):
    hexc = COLORES.get(color, color)
    caja(slide, 1.05, 0.22, W - 2.1, 0.72, relleno=hexc, borde="000000", grosor=1.25,
         redondeo=0.12, nombre="barra_titulo")
    texto(slide, 1.05, 0.22, W - 2.1, 0.72, titulo, size=30, color=TEXTO_SOBRE.get(color, "FFFFFF"),
          fuente=F_TITULO, negrita=True, alinear=PP_ALIGN.CENTER, ancla=MSO_ANCHOR.MIDDLE, nombre="titulo")
    for x in (0.25, W - 0.95):
        slide.shapes.add_picture(str(ASSETS / "icono_chip.png"), Inches(x), Inches(0.2),
                                 Inches(0.72), Inches(0.72)).name = "icono_chip"


def pie(slide, meta, n):
    texto(slide, 0.3, 7.05, 4, 0.35, f"By: {meta.get('autor_corto', 'C. Otamendi')}", size=11,
          color=GRIS, nombre="pie_autor")
    texto(slide, W - 1.3, 7.05, 1.0, 0.35, str(n), size=11, color=GRIS, alinear=PP_ALIGN.RIGHT,
          nombre="pie_numero")


def callout(slide, txt, x, y_fondo, ancho_max, size=16):
    w = min(ancho_max, ancho_est(txt, size) + 0.6)
    nl = lineas_est(txt, w - 0.3, size)
    h = nl * size * 1.3 / 72 + 0.25
    y = y_fondo - h
    cx = x + (ancho_max - w) / 2
    c = caja(slide, cx, y, w, h, relleno=CALLOUT, borde="000000", grosor=1.0, nombre="callout")
    sombra(c)
    texto(slide, cx, y, w, h, txt, size=size, negrita=True, alinear=PP_ALIGN.CENTER,
          ancla=MSO_ANCHOR.MIDDLE, nombre="callout_texto")
    return y


def cajas_vinetas(slide, items, x, y0, w, y1):
    """Cada viñeta de nivel 0 en su cajita con la empanada a la izquierda (estilo ParteDigital).
    Las de nivel 1 van dentro de la caja de su padre."""
    grupos = []
    for nivel, t in items:
        if nivel == 0 or not grupos:
            grupos.append([t])
        else:
            grupos[-1].append(t)
    alto_disp = y1 - y0
    for size in (20, 18, 16, 14):
        sub = size - 2
        wtxt = w - 0.55 - 0.25
        alturas = []
        for g in grupos:
            nl = lineas_est(g[0], wtxt, size) * size + sum(lineas_est(t, wtxt - 0.3, sub) * sub for t in g[1:])
            alturas.append(nl * 1.3 / 72 + 0.22)
        if sum(alturas) + 0.2 * (len(grupos) - 1) <= alto_disp:
            break
    hueco = min(0.4, (alto_disp - sum(alturas)) / max(1, len(grupos)))
    y = y0
    for g, h in zip(grupos, alturas):
        ancho = min(w - 0.55, max(ancho_est(g[0], size), *[ancho_est(t, sub) + 0.3 for t in g[1:]], 1.0) + 0.35)
        slide.shapes.add_picture(str(ASSETS / "vineta.png"), Inches(x), Inches(y + h / 2 - 0.2),
                                 Inches(0.42), Inches(0.4)).name = "vineta"
        c = caja(slide, x + 0.55, y, ancho, h, relleno="FFFFFF", borde=BORDE, grosor=0.75, nombre="caja_vineta")
        sombra(c)
        tb = texto(slide, x + 0.55, y, ancho, h, g[0], size=size, ancla=MSO_ANCHOR.MIDDLE, margen=0.1,
                   nombre="vineta_texto")
        tf = tb.text_frame
        for t in g[1:]:
            p = tf.add_paragraph()
            p.level = 1
            runs_inline(p, "–  " + t, sub)
        y += h + hueco
    return y


def anchos_columnas(filas, nc, w, size):
    """Ninguna columna más angosta que su palabra más larga; el resto se reparte según el texto."""
    def celdas(c):
        return [limpiar_md(f[c]) if c < len(f) else "" for f in filas]
    palabra = [max((len(p) for t in celdas(c) for p in t.split()), default=1) for c in range(nc)]
    minimos = [pw * size * 0.6 / 72 + 0.25 for pw in palabra]
    if sum(minimos) > w:
        return None
    texto = [min(40, max(len(t) for t in celdas(c))) for c in range(nc)]
    sobra = w - sum(minimos)
    return [m + sobra * t / sum(texto) for m, t in zip(minimos, texto)]


def tabla(slide, filas, x, y, w, color, size=None):
    nf, nc = len(filas), max(len(f) for f in filas)
    tamanos = [size] if size else ([20, 18, 16, 14, 12] if nf <= 4 else [16, 14, 12] if nf <= 7 else [14, 12])
    for size in tamanos:
        anchos = anchos_columnas(filas, nc, w, size)
        if anchos:
            break
    if not anchos:
        anchos = [w / nc] * nc
    alto_fila = size * 1.9 / 72
    gt = slide.shapes.add_table(nf, nc, Inches(x), Inches(y), Inches(w), Inches(alto_fila * nf))
    gt.name = "tabla"
    tbl = gt.table
    # sin estilo por defecto de Office
    tblPr = tbl._tbl.tblPr
    for attr in ("bandRow", "firstRow"):
        tblPr.set(attr, "0")
    for c in range(nc):
        tbl.columns[c].width = Emu(int(Inches(anchos[c])))
    hexc = COLORES.get(color, color)
    for r, fila in enumerate(filas):
        tbl.rows[r].height = Inches(alto_fila)
        for c in range(nc):
            cel = tbl.cell(r, c)
            cel.fill.solid()
            cel.fill.fore_color.rgb = rgb(hexc if r == 0 else ("FFFFFF" if r % 2 else "F2F2F2"))
            tf = cel.text_frame
            tf.word_wrap = True
            cel.vertical_anchor = MSO_ANCHOR.MIDDLE
            p = tf.paragraphs[0]
            p.alignment = PP_ALIGN.CENTER
            txt = fila[c] if c < len(fila) else ""
            runs_inline(p, txt, size, color=TEXTO_SOBRE.get(color, "FFFFFF") if r == 0 else TINTA,
                        negrita=(r == 0 or c == 0))
    return y + alto_fila * nf


def bloque_codigo(slide, lang, etiqueta, codigo, x, y, w, h_max, color):
    """Terminal clara con los tres puntitos (como en ParteDigital) + etiqueta opcional."""
    if etiqueta:
        hexc = COLORES.get(color, color)
        wl = ancho_est(etiqueta, 15) + 0.5
        caja(slide, x, y, wl, 0.4, relleno=hexc, borde="000000", grosor=1.0, nombre="etiqueta_codigo")
        texto(slide, x, y, wl, 0.4, etiqueta, size=15, color=TEXTO_SOBRE.get(color, "FFFFFF"), negrita=True,
              alinear=PP_ALIGN.CENTER, ancla=MSO_ANCHOR.MIDDLE, margen=0.02)
        y += 0.55
    lineas = codigo.splitlines() or [""]
    larga = max(len(l) for l in lineas)
    for size in (20, 18, 16, 15, 14, 13, 12):
        alto = len(lineas) * size * 1.25 / 72 + 0.65
        if alto <= h_max - (0.55 if etiqueta else 0) and larga * size * 0.56 / 72 <= w - 0.45:
            break
    alto = min(alto, h_max)
    c = caja(slide, x, y, w, alto, relleno=TERMINAL, borde="BFBFBF", grosor=0.75, redondeo=0.04,
             nombre="terminal")
    sombra(c)
    for k, col in enumerate(("FF5F56", "FFBD2E", "27C93F")):
        p = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x + 0.2 + k * 0.25), Inches(y + 0.15),
                                   Inches(0.15), Inches(0.15))
        p.fill.solid()
        p.fill.fore_color.rgb = rgb(col)
        p.line.fill.background()
        p.shadow.inherit = False
    tb = slide.shapes.add_textbox(Inches(x + 0.15), Inches(y + 0.4), Inches(w - 0.3), Inches(alto - 0.45))
    tb.name = "codigo"
    tf = tb.text_frame
    tf.word_wrap = True      # con False, LibreOffice/PowerPoint pueden recentrar el texto
    for lado in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
        setattr(tf, lado, Inches(0.08))
    for k, l in enumerate(lineas):
        p = tf.paragraphs[0] if k == 0 else tf.add_paragraph()
        r = p.add_run()
        r.text = l if l else " "
        r.font.name = F_CODIGO
        r.font.size = Pt(size)
        es_com = l.lstrip().startswith(("#", "//", "--"))
        r.font.color.rgb = rgb(COMENTARIO if es_com else TINTA)
    return y + alto


# =====================================================================
#  LAYOUTS
# =====================================================================
def bloques_de(s, tipo):
    return [b for b in s.bloques if b[0] == tipo]


def cuerpo_texto(slide, s, x, y0, w, y1, color):
    """Pinta viñetas, párrafos y tabla en una columna; el callout va abajo."""
    calls = bloques_de(s, "callout")
    if calls:
        y1 = callout(slide, calls[0][1], x, y1, w) - 0.3
    y = y0
    for b in s.bloques:
        if b[0] == "bullets":
            y = cajas_vinetas(slide, b[1], x, y, w, y1)
        elif b[0] == "parrafo":
            nl = lineas_est(b[1], w, 18)
            texto(slide, x, y, w, nl * 0.33 + 0.15, b[1], size=18, nombre="parrafo")
            y += nl * 0.33 + 0.3
        elif b[0] == "tabla":
            y = tabla(slide, b[1], x, y, w, color) + 0.3
    return y


def lay_portada(slide, s, meta, color, deck_dir, forzar, cierre=False):
    fondo(slide)
    barra_logos(slide)
    ancho = SIDEBAR_X - 2 * 0.5
    if s.subtitulo:
        texto(slide, 0.5, 0.3, ancho, 0.55, s.subtitulo, size=24, alinear=PP_ALIGN.CENTER, nombre="lema")
    texto(slide, 0.5, 0.85, ancho, 0.9, s.titulo, size=36, fuente=F_PORTADA, negrita=True,
          alinear=PP_ALIGN.CENTER, ancla=MSO_ANCHOR.MIDDLE, nombre="titulo")
    imgs = bloques_de(s, "img")
    zona = (0.9, 1.95, ancho - 0.8, 4.75)
    if imgs:
        png = resolver_imagen(imgs[0][1], deck_dir, forzar)
        if png:
            imagen_ajustada(slide, png, *zona, nombre="ilustracion")
        else:
            aviso_imagen(slide, *zona, imgs[0][1])
    else:
        cuerpo_texto(slide, s, 1.3, 2.2, ancho - 1.6, 6.6, color)
    texto(slide, 0.5, 6.85, 6, 0.45, f"By: {meta.get('autor', 'Cesar Otamendi')}", size=18, nombre="autor")


def lay_seccion(slide, s, meta, color, n):
    fondo(slide)
    barra_logos(slide)
    ancho = SIDEBAR_X - 1.0
    hexc = COLORES.get(color, color)
    if s.subtitulo:
        texto(slide, 0.5, 2.05, ancho, 0.6, s.subtitulo, size=24, alinear=PP_ALIGN.CENTER,
              italica=True, nombre="lema")
    c = caja(slide, 1.0, 2.8, ancho - 1.0, 1.4, relleno=hexc, borde="000000", grosor=1.5, redondeo=0.15,
             nombre="barra_seccion")
    sombra(c)
    texto(slide, 1.0, 2.8, ancho - 1.0, 1.4, s.titulo, size=40, color=TEXTO_SOBRE.get(color, "FFFFFF"),
          fuente=F_PORTADA, negrita=True, alinear=PP_ALIGN.CENTER, ancla=MSO_ANCHOR.MIDDLE, nombre="titulo")
    calls = bloques_de(s, "callout")
    if calls:
        callout(slide, calls[0][1], 1.0, 5.6, ancho - 1.0, size=18)
    texto(slide, 0.5, 6.85, 6, 0.45, f"By: {meta.get('autor', 'Cesar Otamendi')}", size=18, nombre="autor")


def lay_contenido(slide, s, meta, color, deck_dir, forzar, n):
    fondo(slide)
    barra_titulo(slide, s.titulo, color)
    imgs = bloques_de(s, "img")
    if imgs:
        cuerpo_texto(slide, s, MARGEN, Y_CUERPO + 0.15, 6.5, Y_FIN, color)
        png = resolver_imagen(imgs[0][1], deck_dir, forzar)
        zona = (7.4, Y_CUERPO + 0.15, W - 7.4 - MARGEN, Y_FIN - Y_CUERPO - 0.15)
        imagen_ajustada(slide, png, *zona, nombre="imagen") if png else aviso_imagen(slide, *zona, imgs[0][1])
    else:
        cuerpo_texto(slide, s, MARGEN + 0.4, Y_CUERPO + 0.15, W - 2 * MARGEN - 0.8, Y_FIN, color)
    pie(slide, meta, n)


def lay_diagrama(slide, s, meta, color, deck_dir, forzar, n):
    fondo(slide)
    barra_titulo(slide, s.titulo, color)
    y1 = Y_FIN
    calls = bloques_de(s, "callout")
    if calls:
        y1 = callout(slide, calls[0][1], MARGEN, Y_FIN, W - 2 * MARGEN) - 0.25
    x0, w = MARGEN, W - 2 * MARGEN
    vin = bloques_de(s, "bullets")
    if vin:                                  # viñetas a la izquierda, diagrama a la derecha
        cajas_vinetas(slide, vin[0][1], MARGEN, Y_CUERPO + 0.15, 4.4, y1)
        x0, w = 5.3, W - 5.3 - MARGEN
    imgs = bloques_de(s, "img")
    zona = (x0, Y_CUERPO + 0.1, w, y1 - Y_CUERPO - 0.1)
    if imgs:
        png = resolver_imagen(imgs[0][1], deck_dir, forzar)
        imagen_ajustada(slide, png, *zona, nombre="diagrama") if png else aviso_imagen(slide, *zona, imgs[0][1])
    pie(slide, meta, n)


def lay_codigo(slide, s, meta, color, n):
    fondo(slide)
    barra_titulo(slide, s.titulo, color)
    codigos = bloques_de(s, "code")
    lado = [b for b in s.bloques if b[0] in ("bullets", "callout", "parrafo")]
    wcod = 7.6 if lado else W - 2 * MARGEN
    y = Y_CUERPO + 0.15
    alto_c = (Y_FIN - y - 0.3 * (len(codigos) - 1)) / max(1, len(codigos))
    for _, lang, etq, cod in codigos:
        y = bloque_codigo(slide, lang, etq, cod, MARGEN, y, wcod, alto_c, color) + 0.3
    if lado:
        x = MARGEN + wcod + 0.4
        cuerpo_texto(slide, s, x, Y_CUERPO + 0.15, W - x - MARGEN, Y_FIN, color)
    pie(slide, meta, n)


# =====================================================================
#  ARMADO
# =====================================================================
def construir(deck, forzar=False):
    deck_dir = SLIDES / deck
    md = deck_dir / f"{deck}.md"
    if not md.exists():
        sys.exit(f"ERROR: no existe {md.relative_to(SLIDES.parent)}")
    meta, slides = leer_deck(md)
    color_deck = meta.get("color", "morado")
    print(f">> {deck}: {len(slides)} slides")

    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(W), Inches(H)
    prs.core_properties.title = meta.get("titulo", deck)
    prs.core_properties.author = meta.get("autor", "Cesar Otamendi")
    prs.core_properties.last_modified_by = meta.get("autor", "Cesar Otamendi")
    prs.core_properties.comments = ""
    blank = prs.slide_layouts[6]

    for n, s in enumerate(slides, 1):
        lay = inferir_layout(s, n - 1)
        color = s.dir.get("color", color_deck)
        sl = prs.slides.add_slide(blank)
        if lay == "portada":
            lay_portada(sl, s, meta, color, deck_dir, forzar)
        elif lay == "cierre":
            lay_portada(sl, s, meta, color, deck_dir, forzar, cierre=True)
        elif lay == "seccion":
            lay_seccion(sl, s, meta, color, n)
        elif lay == "diagrama":
            lay_diagrama(sl, s, meta, color, deck_dir, forzar, n)
        elif lay == "codigo":
            lay_codigo(sl, s, meta, color, n)
        else:
            lay_contenido(sl, s, meta, color, deck_dir, forzar, n)
        if s.notas:
            sl.notes_slide.notes_text_frame.text = s.notas
        print(f"   {n:2d}. [{lay:9s}] {s.titulo}")

    OUT.mkdir(exist_ok=True)
    dest = OUT / f"{deck}.pptx"
    prs.save(dest)
    print(f">> listo: {dest.relative_to(SLIDES.parent)}")
    return dest


def main():
    ap = argparse.ArgumentParser(description="Markdown + Mermaid -> .pptx (plantilla EELCCOM)")
    ap.add_argument("deck", nargs="?", help="nombre de la carpeta en slides/ (p.ej. sesion1)")
    ap.add_argument("--all", action="store_true", help="construye todas las presentaciones")
    ap.add_argument("--force-mermaid", action="store_true", help="re-renderiza todos los .mmd")
    a = ap.parse_args()
    if a.all:
        decks = sorted(p.name for p in SLIDES.iterdir() if (p / f"{p.name}.md").exists())
        if not decks:
            print("No hay presentaciones con slides/<deck>/<deck>.md todavía.")
        for d in decks:
            construir(d, a.force_mermaid)
    elif a.deck:
        construir(a.deck, a.force_mermaid)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
