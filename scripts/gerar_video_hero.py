"""Gera os quadros do vídeo do hero: a pizza é montada e assada conforme o scroll.

Linha do tempo (p = 0..1):
  0.00-0.15 massa surge | 0.15-0.35 molho espalha | 0.35-0.55 queijo
  0.55-0.75 coberturas  | 0.75-1.00 forno: queijo doura, borda tosta, brasa sobe

Ferramenta avulsa (não é dependência do app). Uso:
  python -m venv /tmp/videoenv && /tmp/videoenv/bin/pip install pillow numpy
  /tmp/videoenv/bin/python scripts/gerar_video_hero.py /tmp/quadros
  ffmpeg -y -framerate 30 -i /tmp/quadros/q%04d.png -c:v libx264 -preset slow -crf 29 -g 6 \
      -pix_fmt yuv420p -movflags +faststart -an static/videos/forno.mp4
  ffmpeg -y -i static/videos/forno.mp4 -frames:v 1 -q:v 3 static/videos/forno-poster.jpg
"""
import math
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W, H = 1920, 1080
SS = 2  # supersampling para bordas suaves
FPS, SEG = 30, 8
N = FPS * SEG
CX, CY = W // 2, int(H * 0.54)
R = int(H * 0.36)

saida = Path(sys.argv[1])
saida.mkdir(parents=True, exist_ok=True)

rnd = random.Random(7)


def ease(t):
    t = min(1, max(0, t))
    return 1 - (1 - t) ** 3


def fase(p, a, b):
    return ease((p - a) / (b - a))


