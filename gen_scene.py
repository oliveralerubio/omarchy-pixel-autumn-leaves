#!/usr/bin/env python3
"""
Generador procedural de escena pixel art otoñal (480x270).
Genera scene.png y trees.json con semilla fija.
"""
import json, math, os, random, sys
from PIL import Image, ImageDraw, ImageFilter, ImageChops

W, H = 480, 270
GROUND_Y = 222
GROUND_MAX = 262
HERE = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))

rnd = random.Random(20261103)

def mix(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))

def hexc(s):
    s = s.lstrip('#').replace(' ', '')
    return tuple(int(s[i:i+2], 16) for i in (0, 2, 4))

BAYER = [
    [0,  8,  2, 10],
    [12, 4, 14,  6],
    [3, 11,  1,  9],
    [15, 7, 13,  5]
]

img = Image.new("RGB", (W, H), (0, 0, 0))
px = img.load()

# ==========================================
# 1. CIELO ATARDECER OTOÑAL CON DITHERING
# ==========================================
sky_cols = [
    hexc("#34224e"), # morado crepuscular
    hexc("#4e2e5c"),
    hexc("#6c3666"),
    hexc("#8d406d"),
    hexc("#af4d6d"),
    hexc("#cb5f68"),
    hexc("#e27863"),
    hexc("#f29663"),
    hexc("#fbb86e"),
    hexc("#fdd684"),
    hexc("#fff0a8")  # resplandor dorado del horizonte
]

SKY_H = 196
nb = len(sky_cols) - 1
for y in range(SKY_H):
    f = (y / (SKY_H - 1)) * nb
    i = min(int(f), nb - 1)
    frac = f - i
    for x in range(W):
        use_next = (frac * 16) > BAYER[y % 4][x % 4]
        px[x, y] = sky_cols[i + 1] if use_next else sky_cols[i]

d = ImageDraw.Draw(img)

# ==========================================
# 2. SOL DE OTOÑO CON HALO SUAVE
# ==========================================
sx, sy = 120, 115
for r, col in ((52, "#f8b67a"), (42, "#fac584"), (32, "#fcd690"), (22, "#fee6a4")):
    c = hexc(col)
    r2 = r * r
    for yy in range(sy - r, sy + r + 1):
        for xx in range(sx - r, sx + r + 1):
            if (xx - sx)**2 + (yy - sy)**2 <= r2 and 0 <= xx < W and 0 <= yy < H:
                if (xx + yy) % 2 == 0 or r <= 24:
                    px[xx, yy] = c

d.ellipse([sx - 13, sy - 13, sx + 13, sy + 13], fill=hexc("#fff5ce"))
d.ellipse([sx - 8, sy - 8, sx + 8, sy + 8], fill=hexc("#ffffff"))

# ==========================================
# 3. NUBES FLOTANTES EN CAPAS (PUFFY PIXEL ART)
# ==========================================
def draw_fluffy_cloud(cx, cy, length, base_h):
    cloud_img = Image.new("RGBA", (length + 40, base_h * 3 + 20), (0, 0, 0, 0))
    cd = ImageDraw.Draw(cloud_img)
    ox = 20
    oy = base_h * 2

    lobes = []
    num_lobes = rnd.randint(5, 8)
    for idx in range(num_lobes):
        t = idx / (num_lobes - 1)
        lx = ox + t * length + rnd.uniform(-4, 4)
        arch = math.sin(t * math.pi)
        ly = oy - arch * base_h * rnd.uniform(0.7, 1.2)
        lr = base_h * (0.6 + 0.65 * arch) * rnd.uniform(0.85, 1.15)
        lobes.append((lx, ly, lr))

    shade_col = hexc("#b25e74") + (220,)
    for lx, ly, lr in lobes:
        cd.ellipse([lx - lr * 1.3, ly - lr * 0.9 + 2, lx + lr * 1.3, ly + lr * 0.9 + 4], fill=shade_col)
    cd.rectangle([ox - 4, oy - 2, ox + length + 4, oy + base_h * 0.4], fill=shade_col)

    mid_col = hexc("#e88b80") + (240,)
    for lx, ly, lr in lobes:
        cd.ellipse([lx - lr * 1.25, ly - lr * 0.85, lx + lr * 1.25, ly + lr * 0.85], fill=mid_col)

    hi_col = hexc("#fed3a8") + (255,)
    for lx, ly, lr in lobes:
        cd.ellipse([lx - lr * 0.95 - 2, ly - lr * 0.85 - 2, lx + lr * 0.7, ly + lr * 0.25], fill=hi_col)
        if lr > base_h * 0.8:
            cd.ellipse([lx - lr * 0.7 - 2, ly - lr * 0.8 - 2, lx + lr * 0.2, ly - lr * 0.1], fill=hexc("#fff0d0") + (255,))

    dest_x = int(cx - length / 2 - ox)
    dest_y = int(cy - oy)
    img.paste(cloud_img, (dest_x, dest_y), cloud_img)

