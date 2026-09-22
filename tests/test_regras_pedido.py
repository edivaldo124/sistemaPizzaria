"""Regras de negócio do ciclo de vida do pedido não cobertas por test_fluxo_pedido.py:
RN03 (média), RN06, RN07/RN08 (cupom), RN09 (troco), RN11 (cancelamento pelo cliente),
RN13/RN14 (fluxo de status), RN17 (pedido finalizado) e RN20 (cancelamento gerencial)."""
from datetime import timedelta
from decimal import Decimal

import pytest

from dao.usuario_dao import UsuarioDAO
from modelos.categoria import Categoria
from modelos.configuracao import ConfiguracaoLoja, REGRA_PRECO_MEDIA
from modelos.cupom import Cupom, DESCONTO_PERCENTUAL
from modelos.entrega import RegiaoEntrega
from modelos.pedido import (
    STATUS_CANCELADO, STATUS_CONFIRMADO, STATUS_EM_PREPARO, STATUS_ENTREGUE,
    STATUS_PRONTO, STATUS_RECEBIDO, STATUS_SAIU_PARA_ENTREGA, TIPO_RETIRADA,
)
from modelos.pizza import Sabor, SaborPreco, TamanhoPizza
from servicos.erros import ErroRegraNegocio
from servicos.pedidos import alterar_status_pedido, cliente_cancelar_pedido, finalizar_pedido
from servicos.tempo import agora_utc


def _preparar_cardapio(db, *, max_sabores=2):
    categoria = Categoria(nome='Pizzas')
    db.session.add(categoria)
    tamanho = TamanhoPizza(nome='Grande', max_sabores=max_sabores)
    db.session.add(tamanho)
    db.session.flush()

    mussarela = Sabor(nome='Mussarela')
    calabresa = Sabor(nome='Calabresa')
    db.session.add_all([mussarela, calabresa])
    db.session.flush()
    db.session.add(SaborPreco(sabor_id=mussarela.id, tamanho_id=tamanho.id, preco=Decimal('40.00')))
    db.session.add(SaborPreco(sabor_id=calabresa.id, tamanho_id=tamanho.id, preco=Decimal('50.00')))

    regiao = RegiaoEntrega(nome='Centro', taxa_entrega=Decimal('5.00'))
    db.session.add(regiao)
    db.session.commit()
    return tamanho, [mussarela, calabresa], regiao


def _cliente_com_carrinho(db, tamanho, sabores):
    usuario = UsuarioDAO.criar_cliente(nome='Ana', email='ana@example.com', senha='senha-forte-123')
    from servicos.carrinho import obter_carrinho_atual
    from dao.carrinho_dao import CarrinhoDAO

    carrinho = obter_carrinho_atual(usuario)
    CarrinhoDAO.adicionar_item(
        carrinho.id, tamanho_id=tamanho.id, quantidade=1, sabores_ids=[s.id for s in sabores],
    )
    db.session.refresh(carrinho)
    return usuario, carrinho


def test_regra_media_de_precos_multiplos_sabores(app, db):
    """RN03: quando configurado para média, o preço não é o maior valor."""
    tamanho, sabores, _regiao = _preparar_cardapio(db)
    ConfiguracaoLoja.obter().regra_preco_multiplos_sabores = REGRA_PRECO_MEDIA
    db.session.commit()

    usuario, carrinho = _cliente_com_carrinho(db, tamanho, sabores)
    pedido = finalizar_pedido(carrinho=carrinho, tipo=TIPO_RETIRADA, forma_pagamento='pix', cliente=usuario.cliente)

    assert pedido.subtotal == Decimal('45.00')  # média entre 40 e 50


def test_valor_de_troco_menor_que_total_e_rejeitado(app, db):
    """RN09."""
    tamanho, sabores, _regiao = _preparar_cardapio(db, max_sabores=1)
    usuario, carrinho = _cliente_com_carrinho(db, tamanho, [sabores[0]])

    with pytest.raises(ErroRegraNegocio):
        finalizar_pedido(
            carrinho=carrinho, tipo=TIPO_RETIRADA, forma_pagamento='dinheiro',
            cliente=usuario.cliente, troco_para=Decimal('1.00'),
        )


