"""Teste de fluxo real, ponta a ponta: cardápio -> monta pizza -> carrinho ->
checkout -> pedido criado com preço calculado pelo backend -> cozinha avança o status.
"""
from decimal import Decimal

from dao.catalogo_dao import CategoriaDAO, SaborDAO, TamanhoDAO
from dao.pedido_dao import PedidoDAO
from dao.usuario_dao import UsuarioDAO
from modelos.categoria import Categoria
from modelos.entrega import RegiaoEntrega
from modelos.pizza import Sabor, SaborPreco, TamanhoPizza
from modelos.pedido import STATUS_CONFIRMADO, STATUS_EM_PREPARO, STATUS_PRONTO, STATUS_RECEBIDO


def _preparar_cardapio(db):
    categoria = Categoria(nome='Pizzas')
    db.session.add(categoria)

    tamanho = TamanhoPizza(nome='Grande', max_sabores=2)
    db.session.add(tamanho)
    db.session.flush()

    mussarela = Sabor(nome='Mussarela')
    calabresa = Sabor(nome='Calabresa')
    db.session.add_all([mussarela, calabresa])
    db.session.flush()

    db.session.add(SaborPreco(sabor_id=mussarela.id, tamanho_id=tamanho.id, preco=Decimal('40.00')))
    db.session.add(SaborPreco(sabor_id=calabresa.id, tamanho_id=tamanho.id, preco=Decimal('45.00')))

    regiao = RegiaoEntrega(nome='Centro', taxa_entrega=Decimal('5.00'))
    db.session.add(regiao)
    db.session.commit()

    return tamanho, [mussarela, calabresa], regiao


def test_fluxo_completo_pedido_delivery(client, db):
    tamanho, sabores, regiao = _preparar_cardapio(db)

    # RF01: cadastro do cliente
    resposta = client.post('/cadastro', data={
        'nome': 'Ana Cliente', 'email': 'ana@example.com', 'telefone': '11999990000',
        'senha': 'senha-forte-123', 'confirmacao_senha': 'senha-forte-123',
    }, follow_redirects=True)
    assert resposta.status_code == 200

    # RF04: endereço de entrega
    resposta = client.post('/enderecos/', data={
        'logradouro': 'Rua das Pizzas', 'numero': '100', 'bairro': 'Centro',
        'cidade': 'São Paulo', 'uf': 'SP', 'regiao_entrega_id': regiao.id,
    }, follow_redirects=True)
    assert resposta.status_code == 200

    # RF09: monta pizza com 2 sabores - RN03 (maior valor) deve valer 45.00
    resposta = client.post('/carrinho/adicionar-pizza', data={
        'tamanho_id': tamanho.id,
        'sabores_ids': [str(s.id) for s in sabores],
        'quantidade': '1',
    }, follow_redirects=True)
    assert resposta.status_code == 200

    endereco_id = db.session.execute(db.text('select id from enderecos limit 1')).scalar()

    # RF12/RF14: fecha o pedido como delivery, pagamento em dinheiro com troco
    resposta = client.post('/checkout', data={
        'tipo': 'delivery', 'endereco_id': endereco_id,
        'forma_pagamento': 'dinheiro', 'troco_para': '60,00',
    }, follow_redirects=True)
    assert resposta.status_code == 200

    pedidos = PedidoDAO.listar_por_cliente(UsuarioDAO.buscar_por_email('ana@example.com').cliente.id)
    assert len(pedidos) == 1
    pedido = pedidos[0]

    # RN03: dois sabores -> preço = maior valor entre eles (45.00), não a soma nem a média.
    assert pedido.subtotal == Decimal('45.00')
    assert pedido.taxa_entrega == Decimal('5.00')
    assert pedido.total == Decimal('50.00')
    assert pedido.status == STATUS_RECEBIDO

    # RF02: cria funcionário da cozinha e avança o pedido pela fila (RF19/RF20/RN13)
    UsuarioDAO.criar_funcionario(nome='Beto Cozinha', email='beto@pizzaria.com', senha='senha-forte-123', tipo='cozinha')
    client_cozinha = client
    client_cozinha.post('/logout')
    client_cozinha.post('/login', data={'email': 'beto@pizzaria.com', 'senha': 'senha-forte-123'})

    resposta = client_cozinha.get('/cozinha/')
    assert resposta.status_code == 200
    assert pedido.numero.encode() in resposta.data

    client_cozinha.post(f'/cozinha/pedidos/{pedido.id}/confirmar')
    assert PedidoDAO.buscar_por_id(pedido.id).status == STATUS_CONFIRMADO

    client_cozinha.post(f'/cozinha/pedidos/{pedido.id}/em-preparo')
    assert PedidoDAO.buscar_por_id(pedido.id).status == STATUS_EM_PREPARO

    client_cozinha.post(f'/cozinha/pedidos/{pedido.id}/pronto')
    assert PedidoDAO.buscar_por_id(pedido.id).status == STATUS_PRONTO


def test_nao_pode_exceder_maximo_de_sabores_do_tamanho(client, db):
    """RN02: tamanho aceita no máximo N sabores."""
    tamanho, sabores, _regiao = _preparar_cardapio(db)

    terceiro = Sabor(nome='Portuguesa')
    db.session.add(terceiro)
    db.session.flush()
    db.session.add(SaborPreco(sabor_id=terceiro.id, tamanho_id=tamanho.id, preco=Decimal('42.00')))
    db.session.commit()

    client.post('/cadastro', data={
        'nome': 'Ana Cliente', 'email': 'ana@example.com', 'telefone': '11999990000',
        'senha': 'senha-forte-123', 'confirmacao_senha': 'senha-forte-123',
    })

    todos_ids = [str(s.id) for s in sabores] + [str(terceiro.id)]
    resposta = client.post('/carrinho/adicionar-pizza', data={
        'tamanho_id': tamanho.id, 'sabores_ids': todos_ids, 'quantidade': '1',
    })
    assert resposta.status_code == 400
    assert 'no máximo 2 sabor'.encode('utf-8') in resposta.data
