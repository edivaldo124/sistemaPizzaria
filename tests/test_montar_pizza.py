"""Tela de montagem de pizza: dados que a prévia 3D e o preço estimado leem do HTML."""
from decimal import Decimal

from modelos.pizza import Sabor, SaborPreco, TamanhoPizza


def test_montar_pizza_expoe_dados_da_previa(client, db):
    tamanho = TamanhoPizza(nome='Grande', max_sabores=2, numero_fatias=8)
    db.session.add(tamanho)
    db.session.flush()
    sabor = Sabor(nome='Calabresa')
    db.session.add(sabor)
    db.session.flush()
    db.session.add(SaborPreco(sabor_id=sabor.id, tamanho_id=tamanho.id, preco=Decimal('45.00')))
    db.session.commit()

    conteudo = client.get('/montar-pizza').get_data(as_text=True)

    assert 'data-pizza-stage' in conteudo
    assert 'data-regra-preco="maior_valor"' in conteudo
    assert 'data-max="2"' in conteudo and 'data-fatias="8"' in conteudo
    assert f'data-precos="{tamanho.id}:45.00"' in conteudo
    assert 'type="module"' in conteudo and 'js/pizza3d.js' in conteudo