def test_cliente_nao_cancela_pedido_em_preparo(app, db):
    """RN11: depois do início do preparo, só gerência cancela."""
    tamanho, sabores, _regiao = _preparar_cardapio(db, max_sabores=1)
    usuario, carrinho = _cliente_com_carrinho(db, tamanho, [sabores[0]])
    pedido = finalizar_pedido(carrinho=carrinho, tipo=TIPO_RETIRADA, forma_pagamento='pix', cliente=usuario.cliente)

    alterar_status_pedido(pedido=pedido, novo_status=STATUS_CONFIRMADO)
    alterar_status_pedido(pedido=pedido, novo_status=STATUS_EM_PREPARO)

    with pytest.raises(ErroRegraNegocio):
        cliente_cancelar_pedido(pedido=pedido, cliente=usuario.cliente)


def test_cliente_cancela_pedido_recebido(app, db):
    """RN11: antes do preparo, o próprio cliente cancela."""
    tamanho, sabores, _regiao = _preparar_cardapio(db, max_sabores=1)
    usuario, carrinho = _cliente_com_carrinho(db, tamanho, [sabores[0]])
    pedido = finalizar_pedido(carrinho=carrinho, tipo=TIPO_RETIRADA, forma_pagamento='pix', cliente=usuario.cliente)

    cliente_cancelar_pedido(pedido=pedido, cliente=usuario.cliente)
    assert pedido.status == STATUS_CANCELADO


def test_cancelar_pedido_em_preparo_exige_gerencia(app, db):
    """RN20: funcionário comum não pode cancelar pedido já em preparo."""
    tamanho, sabores, _regiao = _preparar_cardapio(db, max_sabores=1)
    usuario, carrinho = _cliente_com_carrinho(db, tamanho, [sabores[0]])
    pedido = finalizar_pedido(carrinho=carrinho, tipo=TIPO_RETIRADA, forma_pagamento='pix', cliente=usuario.cliente)
    alterar_status_pedido(pedido=pedido, novo_status=STATUS_CONFIRMADO)
    alterar_status_pedido(pedido=pedido, novo_status=STATUS_EM_PREPARO)

    atendente = UsuarioDAO.criar_funcionario(nome='Bia', email='bia@pizzaria.com', senha='senha-forte-123', tipo='atendente')
    with pytest.raises(ErroRegraNegocio):
        alterar_status_pedido(pedido=pedido, novo_status=STATUS_CANCELADO, funcionario=atendente.funcionario)

    gerente = UsuarioDAO.criar_funcionario(nome='Gil', email='gil@pizzaria.com', senha='senha-forte-123', tipo='gerente')
    alterar_status_pedido(pedido=pedido, novo_status=STATUS_CANCELADO, funcionario=gerente.funcionario)
    assert pedido.status == STATUS_CANCELADO


def test_pedido_finalizado_nao_muda_de_status(app, db):
    """RN17."""
    tamanho, sabores, _regiao = _preparar_cardapio(db, max_sabores=1)
    usuario, carrinho = _cliente_com_carrinho(db, tamanho, [sabores[0]])
    pedido = finalizar_pedido(carrinho=carrinho, tipo=TIPO_RETIRADA, forma_pagamento='pix', cliente=usuario.cliente)
    for status in (STATUS_CONFIRMADO, STATUS_EM_PREPARO, STATUS_PRONTO):
        alterar_status_pedido(pedido=pedido, novo_status=status)
    alterar_status_pedido(pedido=pedido, novo_status=STATUS_ENTREGUE)

    with pytest.raises(ErroRegraNegocio):
        alterar_status_pedido(pedido=pedido, novo_status=STATUS_CANCELADO)


def test_retirada_nao_pode_ir_para_saiu_para_entrega(app, db):
    """RN14."""
    tamanho, sabores, _regiao = _preparar_cardapio(db, max_sabores=1)
    usuario, carrinho = _cliente_com_carrinho(db, tamanho, [sabores[0]])
    pedido = finalizar_pedido(carrinho=carrinho, tipo=TIPO_RETIRADA, forma_pagamento='pix', cliente=usuario.cliente)
    for status in (STATUS_CONFIRMADO, STATUS_EM_PREPARO, STATUS_PRONTO):
        alterar_status_pedido(pedido=pedido, novo_status=status)

    with pytest.raises(ErroRegraNegocio):
        alterar_status_pedido(pedido=pedido, novo_status=STATUS_SAIU_PARA_ENTREGA)


