"""Gera os quadros do vídeo do hero com as fotos da pizza: ela é montada e assada conforme o scroll.

Linha do tempo (p = 0..1), uma etapa por manchete do hero:
  0.00-0.20 massa pousa na tábua | 0.20-0.40 molho espalha e queijo derrete
  0.40-0.60 coberturas caem      | 0.60-0.80 forno: brilho quente e brasas
  0.80-1.00 mesa: o calor baixa e a pizza fica pronta

Usa as imagens de static/imagens/pizza/ (scripts/preparar_ingredientes.py) e também grava
static/imagens/pizza/vitrine.webp, a pizza pronta sem fundo, usada no cardápio e no login.

Ferramenta avulsa (não é dependência do app). Uso:
  python -m venv /tmp/videoenv && /tmp/videoenv/bin/pip install pillow numpy
  /tmp/videoenv/bin/python scripts/gerar_video_hero.py /tmp/quadros            # horizontal
  /tmp/videoenv/bin/python scripts/gerar_video_hero.py /tmp/vertical 720 1280  # celular em pé
  ffmpeg -y -framerate 30 -i /tmp/quadros/q%04d.png -vf scale=1600:900:flags=lanczos -c:v libx264 \
      -preset slow -crf 30 -g 6 -pix_fmt yuv420p -movflags +faststart -an static/videos/forno.mp4
  ffmpeg -y -i /tmp/quadros/q0239.png -vf scale=1600:900 -q:v 4 static/videos/forno-poster.jpg
  ffmpeg -y -framerate 30 -i /tmp/vertical/q%04d.png -c:v libx264 -preset slow -crf 30 -g 6 \
      -pix_fmt yuv420p -movflags +faststart -an static/videos/forno-vertical.mp4

Foto é mais pesada que desenho: em 1920 o vídeo passa de 6 MB; em 1600x900 com crf 30 fica perto de 4 MB.
"""
import math
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

RAIZ = Path(__file__).resolve().parent.parent
FOTOS = RAIZ / 'static' / 'imagens' / 'pizza'

# Horizontal (padrão) para telas deitadas; passe 720 1280 para a versão em pé do celular.
W, H = (int(sys.argv[2]), int(sys.argv[3])) if len(sys.argv) > 3 else (1920, 1080)
FPS, SEG = 30, 8
N = FPS * SEG
CX, CY = W // 2, int(H * (0.45 if W > H else 0.40))  # em pé, sobe para dar lugar à manchete
D = int(min(W, H) * 0.72)  # diâmetro da pizza; em pé, o celular ainda corta ~18% da largura
CELULA = 160

saida = Path(sys.argv[1])
saida.mkdir(parents=True, exist_ok=True)
rnd = random.Random(7)


def ease(t):
    t = min(1, max(0, t))
    return 1 - (1 - t) ** 3


def fase(p, a, b):
    return ease((p - a) / (b - a))


def foto(nome, lado):
    return Image.open(FOTOS / f'{nome}.webp').convert('RGBA').resize((lado, lado), Image.LANCZOS)


# ---------- Fundo fixo: a bancada desfocada e, por cima, a tábua do tamanho da pizza ----------