cloud_specs = [
    (65, 42, 75, 14),
    (245, 34, 110, 16),
    (415, 52, 90, 15),
    (345, 88, 65, 11),
    (25, 96, 50, 10),
    (180, 85, 45, 8)
]
for cs in cloud_specs:
    draw_fluffy_cloud(*cs)

birds = [(185, 66), (195, 60), (206, 67), (170, 76), (178, 81), (218, 73)]
for bx, by in birds:
    for dx, dy in ((-2, 0), (-1, 1), (0, 0), (1, 1), (2, 0)):
        if 0 <= bx + dx < W and 0 <= by + dy < H:
            px[bx + dx, by + dy] = hexc("#482645")

# ==========================================
# 4. COLINAS EN PLANOS DE PROFUNDIDAD
# ==========================================
HAZE = (235, 185, 140)

def draw_hill(base_y, amp, f1, f2, ph, col_top, col_bot, haze):
    for x in range(W):
        hy = base_y + amp * math.sin(x * f1 + ph) + amp * 0.45 * math.sin(x * f2 + ph * 1.7)
        top = int(hy)
        for y in range(top, H):
            t = min(1.0, (y - top) / 36.0)
            c = mix(col_top, col_bot, t)
            if haze > 0:
                c = mix(c, HAZE, haze)
            if (y - top) < 2 and (x + y) % 2 == 0:
                c = mix(c, col_top, 0.4)
            px[x, y] = c

# Plano 1: Colina lejana
draw_hill(162, 11, 0.011, 0.027, 0.5, hexc("#96637e"), hexc("#af7482"), 0.22)
for x in range(2, W - 2, 7):
    if rnd.random() < 0.8:
        hy = 162 + 11 * math.sin(x * 0.011 + 0.5) + 5 * math.sin(x * 0.027 + 0.85)
        top = int(hy)
        r = rnd.randint(3, 6)
        col = rnd.choice([hexc("#b87870"), hexc("#c68572"), hexc("#a86872")])
        col = mix(col, HAZE, 0.2)
        d.ellipse([x - r, top - r - 2, x + r, top + r - 2], fill=col)

# Plano 2: Colina intermedia
draw_hill(178, 9, 0.016, 0.038, 2.3, hexc("#b26743"), hexc("#9c5737"), 0.10)
for x in range(1, W - 1, 5):
    if rnd.random() < 0.6:
        hy = 178 + 9 * math.sin(x * 0.016 + 2.3) + 4 * math.sin(x * 0.038 + 3.91)
        top = int(hy)
        r = rnd.randint(2, 5)
        col = rnd.choice([hexc("#cf7c34"), hexc("#bd682a"), hexc("#db943c")])
        col = mix(col, HAZE, 0.08)
        d.ellipse([x - r, top - r - 1, x + r, top + r - 1], fill=col)

# Plano 3: Colina cercana
draw_hill(196, 6, 0.021, 0.048, 4.1, hexc("#807537"), hexc("#6d632c"), 0.0)

