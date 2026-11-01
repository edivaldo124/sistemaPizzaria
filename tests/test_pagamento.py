"""RF16: transições de status do pagamento (pendente -> aprovado/recusado)."""
from decimal import Decimal

from dao.usuario_dao import UsuarioDAO
from modelos.categoria import Categoria
from modelos.entrega import RegiaoEntrega
from modelos.pagamento import STATUS_APROVADO, STATUS_PENDENTE, STATUS_RECUSADO
from modelos.pizza import Sabor, SaborPreco, TamanhoPizza
from servicos.erros import ErroRegraNegocio
from servicos.pagamentos import aprovar_pagamento, recusar_pagamento


def _criar_pedido_delivery(db, client):
    categoria = Categoria(nome='Pizzas')
    db.session.add(categoria)
    tamanho = TamanhoPizza(nome='Média', max_sabores=1)
    db.session.add(tamanho)
    db.session.flush()
    sabor = Sabor(nome='Mussarela')
    db.session.add(sabor)
    db.session.flush()
    db.session.add(SaborPreco(sabor_id=sabor.id, tamanho_id=tamanho.id, preco=Decimal('35.00')))
    regiao = RegiaoEntrega(nome='Centro', taxa_entrega=Decimal('5.00'))
    db.session.add(regiao)
    db.session.commit()

    client.post('/cadastro', data={
        'nome': 'Ana Cliente', 'email': 'ana@example.com', 'telefone': '11999990000',
        'senha': 'senha-forte-123', 'confirmacao_senha': 'senha-forte-123',
    })
    client.post('/enderecos/', data={
        'logradouro': 'Rua X', 'numero': '1', 'bairro': 'Centro',
        'cidade': 'SP', 'uf': 'SP', 'regiao_entrega_id': regiao.id,
    })
    client.post('/carrinho/adicionar-pizza', data={'tamanho_id': tamanho.id, 'sabores_ids': [sabor.id], 'quantidade': '1'})
    endereco_id = db.session.execute(db.text('select id from enderecos limit 1')).scalar()
    client.post('/checkout', data={
        'tipo': 'delivery', 'endereco_id': endereco_id, 'forma_pagamento': 'pix',
    })

    from dao.pedido_dao import PedidoDAO
    cliente = UsuarioDAO.buscar_por_email('ana@example.com').cliente
    return PedidoDAO.listar_por_cliente(cliente.id)[0]


def test_aprovar_pagamento_pendente(client, db):
    pedido = _criar_pedido_delivery(db, client)
    assert pedido.pagamento_atual.status == STATUS_PENDENTE

    aprovar_pagamento(pedido)
    assert pedido.pagamento_atual.status == STATUS_APROVADO


def test_recusar_pagamento_pendente(client, db):
    pedido = _criar_pedido_delivery(db, client)

    recusar_pagamento(pedido)
    assert pedido.pagamento_atual.status == STATUS_RECUSADO


def test_nao_pode_reprocessar_pagamento_ja_aprovado(client, db):
    pedido = _criar_pedido_delivery(db, client)
    aprovar_pagamento(pedido)

    try:
        aprovar_pagamento(pedido)
        assert False, 'deveria ter levantado ErroRegraNegocio'
    except ErroRegraNegocio:
        pass


def test_rota_aprovar_pagamento_exige_papel_de_caixa(client, db):
    pedido = _criar_pedido_delivery(db, client)

    # Cliente autenticado (não é atendente/gerente/admin) não pode aprovar pagamento.
    resposta = client.post(f'/pagamentos/{pedido.id}/aprovar', follow_redirects=False)
    assert resposta.status_code == 403


def _webhook(client, monkeypatch, resposta):
    import blueprints.pagamento_bp as pagamento_bp
    monkeypatch.setattr(pagamento_bp, 'consultar_pagamento_mercado_pago', lambda _id: resposta)
    return client.post('/pagamentos/mercadopago/webhook', json={'data': {'id': '123'}})


def test_webhook_aprova_somente_com_valor_integral(client, db, monkeypatch):
    pedido = _criar_pedido_delivery(db, client)
    base = {'external_reference': pedido.numero, 'status': 'approved', 'currency_id': 'BRL'}

    _webhook(client, monkeypatch, {**base, 'transaction_amount': 1.0})
    assert pedido.pagamento_atual.status == STATUS_PENDENTE

    _webhook(client, monkeypatch, {**base, 'transaction_amount': float(pedido.total)})
    assert pedido.pagamento_atual.status == STATUS_APROVADO


def test_webhook_pendente_atrasado_nao_desfaz_aprovacao(client, db, monkeypatch):
    pedido = _criar_pedido_delivery(db, client)
    aprovar_pagamento(pedido)

    _webhook(client, monkeypatch, {'external_reference': pedido.numero, 'status': 'pending'})
    assert pedido.pagamento_atual.status == STATUS_APROVADO


def test_webhook_ignora_id_nao_numerico(client, db, monkeypatch):
    chamado = []
    import blueprints.pagamento_bp as pagamento_bp
    monkeypatch.setattr(pagamento_bp, 'consultar_pagamento_mercado_pago', lambda _id: chamado.append(_id) or {})
    r = client.post('/pagamentos/mercadopago/webhook', json={'data': {'id': '../users/me'}})
    assert r.status_code == 200 and chamado == []
