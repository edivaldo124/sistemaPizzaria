"""Testes da página inicial com vídeo hero e transição do cardápio para /cardapio."""
from decimal import Decimal

from dao.catalogo_dao import CategoriaDAO, ProdutoDAO
from modelos.categoria import Categoria
from modelos.produto import Produto


def test_pagina_inicial_contem_video_hero_e_link_cardapio(client, db):
    resposta = client.get('/')
    assert resposta.status_code == 200
    conteudo = resposta.get_data(as_text=True)

    # Hero com o vídeo que avança com a rolagem
    assert 'data-hero' in conteudo
    assert 'videos/forno.mp4' in conteudo

    # Link para o cardápio
    assert '/cardapio' in conteudo
    assert 'Ver o cardápio' in conteudo

    # Manchetes por etapa e medidor de rolagem
    assert conteudo.count('data-manchete') == 5
    assert 'Lenha de' in conteudo
    assert 'data-hero-num' in conteudo


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

    assert 'Os que mais saem do forno' in conteudo
    assert 'Pizza Marguerita Especial' in conteudo
    assert 'Tomate confit e manjericão fresco' in conteudo


def test_pagina_cardapio_nao_contem_video_hero(client, db):
    resposta = client.get('/cardapio')
    assert resposta.status_code == 200
    conteudo = resposta.get_data(as_text=True)

    assert 'data-hero' not in conteudo
    assert 'O cardápio de hoje' in conteudo


def test_carrinho_nao_contem_video_hero(client, db):
    resposta = client.get('/carrinho/')
    assert resposta.status_code == 200
    conteudo = resposta.get_data(as_text=True)

    assert 'data-hero' not in conteudo