# ==========================================
# 5. SUELO DE PASTO OTOÑAL
# ==========================================
GR_TOP = 208
grass_shades = [
    hexc("#787132"),
    hexc("#6b642a"),
    hexc("#5e5824"),
    hexc("#524d1f"),
    hexc("#46421a")
]
for y in range(GR_TOP, H):
    f = (y - GR_TOP) / (H - GR_TOP) * (len(grass_shades) - 1)
    idx = min(int(f), len(grass_shades) - 2)
    frac = f - idx
    for x in range(W):
        c = grass_shades[idx + 1] if (frac * 16) > BAYER[y % 4][x % 4] else grass_shades[idx]
        px[x, y] = c

# ==========================================
# 6. GENERADOR DE ÁRBOLES PROCEDURALES ESTILO REFERENCIA
# ==========================================
PALETTES = {
    "gold": [
        hexc("#340c10"), # 0: sombra profunda / base
        hexc("#641412"), # 1: carmesí oscuro
        hexc("#982614"), # 2: rojo óxido
        hexc("#c84816"), # 3: naranja intenso
        hexc("#e8741a"), # 4: ámbar brillante
        hexc("#f8a822"), # 5: amarillo dorado
        hexc("#fecf44"), # 6: amarillo cálido
        hexc("#fff28e")  # 7: luz solar intensa
    ],
    "orange": [
        hexc("#2c0a0e"),
        hexc("#561212"),
        hexc("#822212"),
        hexc("#b43c14"),
        hexc("#d86018"),
        hexc("#ee8222"),
        hexc("#f8a83a"),
        hexc("#fed068")
    ],
    "crimson": [
        hexc("#26080e"),
        hexc("#460e14"),
        hexc("#6e161a"),
        hexc("#962220"),
        hexc("#be3624"),
        hexc("#dc4e2c"),
        hexc("#ee7038"),
        hexc("#fa9858")
    ],
    "amber": [
        hexc("#2e100e"),
        hexc("#501e10"),
        hexc("#742e12"),
        hexc("#9c4816"),
        hexc("#be681c"),
        hexc("#dc8824"),
        hexc("#f0aa36"),
        hexc("#fcc85e")
    ]
}

BARK = {
    "outline": hexc("#22101e"),
    "dark":    hexc("#341a22"),
    "mid":     hexc("#522c2a"),
    "light":   hexc("#7a4432"),
    "hi":      hexc("#9c603e"),
}

trees_info = []


def lerp(a, b, t):
    return a + (b - a) * t


def make_pad_mask(size, cx, cy, r):
    """Racimo orgánico de hojas: unión de elipses con bordes pixelados naturales."""
    m = Image.new("L", size, 0)
    d = ImageDraw.Draw(m)
    d.ellipse([cx - r, cy - r * 0.78, cx + r, cy + r * 0.78], fill=255)
    for _ in range(rnd.randint(4, 6)):
        a = rnd.uniform(0, 2 * math.pi)
        dist = r * rnd.uniform(0.3, 0.7)
        rr = r * rnd.uniform(0.5, 0.75)
        d.ellipse([cx + math.cos(a) * dist - rr, cy + math.sin(a) * dist * 0.75 - rr * 0.75,
                   cx + math.cos(a) * dist + rr, cy + math.sin(a) * dist * 0.75 + rr * 0.75], fill=255)
    src = m.copy()
    sp, mp = src.load(), m.load()
    w, h = size
    x0, x1 = max(1, int(cx - r * 1.5)), min(w - 1, int(cx + r * 1.5))
    y0, y1 = max(1, int(cy - r * 1.5)), min(h - 1, int(cy + r * 1.5))
    for y in range(y0, y1):
        for x in range(x0, x1):
            nb = (sp[x - 1, y], sp[x + 1, y], sp[x, y - 1], sp[x, y + 1])
            if sp[x, y] and min(nb) == 0 and rnd.random() < 0.5:
                mp[x, y] = 0
            elif not sp[x, y] and max(nb) and rnd.random() < 0.25:
                mp[x, y] = 255
    return m


