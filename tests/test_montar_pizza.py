"""Tela de montagem de pizza: dados que a montagem com fotos (static/js/pizza.js) lê do HTML."""
from decimal import Decimal

from modelos.pizza import Sabor, SaborPreco, TamanhoPizza


def test_montar_pizza_expoe_dados_da_montagem(client, db):
    tamanho = TamanhoPizza(nome='Grande', max_sabores=2, numero_fatias=8)
    db.session.add(tamanho)
    db.session.flush()
    sabor = Sabor(nome='Calabresa', descricao='Calabresa fatiada e cebola')
    db.session.add(sabor)
    db.session.flush()
    db.session.add(SaborPreco(sabor_id=sabor.id, tamanho_id=tamanho.id, preco=Decimal('45.00')))
    db.session.commit()

    conteudo = client.get('/montar-pizza').get_data(as_text=True)

    assert 'data-palco' in conteudo and 'imagens/pizza/massa.webp' in conteudo
    assert 'data-max-sabores="2"' in conteudo and 'data-fatias="8"' in conteudo
    assert 'data-nome="Calabresa"' in conteudo and 'data-detalhe="Calabresa fatiada e cebola"' in conteudo
    assert 'js/pizza.js' in conteudo and 'pizza3d' not in conteudo
