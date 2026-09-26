"""Testes da página inicial com vídeo hero e transição do cardápio para /cardapio."""
from decimal import Decimal

from dao.catalogo_dao import CategoriaDAO, ProdutoDAO
from modelos.categoria import Categoria
from modelos.produto import Produto


def test_pagina_inicial_contem_video_hero_e_link_cardapio(client, db):
    resposta = client.get('/')
    assert resposta.status_code == 200
    conteudo = resposta.get_data(as_text=True)

    # Hero com atributo data-video-hero
    assert 'data-video-hero' in conteudo

    # Link para o cardápio
    assert '/cardapio' in conteudo
    assert 'Ver cardápio' in conteudo

    # Elementos do hero
    assert 'Direto do forno a lenha' in conteudo
    assert 'ROLE' in conteudo
    assert 'data-hero-progress' in conteudo


def test_pagina_inicial_exibe_destaques(client, db):
    # Cria categoria e produtos para teste dos destaques
    categoria = Categoria(nome='Especiais', ordem_exibicao=1, ativo=True)
    db.session.add(categoria)
    db.session.flush()

    p1 = Produto(
        nome='Pizza Marguerita Especial',
        descricao='Tomate confit e manjericão fresco',
        preco=Decimal('58.00'),
        categoria_id=categoria.id,
        ativo=True,
        disponivel=True,
    )
    db.session.add(p1)
    db.session.commit()

    resposta = client.get('/')
    assert resposta.status_code == 200
    conteudo = resposta.get_data(as_text=True)

    assert 'Destaques da casa' in conteudo
    assert 'Pizza Marguerita Especial' in conteudo
    assert 'Tomate confit e manjericão fresco' in conteudo


def test_pagina_cardapio_nao_contem_video_hero(client, db):
    resposta = client.get('/cardapio')
    assert resposta.status_code == 200
    conteudo = resposta.get_data(as_text=True)

    assert 'data-video-hero' not in conteudo
    assert 'O cardápio de hoje' in conteudo


def test_carrinho_nao_contem_video_hero(client, db):
    resposta = client.get('/carrinho/')
    assert resposta.status_code == 200
    conteudo = resposta.get_data(as_text=True)

    assert 'data-video-hero' not in conteudo