def paint_pad(layer, spawn_mask, cx, cy, r, pal, base_idx, sun):
    """Pinta un racimo de hojas con sombreado volumétrico y motas de textura."""
    size = layer.size
    m = make_pad_mask(size, cx, cy, r)
    if spawn_mask:
        spawn_mask.paste(255, (0, 0), m)

    step = max(1, int(round(r * 0.18)))
    # Luz viene desde arriba-izquierda (hacia el sol de poniente)
    l1 = ImageChops.multiply(m, ImageChops.offset(m, -step, -step))
    l2 = ImageChops.multiply(l1, ImageChops.offset(l1, -step, -step))
    l3 = ImageChops.multiply(l2, ImageChops.offset(l2, -step, -step))

    idx0 = max(0, min(7, base_idx))
    idx1 = min(7, idx0 + 1)
    idx2 = min(7, idx0 + 2)
    idx3 = min(7, idx0 + 3)

    layer.paste(Image.new("RGBA", size, pal[idx0] + (255,)), (0, 0), m)
    layer.paste(Image.new("RGBA", size, pal[idx1] + (255,)), (0, 0), l1)
    layer.paste(Image.new("RGBA", size, pal[idx2] + (255,)), (0, 0), l2)
    if sun > 0.40:
        layer.paste(Image.new("RGBA", size, pal[idx3] + (255,)), (0, 0), l3)

    # Detalle pixel art: pequeñas motas de hoja en el racimo
    lp, mp = layer.load(), m.load()
    for _ in range(int(r * r * 0.30)):
        xx = int(cx + rnd.uniform(-r * 1.1, r * 1.1))
        yy = int(cy + rnd.uniform(-r * 0.9, r * 0.9))
        if 0 <= xx < size[0] and 0 <= yy < size[1] and mp[xx, yy]:
            tone = min(7, max(0, idx1 + rnd.choice([-1, 0, 1, 2])))
            lp[xx, yy] = pal[tone] + (255,)