def mistura(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


# Fundo: tijolo escuro de forno com brilho quente embaixo
yy, xx = np.mgrid[0:H, 0:W]
dist = np.sqrt(((xx - CX) / W) ** 2 + ((yy - H * 1.05) / H) ** 2)
fundo_base = np.zeros((H, W, 3), np.float32)
fundo_base[:] = (20, 17, 16)
tijolo = np.zeros((H, W), np.float32)
alt_t, larg_t = 54, 132
for linha in range(H // alt_t + 1):
    desloc = (larg_t // 2) * (linha % 2)
    y0 = linha * alt_t
    tijolo[y0:y0 + 3, :] = 1
    for x in range(-desloc, W, larg_t):
        tijolo[y0:y0 + alt_t, max(0, x):max(0, x) + 3] = 1
ruido = np.random.default_rng(3).normal(0, 3.5, (H, W, 1)).astype(np.float32)

brasas = [
    {"x": rnd.uniform(0.15, 0.85) * W, "v": rnd.uniform(0.35, 0.9), "fase": rnd.random(),
     "r": rnd.uniform(1.5, 4.2), "osc": rnd.uniform(8, 30)}
    for _ in range(70)
]

# Posições fixas dos ingredientes
queijo = []
for _ in range(34):
    a, d = rnd.uniform(0, math.tau), math.sqrt(rnd.random()) * R * 0.72
    queijo.append((CX + math.cos(a) * d, CY + math.sin(a) * d * 0.96, rnd.uniform(0.11, 0.2) * R, rnd.random()))

coberturas = []
tentativas = 0
while len(coberturas) < 11 and tentativas < 2000:
    tentativas += 1
    a, d = rnd.uniform(0, math.tau), math.sqrt(rnd.random()) * R * 0.66
    x, y = CX + math.cos(a) * d, CY + math.sin(a) * d
    if all(math.hypot(x - c[0], y - c[1]) > R * 0.27 for c in coberturas):
        coberturas.append((x, y, rnd.random()))
folhas = []
for _ in range(7):
    a, d = rnd.uniform(0, math.tau), math.sqrt(rnd.random()) * R * 0.6
    folhas.append((CX + math.cos(a) * d, CY + math.sin(a) * d, rnd.uniform(0, 180), rnd.random()))


def quadro(i):
    p = i / (N - 1)
    forno = fase(p, 0.72, 1.0)

    # fundo
    brilho = np.clip(1.25 - dist * 1.6, 0, 1)[..., None] * (0.35 + 0.65 * forno)
    fundo = fundo_base + tijolo[..., None] * np.array([10, 7, 6], np.float32)
    fundo += brilho * np.array([150, 62, 22], np.float32) * (0.9 + 0.1 * math.sin(i * 0.9))
    fundo += ruido
    img = Image.fromarray(np.clip(fundo, 0, 255).astype(np.uint8)).resize((W * SS, H * SS))
    d = ImageDraw.Draw(img, "RGBA")
    s = SS

    def elipse(x, y, rx, ry, cor):
        d.ellipse([(x - rx) * s, (y - ry) * s, (x + rx) * s, (y + ry) * s], fill=cor)

    # massa
    m = fase(p, 0.0, 0.15)
    if m > 0:
        rr = R * (0.55 + 0.45 * m)
        elipse(CX, CY + R * 0.06, rr * 1.04, rr * 0.99, (0, 0, 0, int(110 * m)))  # sombra
        borda = mistura((226, 196, 150), (176, 104, 42), forno)
        elipse(CX, CY, rr, rr, borda + (int(255 * m),))
        miolo = mistura((240, 218, 178), (214, 160, 92), forno)
        elipse(CX, CY, rr * 0.88, rr * 0.88, miolo + (int(255 * m),))
        # marcas de tostado na borda
        if forno > 0:
            for k in range(26):
                a = k / 26 * math.tau + 0.3
                elipse(CX + math.cos(a) * rr * 0.94, CY + math.sin(a) * rr * 0.94,
                       rr * 0.035, rr * 0.03, (70, 34, 14, int(170 * forno * (0.5 + (k % 3) / 4))))

    # molho
    mo = fase(p, 0.15, 0.35)
    if mo > 0:
        elipse(CX, CY, R * 0.84 * mo, R * 0.84 * mo, mistura((201, 52, 34), (160, 38, 22), forno) + (255,))

    # queijo
    q = fase(p, 0.35, 0.55)
    for (x, y, r, atraso) in queijo:
        t = fase(q, atraso * 0.6, atraso * 0.6 + 0.4)
        if t > 0:
            cor = mistura((250, 236, 200), (238, 184, 70), forno)
            elipse(x, y, r * t, r * t * 0.92, cor + (235,))
            if forno > 0.3:
                elipse(x + r * 0.2, y - r * 0.15, r * 0.25 * t, r * 0.2 * t, (180, 102, 30, int(120 * forno)))

    # coberturas: rodelas de calabresa e manjericão
    c = fase(p, 0.55, 0.75)
    for (x, y, atraso) in coberturas:
        t = fase(c, atraso * 0.55, atraso * 0.55 + 0.45)
        if t > 0:
            rr = R * 0.105 * (0.4 + 0.6 * t) * (1 + 0.25 * (1 - t))
            elipse(x, y + 3, rr, rr, (60, 16, 10, int(140 * t)))
            elipse(x, y, rr, rr, mistura((178, 44, 36), (138, 30, 22), forno) + (int(255 * t),))
            elipse(x - rr * 0.25, y - rr * 0.25, rr * 0.35, rr * 0.3, (230, 120, 100, int(110 * t)))
    for (x, y, ang, atraso) in folhas:
        t = fase(c, 0.3 + atraso * 0.5, 0.5 + atraso * 0.5)
        if t > 0:
            folha = Image.new("RGBA", (int(R * 0.2 * s), int(R * 0.1 * s)), (0, 0, 0, 0))
            ImageDraw.Draw(folha).ellipse([0, 0, folha.width - 1, folha.height - 1],
                                          fill=mistura((49, 91, 55), (38, 70, 40), forno) + (int(255 * t),))
            folha = folha.rotate(ang, expand=True)
            img.paste(folha, (int(x * s - folha.width / 2), int(y * s - folha.height / 2)), folha)

    # brasas subindo (sempre um pouco, bem mais no forno)
    intensidade = 0.25 + 0.75 * forno
    for b in brasas:
        ciclo = (p * b["v"] * 3 + b["fase"]) % 1
        y = H * (1.02 - ciclo * 1.1)
        x = b["x"] + math.sin(ciclo * 9 + b["fase"] * 6) * b["osc"]
        alfa = int(255 * intensidade * math.sin(math.pi * ciclo))
        elipse(x, y, b["r"] * 2.4, b["r"] * 2.4, (240, 120, 40, alfa // 5))
        elipse(x, y, b["r"], b["r"], (255, 196, 90, alfa))

    img = img.resize((W, H), Image.LANCZOS)
    if forno > 0:  # calor tremulando
        brilho_img = img.filter(ImageFilter.GaussianBlur(18))
        img = Image.blend(img, brilho_img, 0.12 * forno)
    img.convert("RGB").save(saida / f"q{i:04d}.png")


for i in range(N):
    quadro(i)
print(f"{N} quadros em {saida}")