bancada = Image.open(FOTOS / 'fundo.webp').convert('RGB')
fundo = bancada.resize((W, W), Image.LANCZOS).crop((0, (W - H) // 2, W, (W + H) // 2))
fundo = ImageEnhance.Brightness(fundo.filter(ImageFilter.GaussianBlur(22))).enhance(0.42).convert('RGBA')
LADO_TABUA = int(D * 1.16 / 0.79)  # na foto a tábua ocupa 79% da largura
tabua = bancada.resize((LADO_TABUA, LADO_TABUA), Image.LANCZOS).convert('RGBA')
yy, xx = np.mgrid[0:LADO_TABUA, 0:LADO_TABUA]
r = np.hypot(xx - LADO_TABUA / 2, yy - LADO_TABUA / 2) / (LADO_TABUA / 2)
tabua.putalpha(Image.fromarray((np.clip((1 - r) / 0.24, 0, 1) * 255).astype(np.uint8)))
fundo.alpha_composite(tabua, (int(CX - LADO_TABUA * 0.482), int(CY - LADO_TABUA * 0.467)))

# Brilho do forno (somado ao fundo na etapa do forno)
yy, xx = np.mgrid[0:H, 0:W]
calor = np.clip(1.15 - np.hypot((xx - CX) / W, (yy - H * 1.1) / H) * 1.5, 0, 1)[..., None] * np.array([170, 70, 24], np.float32)

# ---------- Camadas da pizza ----------

massa = foto('massa', D)
molho = foto('molho', int(D * 0.84))
queijo = foto('queijo', int(D * 0.80))

# Sombra da pizza na tábua, deslocada para baixo e à direita como a luz das fotos.
sombra = Image.new('L', (int(D * 1.2), int(D * 1.2)), 0)
ImageDraw.Draw(sombra).ellipse([D * 0.1, D * 0.1, D * 1.1, D * 1.1], fill=150)
sombra = sombra.filter(ImageFilter.GaussianBlur(D * 0.035))

# Coberturas da "pizza da casa": calabresa, cebola, azeitona e manjericão por cima.
COBERTURAS = [('calabresa', 0.1, 15), ('cebola', 0.085, 8), ('azeitona', 0.058, 10), ('manjericao', 0.075, 7)]
tiras = {nome: Image.open(FOTOS / f'{nome}.webp').convert('RGBA') for nome, _, _ in COBERTURAS}
pecas = []
ocupados = []
for nome, tam, qtd in COBERTURAS:
    feitos = tentativas = 0
    while feitos < qtd and tentativas < 3000:
        tentativas += 1
        raio = math.sqrt(0.004 + rnd.random() * 0.996) * 0.35
        ang = rnd.uniform(0, math.tau)
        x, y = 0.5 + math.cos(ang) * raio, 0.5 + math.sin(ang) * raio
        dist = tam * (0.55 if nome == 'manjericao' else 0.82)
        if nome != 'manjericao' and any(math.hypot(x - ox, y - oy) < (dist + od) * 0.5 for ox, oy, od in ocupados):
            continue
        if nome != 'manjericao':
            ocupados.append((x, y, dist))
        lado = int(D * tam / 0.84 * rnd.uniform(0.9, 1.1))
        k = rnd.randrange(4)
        celula = tiras[nome].crop((k * CELULA, 0, (k + 1) * CELULA, CELULA)).resize((lado, lado), Image.LANCZOS)
        pecas.append({'nome': nome, 'img': celula, 'x': x, 'y': y, 'giro': rnd.uniform(0, 360)})
        feitos += 1
# ordem de queda espalhada pela pizza (não por ingrediente), com as folhas por último
folhas = [p for p in pecas if p['nome'] == 'manjericao']
base = [p for p in pecas if p['nome'] != 'manjericao']
rnd.shuffle(base)
pecas = base + folhas
for i, p in enumerate(pecas):
    p['inicio'] = 0.4 + 0.15 * i / len(pecas)


def colar(tela, img, cx, cy, alfa=1.0):
    if alfa < 1:
        img = img.copy()
        img.putalpha(img.getchannel('A').point(lambda v: int(v * alfa)))
    tela.alpha_composite(img, (int(cx - img.width / 2), int(cy - img.height / 2)))


def pizza_no_ponto(p):
    """A pizza (sem fundo) no instante p, num quadro do tamanho da massa."""
    tela = Image.new('RGBA', (D, D), (0, 0, 0, 0))
    tela.alpha_composite(massa)

    mo = fase(p, 0.2, 0.33)
    if mo > 0:
        camada = molho.rotate(-120 * (1 - mo), resample=Image.BICUBIC)
        mascara = Image.new('L', camada.size, 0)
        rr = camada.width / 2 * 1.45 * mo
        ImageDraw.Draw(mascara).ellipse([camada.width / 2 - rr, camada.height / 2 - rr, camada.width / 2 + rr, camada.height / 2 + rr], fill=255)
        alfa = Image.fromarray(np.minimum(np.asarray(camada.getchannel('A')), np.asarray(mascara)))
        camada.putalpha(alfa)
        colar(tela, camada, D / 2, D / 2)

    qu = fase(p, 0.3, 0.42)
    if qu > 0:
        camada = queijo
        escala = 0.92 + 0.08 * qu
        if escala < 1:
            lado = int(camada.width * escala)
            camada = camada.resize((lado, lado), Image.LANCZOS)
        if qu < 1:
            camada = camada.filter(ImageFilter.GaussianBlur(7 * (1 - qu)))
        colar(tela, camada, D / 2, D / 2, qu)

    for peca in pecas:
        t = ease((p - peca['inicio']) / 0.035)
        if t <= 0:
            continue
        img = peca['img']
        escala = 1 + 0.5 * (1 - t)
        if escala != 1:
            lado = int(img.width * escala)
            img = img.resize((lado, lado), Image.BILINEAR)
        img = img.rotate(peca['giro'] + 40 * (1 - t), resample=Image.BICUBIC)
        colar(tela, img, peca['x'] * D, peca['y'] * D - D * 0.05 * (1 - t), t)
    return tela


def quadro(i):
    p = i / (N - 1)
    assa = fase(p, 0.6, 0.8)  # quanto a pizza já assou (fica)
    calor_agora = assa * (1 - fase(p, 0.82, 0.97))  # brilho do forno (vai e volta)

    img = fundo.copy()
    if calor_agora > 0:
        arr = np.asarray(img.convert('RGB')).astype(np.float32) + calor * calor_agora * (0.9 + 0.1 * math.sin(i * 0.9))
        img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert('RGBA')

    m = 0.35 + 0.65 * fase(p, 0.0, 0.14)  # a massa já está na tábua no primeiro quadro e se assenta
    if m > 0:
        pizza = pizza_no_ponto(p)
        if assa > 0:  # assar: mais contraste e cor, o queijo doura
            rgb = ImageEnhance.Color(ImageEnhance.Contrast(pizza.convert('RGB')).enhance(1 + 0.12 * assa)).enhance(1 + 0.15 * assa)
            rgb = ImageEnhance.Brightness(rgb).enhance(1 - 0.06 * assa)
            rgb.putalpha(pizza.getchannel('A'))
            pizza = rgb
        zoom = (1.1 - 0.1 * m) * (1 + 0.035 * fase(p, 0.82, 1.0))
        lado = int(D * zoom)
        if lado != D:
            pizza = pizza.resize((lado, lado), Image.LANCZOS)
        som = sombra.resize((int(sombra.width * zoom), int(sombra.height * zoom)))
        camada_sombra = Image.new('RGBA', som.size, (20, 10, 4, 0))
        camada_sombra.putalpha(som)
        colar(img, camada_sombra, CX + D * 0.025, CY + D * 0.04 - D * 0.06 * (1 - m))
        colar(img, pizza, CX, CY - D * 0.06 * (1 - m))

    # brasas subindo: poucas sempre, muitas no forno
    d = ImageDraw.Draw(img, 'RGBA')
    intensidade = 0.2 + 0.8 * calor_agora
    for b in BRASAS:
        ciclo = (p * b['v'] * 3 + b['fase']) % 1
        y = H * (1.02 - ciclo * 1.1)
        x = b['x'] + math.sin(ciclo * 9 + b['fase'] * 6) * b['osc']
        alfa = int(255 * intensidade * math.sin(math.pi * ciclo))
        d.ellipse([x - b['r'] * 2.4, y - b['r'] * 2.4, x + b['r'] * 2.4, y + b['r'] * 2.4], fill=(240, 120, 40, alfa // 5))
        d.ellipse([x - b['r'], y - b['r'], x + b['r'], y + b['r']], fill=(255, 196, 90, alfa))

    img.convert('RGB').save(saida / f'q{i:04d}.png')


BRASAS = [
    {'x': rnd.uniform(0.1, 0.9) * W, 'v': rnd.uniform(0.35, 0.9), 'fase': rnd.random(), 'r': rnd.uniform(1.5, 3.8), 'osc': rnd.uniform(8, 30)}
    for _ in range(60)
]

for i in range(N):
    quadro(i)

vitrine = pizza_no_ponto(1.0)
vitrine.resize((720, 720), Image.LANCZOS).save(FOTOS / 'vitrine.webp', 'WEBP', quality=80, method=6)
print(f'{N} quadros em {saida}; vitrine em {FOTOS / "vitrine.webp"}')