def generate_tree(cx, base_y, trunk_h, crown_rx, crown_ry, trunk_w, pal_name, far_level=0.0):
    pal = PALETTES[pal_name]
    pad = 36
    w_box = int(crown_rx * 2.8 + pad * 2)
    h_box = int(trunk_h + crown_ry * 2.5 + pad * 2)
    ox = w_box // 2
    oy = h_box - pad
    fork_y = oy - trunk_h
    ccy = fork_y - crown_ry * 0.60
    big = crown_rx > 60
    depth_max = 4 if big else 3 if crown_rx > 45 else 2

    bark = Image.new("RGBA", (w_box, h_box), (0, 0, 0, 0))
    bk = ImageDraw.Draw(bark)
    strokes = []
    tips = []
    mids = []

    def inside(x, y, k=1.0):
        return ((x - ox) / (crown_rx * k)) ** 2 + ((y - ccy) / (crown_ry * k)) ** 2 <= 1.0

    def grow(x, y, ang, length, w, depth):
        ang = max(math.radians(-168), min(math.radians(-12), ang))
        bend = rnd.uniform(-0.18, 0.18)
        pts = []
        steps = max(6, int(length))
        for i in range(steps + 1):
            t = i / steps
            a = ang + bend * t
            pts.append((x + math.cos(a) * length * t, y + math.sin(a) * length * t))
        x2, y2 = pts[-1]
        strokes.append((pts, w, max(1.0, w * 0.70)))
        if depth >= depth_max or not inside(x2, y2, 1.05) or length < 7:
            tips.append((x2, y2))
            return
        if depth >= 1:
            mids.append((pts[len(pts) // 2], depth))
        n = 3 if (rnd.random() < 0.25 and depth < depth_max) else 2
        spread = rnd.uniform(0.48, 0.75)
        for k in range(n):
            off = (k - (n - 1) / 2.0) * spread + rnd.uniform(-0.12, 0.12)
            grow(x2, y2, ang + off, length * rnd.uniform(0.74, 0.88), w * 0.65, depth + 1)

    # 3 ramas principales desde el tronco
    limbs = 3 if big else 2
    for k in range(limbs):
        off = (k - (limbs - 1) / 2.0) * 0.80 + rnd.uniform(-0.08, 0.08)
        grow(ox, fork_y + 2, -math.pi / 2 + off, crown_ry * (0.58 if big else 0.70), trunk_w * 0.55, 0)

    # ---------- Capa 1: Follaje trasero profundo (tonos 1-2, carmesí y naranja óxido) ----------
    back_layer = Image.new("RGBA", (w_box, h_box), (0, 0, 0, 0))
    smask = Image.new("L", (w_box, h_box), 0)

    # Colocar racimos traseros en las ramas intermedias y el fondo
    for (mx, my), d_lv in mids:
        if d_lv <= 2 and rnd.random() < 0.7:
            r = crown_rx * rnd.uniform(0.15, 0.21)
            paint_pad(back_layer, smask, mx, my, r, pal, 1, 0.1)

    # Masa de relleno trasera superior
    for _ in range(5 if big else 3):
        a = rnd.uniform(math.radians(-165), math.radians(-15))
        d_ = rnd.uniform(0.2, 0.65)
        x = ox + math.cos(a) * crown_rx * d_
        y = ccy + math.sin(a) * crown_ry * d_ * 0.85
        paint_pad(back_layer, smask, x, y, crown_rx * rnd.uniform(0.17, 0.24), pal, 1, 0.15)

    # ---------- Capa 2: Tronco y ramas ----------
    def stamp(pts, w0, w1, col, shrink=0.0, off=0.0):
        n = len(pts)
        for i, (x, y) in enumerate(pts):
            w = lerp(w0, w1, i / max(1, n - 1))
            r = max(0.6, w / 2.0 - shrink)
            bk.ellipse([x - r + off, y - r + off, x + r + off, y + r + off], fill=col + (255,))

    # Contorno oscuro de ramas
    for pts, w0, w1 in strokes:
        stamp(pts, w0 + 1.6, w1 + 1.6, BARK["outline"], 0)
    # Cuerpo de corteza
    for pts, w0, w1 in strokes:
        stamp(pts, w0, w1, BARK["mid"], 0)
    # Luz lateral en ramas
    for pts, w0, w1 in strokes:
        if w0 >= 2.5:
            stamp(pts, w0 * 0.6, w1 * 0.6, BARK["light"], 0, -w0 * 0.15)

    # Tronco principal
    bpx = bark.load()
    for y in range(int(fork_y), oy + 1):
        t = (y - fork_y) / max(1, (oy - fork_y))
        flare = max(0.0, (t - 0.70) / 0.30) ** 2.2 * trunk_w * 0.95
        cur_w = trunk_w * (0.80 + 0.20 * t) + flare
        cxx = ox + math.sin(t * 2.4) * trunk_w * 0.05
        xl, xr = int(round(cxx - cur_w / 2)), int(round(cxx + cur_w / 2))
        for x in range(xl, xr + 1):
            ratio = (x - xl) / max(1, xr - xl)
            if x in (xl, xr):
                c = BARK["outline"]
            elif ratio < 0.18:
                c = BARK["hi"]
            elif ratio < 0.48:
                c = BARK["light"]
            elif ratio < 0.78:
                c = BARK["mid"]
            else:
                c = BARK["dark"]
            if ((x * 3) ^ (y // 3)) % 7 == 0 and x not in (xl, xr):
                c = mix(c, BARK["outline"], 0.35)
            bpx[x, y] = c + (255,)

    # Raíces nudadas
    for side in (-1, 1):
        for k, (sr, er, lift) in enumerate(((0.45, 1.15, 9), (0.28, 0.85, 5))):
            x0, y0 = ox + side * trunk_w * sr, oy - lift
            x1 = ox + side * trunk_w * er
            bk.line([x0, y0, x1, oy + 1], fill=BARK["outline"] + (255,), width=4 if k == 0 else 3)
            bk.line([x0, y0, x1, oy + 1], fill=BARK["mid"] + (255,), width=2)
            bk.line([x0 - side, y0, x1 - side, oy + 1], fill=BARK["light"] + (255,), width=1)

    # ---------- Capa 3: Follaje medio (naranjas y ámbar entre ramas) ----------
    mid_layer = Image.new("RGBA", (w_box, h_box), (0, 0, 0, 0))
    for (mx, my), d_lv in mids:
        if d_lv >= 1 and rnd.random() < 0.55:
            r = crown_rx * rnd.uniform(0.12, 0.17)
            paint_pad(mid_layer, smask, mx, my, r, pal, 2, 0.35)

    # ---------- Capa 4: Follaje frontal (racimos dorados sobre puntas y ramas) ----------
    front_layer = Image.new("RGBA", (w_box, h_box), (0, 0, 0, 0))
    pad_r = max(3.8, crown_rx * (0.13 if big else 0.18))

    tufts_front = [(x, y, pad_r * rnd.uniform(0.85, 1.25)) for x, y in tips]
    # racimos sobre ramas intermedias: rompen las lineas duras de las ramas
    for (mx, my), d_lv in mids:
        if d_lv >= 1 and rnd.random() < 0.5:
            tufts_front.append((mx + rnd.uniform(-3, 3), my - rnd.uniform(1, 4), pad_r * rnd.uniform(0.8, 1.05)))
    # corona superior
    for off_x in (-0.4, -0.15, 0.15, 0.4):
        tufts_front.append((ox + crown_rx * off_x + rnd.uniform(-5, 5),
                            ccy - crown_ry * rnd.uniform(0.45, 0.75),
                            pad_r * rnd.uniform(0.95, 1.25)))

    tufts_front.sort(key=lambda p: p[1])
    for x, y, r in tufts_front:
        h_rel = (y - (ccy - crown_ry)) / max(1.0, crown_ry * 2.0)
        x_rel = (x - (ox - crown_rx)) / max(1.0, crown_rx * 2.0)
        sun = (1.0 - h_rel * 0.6) * 0.7 + (1.0 - x_rel) * 0.3 + rnd.uniform(-0.1, 0.1)
        sun = max(0.0, min(1.0, sun))
        base = 2 if sun < 0.30 else 3 if sun < 0.65 else 4
        paint_pad(front_layer, smask, x, y, r, pal, base, sun)

    # ---------- Composición estratificada ----------
    comp = Image.new("RGBA", (w_box, h_box), (0, 0, 0, 0))
    comp.alpha_composite(back_layer)
    comp.alpha_composite(mid_layer)
    comp.alpha_composite(bark)
    comp.alpha_composite(front_layer)

    # Contorno fino de 1 píxel
    alpha = comp.split()[3]
    edge = ImageChops.subtract(alpha.filter(ImageFilter.MaxFilter(3)), alpha)
    outline = Image.new("RGBA", comp.size, pal[0] + (255,))
    outline.putalpha(edge.point(lambda v: 255 if v > 40 else 0))
    final = Image.new("RGBA", comp.size, (0, 0, 0, 0))
    final.alpha_composite(outline)
    final.alpha_composite(comp)

    # Bruma atmosférica si está lejos
    if far_level > 0.0:
        fp = final.load()
        haze_c = mix(HAZE, (160, 110, 130), 0.3)
        for yy in range(h_box):
            for xx in range(w_box):
                p = fp[xx, yy]
                if p[3] > 0:
                    fp[xx, yy] = mix(p[:3], haze_c, far_level * 0.55) + (p[3],)

    img_x, img_y = int(cx - ox), int(base_y - oy)
    img.paste(final, (img_x, img_y), final)

    # Puntos de spawn para hojas que caen: dentro de copas reales
    mp = smask.load()
    cand = [(img_x + xx, img_y + yy) for yy in range(0, h_box, 2) for xx in range(0, w_box, 2)
            if mp[xx, yy] > 0 and yy > ccy - crown_ry * 0.3]
    rnd.shuffle(cand)
    trees_info.append({
        "x": round(cx), "y": round(img_y + ccy), "rx": round(crown_rx), "ry": round(crown_ry),
        "base": round(base_y),
        "pts": [[px, py] for px, py in cand[:140]],
        "pal": ["#%02x%02x%02x" % pal[i] for i in (3, 4, 5, 6)],
    })


# ==========================================
# 7. COMPOSICIÓN DE ÁRBOLES
# ==========================================
tree_specs = [
    # (cx, base_y, trunk_h, rx, ry, trunk_w, paleta, bruma)
    (210, 212, 22, 26, 20, 5, "orange", 0.70),
    (385, 214, 24, 30, 22, 6, "amber", 0.60),
    (42,  218, 30, 38, 28, 8, "crimson", 0.40),
    (125, 224, 38, 50, 38, 10, "orange", 0.20),
    (440, 228, 44, 56, 42, 12, "crimson", 0.15),
    (295, 244, 56, 84, 66, 18, "gold", 0.0),
]
for spec in tree_specs:
    generate_tree(*spec)
# ==========================================
# 8. PASTO DE PRIMER PLANO Y HOJAS CAÍDAS
# ==========================================
blade_colors = [
    hexc("#a49e3c"),
    hexc("#8e8a34"),
    hexc("#7b782c"),
    hexc("#b8b248"),
    hexc("#545020")
]

for _ in range(3200):
    bx = rnd.randint(0, W - 1)
    by = rnd.randint(GR_TOP + 4, H - 1)
    rel_depth = (by - GR_TOP) / (H - GR_TOP)
    hgt = 1 + int(rel_depth * 4.5) + rnd.randint(0, 1)
    col = rnd.choice(blade_colors)
    lean = rnd.choice([-1, 0, 0, 1])
    for step in range(hgt):
        lx = bx + (lean if step >= hgt // 2 else 0)
        ly = by - step
        if 0 <= lx < W and 0 <= ly < H:
            px[lx, ly] = col if step < hgt - 1 else mix(col, (245, 225, 130), 0.4)

for bx in range(0, W, 4):
    if rnd.random() < 0.75:
        hgt = rnd.randint(6, 13)
        col = rnd.choice([hexc("#3a3818"), hexc("#45431d"), hexc("#525022")])
        lean = rnd.choice([-1, 0, 1])
        for step in range(hgt):
            lx = bx + int(lean * step / 3)
            ly = H - 1 - step
            if 0 <= lx < W and 0 <= ly < H:
                px[lx, ly] = col if step < hgt - 2 else hexc("#8c8838")

ground_leaf_colors = [
    hexc("#f8be22"),
    hexc("#ea8416"),
    hexc("#c65214"),
    hexc("#882614"),
    hexc("#fde460")
]

for _ in range(320):
    lx = rnd.randint(2, W - 3)
    ly = rnd.randint(GR_TOP + 12, H - 3)
    c = rnd.choice(ground_leaf_colors)
    sh = mix(c, (40, 15, 10), 0.5)
    pat = rnd.choice([0, 1, 2])
    if pat == 0:
        px[lx, ly] = c; px[lx + 1, ly] = c; px[lx, ly + 1] = sh
    elif pat == 1:
        px[lx, ly] = c; px[lx, ly + 1] = c; px[lx + 1, ly + 1] = sh
    else:
        px[lx, ly] = c; px[lx + 1, ly] = c

for _ in range(250):
    lx = int(rnd.gauss(295, 40))
    ly = int(rnd.gauss(246, 7))
    if 0 <= lx < W - 1 and GR_TOP < ly < H - 1:
        c = rnd.choice(ground_leaf_colors)
        px[lx, ly] = c
        if rnd.random() < 0.6:
            px[lx + 1, ly] = c

for _ in range(120):
    lx = int(rnd.gauss(125, 24))
    ly = int(rnd.gauss(228, 5))
    if 0 <= lx < W - 1 and GR_TOP < ly < H - 1:
        c = rnd.choice(ground_leaf_colors)
        px[lx, ly] = c

mushrooms = [(190, 248), (360, 256), (80, 238)]
for mx, my in mushrooms:
    px[mx, my] = hexc("#e8dec4")
    px[mx, my - 1] = hexc("#e8dec4")
    px[mx - 1, my - 2] = hexc("#b82418")
    px[mx, my - 2] = hexc("#d83824")
    px[mx + 1, my - 2] = hexc("#b82418")
    px[mx, my - 3] = hexc("#d83824")
    px[mx, my - 3] = hexc("#fffcee")

scene_path = os.path.join(HERE, "scene.png")
img.save(scene_path)

info = {
    "scene": [W, H],
    "groundY": GROUND_Y,
    "groundMax": GROUND_MAX,
    "trees": trees_info
}
with open(os.path.join(HERE, "trees.json"), "w") as f:
    json.dump(info, f, separators=(",", ":"))

print(f"Scene generated: {len(trees_info)} trees -> {scene_path}")
