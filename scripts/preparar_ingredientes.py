"""Prepara as imagens da tela "Monte sua pizza" a partir das fotos geradas por IA.

As fotos originais (PNG, fundo liso) ficam fora do repositório. Este script tira o fundo,
separa cada peça das folhas de ingredientes e grava em static/imagens/pizza/:

  - camadas (massa, molho, queijo, chocolate): um disco recortado, quadrado, em WebP;
  - ingredientes: uma tira com 4 variações por ingrediente (célula de 160 px, sombra já
    aplicada), para a página baixar um arquivo só por ingrediente;
  - fundo.webp: a tábua sobre a bancada, sem recorte.

Ferramenta avulsa (não é dependência do app). Uso:
  python -m venv /tmp/imgenv && /tmp/imgenv/bin/pip install pillow numpy scipy
  /tmp/imgenv/bin/python -I scripts/preparar_ingredientes.py <pasta-das-originais>
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / 'static' / 'imagens' / 'pizza'
CELULA = 160
VARIACOES = 4

# Cor de fundo pedida na geração: branco para quase tudo, azul ou magenta para o que é claro.
FUNDOS = {'branco': (255, 255, 255), 'azul': (40, 90, 220), 'magenta': (230, 30, 220)}

# Folhas: arquivo original -> fundo e, por fileira (de cima para baixo), o ingrediente.
FOLHAS = {
    'calabresa': ('branco', ['calabresa']),
    'folha-pepperoni-azeitona-cogumelo': ('branco', ['pepperoni', 'azeitona', 'cogumelo']),
    'folha-tomate-manjericao-pimentao': ('branco', ['tomate', 'manjericao', 'pimentao']),
    'folha-presunto-frango-carnesol': ('branco', ['presunto', 'frango', 'carnesol']),
    'folha-bacon-cebolacar-pequi': ('branco', ['bacon', 'cebolacar', 'pequi']),
    'folha-oregano-milho-brocolis': ('branco', ['oregano', 'milho', 'brocolis']),
    'folha-rucula-morango-granulado': ('branco', ['rucula', 'morango', 'granulado']),
    'folha-cheddar-chocolate-ervilha': ('branco', ['borda-cheddar', 'borda-chocolate', 'ervilha']),
    'folha-catupiry-parmesao-provolone': ('azul', ['catupiry', 'parmesao', 'provolone']),
    'folha-cebola-ovo-palmito': ('azul', ['cebola', 'ovo', 'palmito']),
    'folha-coalho-banana-cebolaroxa': ('azul', ['coalho', 'banana', 'cebolaroxa']),
    'folha-gorgonzola-atum-mussarela': ('magenta', ['gorgonzola', 'atum', 'mussarela']),
}

# Camadas: arquivo original -> (fundo, nome de saída, lado em px)
CAMADAS = {
    'massa': ('branco', 'massa', 880),
    'molho': ('branco', 'molho', 740),
    'queijo': ('azul', 'queijo', 740),
    'chocolate': ('branco', 'chocolate', 740),
}

# Montinhos feitos de pedacinhos soltos (orégano, milho, desfiados): junta o que está a
# poucos pixels de distância antes de separar as peças.
JUNTAR_PX = 12


def ler(caminho):
    return np.asarray(Image.open(caminho).convert('RGB')).astype(np.float32)


def cor_do_fundo(img):
    borda = np.concatenate([img[:6].reshape(-1, 3), img[-6:].reshape(-1, 3), img[:, :6].reshape(-1, 3), img[:, -6:].reshape(-1, 3)])
    return np.median(borda, axis=0)


def alfa_por_cor(img, fundo_nome):
    """Transparência: o fundo é o que, a partir da borda da imagem, tem a cor do fundo
    (no branco, também o cinza claro e neutro das sombras). Furos grandes com a cor do
    fundo, como o miolo de uma rodela de cebola, também viram fundo."""
    r, g, b = img[..., 0], img[..., 1], img[..., 2]
    if fundo_nome == 'branco':
        croma = img.max(axis=2) - img.min(axis=2)
        candidato = (croma < 28) & (img.mean(axis=2) > 150)
    elif fundo_nome == 'azul':
        candidato = (b - np.maximum(r, g)) > 35
    else:  # magenta
        candidato = (np.minimum(r, b) - g) > 50
    rotulos, _ = ndimage.label(candidato)
    na_borda = np.unique(np.concatenate([rotulos[0], rotulos[-1], rotulos[:, 0], rotulos[:, -1]]))
    areas = ndimage.sum(np.ones_like(rotulos), rotulos, index=np.arange(rotulos.max() + 1))
    # No branco, brilho forte (azeitona) também é claro e neutro: só furo bem grande vira fundo.
    # Azul e magenta não existem na comida, então ali qualquer furo é fundo.
    furo_minimo = img.shape[0] * img.shape[1] * 0.004 if fundo_nome == 'branco' else 4
    eh_fundo = np.isin(np.arange(len(areas)), na_borda) | (areas > furo_minimo)
    eh_fundo[0] = False
    objeto = ~eh_fundo[rotulos]
    objeto = ndimage.binary_opening(objeto, iterations=1)
    objeto = ndimage.binary_erosion(objeto, iterations=2 if fundo_nome == "branco" else 1)
    return ndimage.gaussian_filter(objeto.astype(np.float32), 0.8)


def descontaminar(img, alfa, fundo, fundo_nome='branco'):
    """Tira o halo da cor do fundo dos pixels semitransparentes e o reflexo azul das bordas."""
    if fundo_nome == 'azul':
        img = img.copy()
        img[..., 2] = np.minimum(img[..., 2], np.maximum(img[..., 0], img[..., 1]) + 10)
    elif fundo_nome == 'magenta':
        img = img.copy()
        teto = img[..., 1] + 40
        img[..., 0] = np.where(img[..., 2] > teto, np.minimum(img[..., 0], np.maximum(teto, img[..., 1] * 1.15 + 20)), img[..., 0])
        img[..., 2] = np.minimum(img[..., 2], np.maximum(img[..., 0], img[..., 1]) + 10)
    a = alfa[..., None]
    seguro = np.maximum(a, 0.3)
    cor = (img - (1 - a) * fundo) / seguro
    cor = np.where(a > 0.98, img, cor)
    return np.clip(cor, 0, 255)


def rgba(img, alfa):
    return Image.fromarray(np.dstack([img, alfa * 255]).astype(np.uint8), 'RGBA')


def pecas(img, alfa, area_min):
    cheio = alfa > 0.5
    rotulos, n = ndimage.label(ndimage.binary_dilation(cheio, iterations=JUNTAR_PX))
    rotulos = rotulos * cheio
    achadas = []
    for i, fatia in enumerate(ndimage.find_objects(rotulos), start=1):
        if fatia is None:
            continue
        mascara = rotulos[fatia] == i
        if mascara.sum() < area_min:
            continue
        ys, xs = fatia
        cy = (ys.start + ys.stop) / 2
        cx = (xs.start + xs.stop) / 2
        achadas.append({'fatia': fatia, 'mascara': mascara, 'cx': cx, 'cy': cy, 'area': int(mascara.sum()), 'id': i, 'rotulos': rotulos})
    return achadas


def fileiras(achadas, n):
    """Agrupa as peças em n fileiras pelos maiores saltos de altura."""
    if n == 1:
        return [sorted(achadas, key=lambda p: (p['cy'], p['cx']))]
    ordem = sorted(achadas, key=lambda p: p['cy'])
    saltos = sorted(range(1, len(ordem)), key=lambda i: ordem[i]['cy'] - ordem[i - 1]['cy'], reverse=True)[: n - 1]
    cortes = [0] + sorted(saltos) + [len(ordem)]
    return [sorted(ordem[a:b], key=lambda p: p['cx']) for a, b in zip(cortes, cortes[1:])]


def sombra(peca):
    """Sombra suave deslocada para baixo e à direita, como a luz das fotos (de cima, à esquerda)."""
    a = peca.getchannel('A')
    desloc = max(2, peca.width // 60)
    tela = Image.new('L', peca.size, 0)
    tela.paste(a, (desloc, desloc * 2))
    tela = tela.filter(ImageFilter.GaussianBlur(desloc * 1.6)).point(lambda v: int(v * 0.42))
    base = Image.new('RGBA', peca.size, (40, 20, 10, 0))
    base.putalpha(tela)
    return Image.alpha_composite(base, peca)


def celula(img, alfa, peca):
    ys, xs = peca['fatia']
    pad = 4
    y0, y1 = max(0, ys.start - pad), min(img.shape[0], ys.stop + pad)
    x0, x1 = max(0, xs.start - pad), min(img.shape[1], xs.stop + pad)
    so_ela = np.zeros_like(alfa[y0:y1, x0:x1])
    dentro = ndimage.binary_dilation(peca['rotulos'][y0:y1, x0:x1] == peca['id'], iterations=3)
    so_ela[dentro] = alfa[y0:y1, x0:x1][dentro]
    recorte = rgba(img[y0:y1, x0:x1], so_ela)
    lado = int(CELULA * 0.84)
    escala = lado / max(recorte.size)
    recorte = recorte.resize((max(1, round(recorte.width * escala)), max(1, round(recorte.height * escala))), Image.LANCZOS)
    quadro = Image.new('RGBA', (CELULA, CELULA), (0, 0, 0, 0))
    quadro.paste(recorte, ((CELULA - recorte.width) // 2, (CELULA - recorte.height) // 2))
    return sombra(quadro)


def preparar_folha(origem, fundo_nome, nomes, relatorio):
    img = ler(origem)
    fundo = np.array(FUNDOS[fundo_nome], dtype=np.float32) if fundo_nome != 'branco' else cor_do_fundo(img)
    alfa = alfa_por_cor(img, fundo_nome)
    limpa = descontaminar(img, alfa, fundo, fundo_nome)
    achadas = pecas(limpa, alfa, area_min=img.shape[0] * img.shape[1] * 0.0015)
    grupos = fileiras(achadas, len(nomes))
    for nome, grupo in zip(nomes, grupos):
        # As maiores primeiro: peças cortadas pela metade ou fundidas costumam ser as estranhas.
        mediana = np.median([p['area'] for p in grupo]) if grupo else 0
        boas = [p for p in grupo if 0.55 * mediana <= p['area'] <= 1.6 * mediana] or grupo
        escolhidas = (boas * VARIACOES)[:VARIACOES]
        tira = Image.new('RGBA', (CELULA * VARIACOES, CELULA), (0, 0, 0, 0))
        for i, p in enumerate(escolhidas):
            tira.paste(celula(limpa, alfa, p), (i * CELULA, 0))
        tira.save(SAIDA / f'{nome}.webp', 'WEBP', quality=82, method=6)
        relatorio[nome] = {'pecas_na_fileira': len(grupo), 'usadas': len(set(id(p) for p in escolhidas))}


def preparar_camada(origem, fundo_nome, nome, lado, relatorio):
    img = ler(origem)
    fundo = np.array(FUNDOS[fundo_nome], dtype=np.float32) if fundo_nome != 'branco' else cor_do_fundo(img)
    alfa = alfa_por_cor(img, fundo_nome)
    limpa = descontaminar(img, alfa, fundo, fundo_nome)
    achadas = sorted(pecas(limpa, alfa, area_min=500), key=lambda p: p['area'], reverse=True)
    principal = achadas[0]
    ys, xs = principal['fatia']
    # Recorte quadrado centrado no disco, para as camadas se alinharem pelo centro.
    cy, cx = (ys.start + ys.stop) / 2, (xs.start + xs.stop) / 2
    meio = max(ys.stop - ys.start, xs.stop - xs.start) / 2 + 2
    y0, y1, x0, x1 = int(cy - meio), int(cy + meio), int(cx - meio), int(cx + meio)
    tela = np.zeros((y1 - y0, x1 - x0, 4), dtype=np.float32)
    sy0, sx0 = max(0, y0), max(0, x0)
    sy1, sx1 = min(img.shape[0], y1), min(img.shape[1], x1)
    so_principal = np.zeros_like(alfa)
    so_principal[ys, xs] = principal['mascara'] * alfa[ys, xs]
    tela[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0, :3] = limpa[sy0:sy1, sx0:sx1]
    tela[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0, 3] = so_principal[sy0:sy1, sx0:sx1] * 255
    imagem = Image.fromarray(tela.astype(np.uint8), 'RGBA').resize((lado, lado), Image.LANCZOS)
    imagem.save(SAIDA / f'{nome}.webp', 'WEBP', quality=78, method=6)
    relatorio[nome] = {'diametro_original': int(meio * 2)}


def preparar_fundo(origem, relatorio):
    imagem = Image.open(origem).convert('RGB')
    lado = min(imagem.size)
    imagem = imagem.crop(((imagem.width - lado) // 2, (imagem.height - lado) // 2, (imagem.width + lado) // 2, (imagem.height + lado) // 2))
    imagem.resize((1000, 1000), Image.LANCZOS).save(SAIDA / 'fundo.webp', 'WEBP', quality=70, method=6)
    relatorio['fundo'] = {'lado': lado}


def main():
    originais = Path(sys.argv[1])
    SAIDA.mkdir(parents=True, exist_ok=True)
    relatorio = {}
    for arquivo, (fundo, nomes) in FOLHAS.items():
        caminho = originais / f'{arquivo}.png'
        if caminho.exists():
            preparar_folha(caminho, fundo, nomes, relatorio)
    for arquivo, (fundo, nome, lado) in CAMADAS.items():
        caminho = originais / f'{arquivo}.png'
        if caminho.exists():
            preparar_camada(caminho, fundo, nome, lado, relatorio)
    if (originais / 'fundo.png').exists():
        preparar_fundo(originais / 'fundo.png', relatorio)
    print(json.dumps(relatorio, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