def test_nao_pode_pular_etapas_do_fluxo(app, db):
    """RN13: recebido não pode ir direto para em_preparo."""
    tamanho, sabores, _regiao = _preparar_cardapio(db, max_sabores=1)
    usuario, carrinho = _cliente_com_carrinho(db, tamanho, [sabores[0]])
    pedido = finalizar_pedido(carrinho=carrinho, tipo=TIPO_RETIRADA, forma_pagamento='pix', cliente=usuario.cliente)

    with pytest.raises(ErroRegraNegocio):
        alterar_status_pedido(pedido=pedido, novo_status=STATUS_EM_PREPARO)


def test_cupom_expirado_e_rejeitado(app, db):
    """RN07."""
    tamanho, sabores, _regiao = _preparar_cardapio(db, max_sabores=1)
    usuario, carrinho = _cliente_com_carrinho(db, tamanho, [sabores[0]])

    db.session.add(Cupom(
        codigo='VENCIDO10', tipo_desconto=DESCONTO_PERCENTUAL, valor=Decimal('10'),
        validade_fim=agora_utc() - timedelta(days=1),
    ))
    db.session.commit()

    with pytest.raises(ErroRegraNegocio):
        finalizar_pedido(
            carrinho=carrinho, tipo=TIPO_RETIRADA, forma_pagamento='pix',
            cliente=usuario.cliente, cupom_codigo='VENCIDO10',
        )


def test_cupom_abaixo_do_valor_minimo_e_rejeitado(app, db):
    """RN07: valor mínimo do cupom não atingido."""
    tamanho, sabores, _regiao = _preparar_cardapio(db, max_sabores=1)
    usuario, carrinho = _cliente_com_carrinho(db, tamanho, [sabores[0]])

    db.session.add(Cupom(
        codigo='ACIMA200', tipo_desconto=DESCONTO_PERCENTUAL, valor=Decimal('10'),
        valor_minimo_pedido=Decimal('200.00'),
    ))
    db.session.commit()

    with pytest.raises(ErroRegraNegocio):
        finalizar_pedido(
            carrinho=carrinho, tipo=TIPO_RETIRADA, forma_pagamento='pix',
            cliente=usuario.cliente, cupom_codigo='ACIMA200',
        )


def test_cupom_esgotado_e_rejeitado(app, db):
    """RN07: quantidade disponível esgotada."""
    tamanho, sabores, _regiao = _preparar_cardapio(db, max_sabores=1)
    usuario, carrinho = _cliente_com_carrinho(db, tamanho, [sabores[0]])

    db.session.add(Cupom(
        codigo='ESGOTADO', tipo_desconto=DESCONTO_PERCENTUAL, valor=Decimal('10'),
        quantidade_disponivel=1, quantidade_utilizada=1,
    ))
    db.session.commit()

    with pytest.raises(ErroRegraNegocio):
        finalizar_pedido(
            carrinho=carrinho, tipo=TIPO_RETIRADA, forma_pagamento='pix',
            cliente=usuario.cliente, cupom_codigo='ESGOTADO',
        )


def test_delivery_confirmado_exige_regiao_de_entrega_ativa(app, db):
    """RN06: endereço fora da área atendida não pode ser confirmado."""
    tamanho, sabores, regiao = _preparar_cardapio(db, max_sabores=1)
    usuario, carrinho = _cliente_com_carrinho(db, tamanho, [sabores[0]])

    from modelos.endereco import Endereco
    endereco = Endereco(
        cliente_id=usuario.cliente.id, logradouro='Rua X', numero='1', bairro='Centro',
        cidade='SP', uf='SP', regiao_entrega_id=regiao.id,
    )
    db.session.add(endereco)
    db.session.commit()

    from modelos.pedido import TIPO_DELIVERY
    pedido = finalizar_pedido(
        carrinho=carrinho, tipo=TIPO_DELIVERY, forma_pagamento='pix',
        cliente=usuario.cliente, endereco=endereco,
    )

    regiao.ativo = False
    db.session.commit()

    with pytest.raises(ErroRegraNegocio):
        alterar_status_pedido(pedido=pedido, novo_status=STATUS_CONFIRMADO)
