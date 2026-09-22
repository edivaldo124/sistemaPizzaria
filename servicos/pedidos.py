"""Orquestração do ciclo de vida do pedido (RF17-RF22, RN06, RN09, RN11, RN13-RN20).

`finalizar_pedido` é o único caminho para transformar um carrinho em pedido: valida
tudo no backend, calcula os valores a partir do banco (nunca do que o navegador
mandou) e grava pedido + itens + pagamento + histórico numa única transação.
"""
from config import db
from modelos.pagamento import FORMA_DINHEIRO, Pagamento, STATUS_APROVADO, STATUS_ESTORNADO
from modelos.pedido import (
    FLUXO_PEDIDO_POR_TIPO, STATUS_CANCELADO, STATUS_CONFIRMADO, STATUS_EM_PREPARO, STATUS_FINAIS,
    STATUS_PRONTO, STATUS_RECEBIDO, STATUS_SAIU_PARA_ENTREGA, STATUS_PEDIDO_VALIDOS,
    HistoricoPedido, ItemPedido, ItemPedidoAdicional, ItemPedidoSabor, Pedido, TIPO_DELIVERY,
    TIPO_SALAO,
)
from modelos.carrinho import STATUS_CARRINHO_CONVERTIDO
from modelos.cupom import Cupom
from servicos import disponibilidade, precos
from servicos.erros import ErroRegraNegocio
from servicos.estoque import descontar_estoque_do_pedido
from servicos.tempo import agora_utc


def finalizar_pedido(*, carrinho, tipo, forma_pagamento, cliente=None, endereco=None, comanda=None,
                      troco_para=None, cupom_codigo=None, observacoes=None, atendente=None,
                      horario_agendado=None, agora=None):
    agora = agora or agora_utc()

    if not carrinho.itens:
        raise ErroRegraNegocio('O carrinho está vazio.')

    if tipo == TIPO_DELIVERY:
        if endereco is None:
            raise ErroRegraNegocio('Informe um endereço de entrega.')
        if endereco.regiao_entrega is None or not endereco.regiao_entrega.ativo:
            raise ErroRegraNegocio('Este endereço está fora da área de entrega atendida.')  # RN06
        taxa_entrega = endereco.regiao_entrega.taxa_entrega
    elif tipo == TIPO_SALAO:
        if comanda is None:
            raise ErroRegraNegocio('Pedido de salão precisa estar associado a uma mesa/comanda.')  # RN15
        taxa_entrega = precos.arredondar(0)
    else:
        taxa_entrega = precos.arredondar(0)

    itens_precificados = [(item, precos.calcular_preco_item_carrinho(item)) for item in carrinho.itens]

    cupom = None
    if cupom_codigo:
        cupom = Cupom.query.filter_by(codigo=cupom_codigo.strip().upper()).first()
        if cupom is None:
            raise ErroRegraNegocio('Cupom inválido.')

    totais = precos.calcular_totais(
        [(preco, item.quantidade) for item, preco in itens_precificados],
        taxa_entrega=taxa_entrega, cupom=cupom, agora=agora,
    )

    disponibilidade.validar_valor_minimo(totais['subtotal'])
    disponibilidade.validar_horario_pedido(agora, horario_agendado)

    if forma_pagamento == FORMA_DINHEIRO and troco_para is not None:
        if troco_para < totais['total']:  # RN09
            raise ErroRegraNegocio('O valor para troco deve ser maior ou igual ao total do pedido.')

    try:
        pedido = Pedido(
            cliente_id=cliente.id if cliente else None,
            tipo=tipo,
            endereco_entrega_id=endereco.id if endereco else None,
            comanda_id=comanda.id if comanda else None,
            subtotal=totais['subtotal'], desconto=totais['desconto'],
            taxa_entrega=totais['taxa_entrega'], total=totais['total'],
            cupom_id=cupom.id if cupom else None,
            observacoes=observacoes,
            atendente_id=atendente.id if atendente else None,
            horario_agendado=horario_agendado,
        )
        db.session.add(pedido)
        db.session.flush()

        for item_carrinho, preco_unitario in itens_precificados:
            item_pedido = ItemPedido(
                pedido_id=pedido.id, produto_id=item_carrinho.produto_id,
                tamanho_id=item_carrinho.tamanho_id, massa_id=item_carrinho.massa_id,
                borda_id=item_carrinho.borda_id, quantidade=item_carrinho.quantidade,
                preco_unitario=preco_unitario,
                subtotal=precos.arredondar(preco_unitario * item_carrinho.quantidade),
                observacoes=item_carrinho.observacoes,
            )
            db.session.add(item_pedido)
            db.session.flush()

            for sabor_carrinho in item_carrinho.sabores:
                db.session.add(ItemPedidoSabor(item_pedido_id=item_pedido.id, sabor_id=sabor_carrinho.sabor_id))
            for adicional_carrinho in item_carrinho.adicionais:
                db.session.add(ItemPedidoAdicional(
                    item_pedido_id=item_pedido.id, adicional_id=adicional_carrinho.adicional_id,
                    quantidade=adicional_carrinho.quantidade, preco_unitario=adicional_carrinho.adicional.preco,
                ))

        db.session.add(Pagamento(
            pedido_id=pedido.id, forma=forma_pagamento, valor=totais['total'], troco_para=troco_para,
        ))
        db.session.add(HistoricoPedido(
            pedido_id=pedido.id, funcionario_id=atendente.id if atendente else None,
            status_anterior=None, status_novo=STATUS_RECEBIDO, observacao='Pedido criado.',
        ))

        if cupom is not None:
            cupom.quantidade_utilizada += 1

        carrinho.status = STATUS_CARRINHO_CONVERTIDO

        ingredientes_abaixo_do_minimo = descontar_estoque_do_pedido(pedido)

        db.session.commit()
        pedido.ingredientes_abaixo_do_minimo = ingredientes_abaixo_do_minimo  # só para a view avisar (RF33)
        return pedido
    except Exception:
        db.session.rollback()
        raise


def _registrar_transicao(pedido, novo_status, funcionario, observacao):
    anterior = pedido.status
    pedido.status = novo_status
    db.session.add(HistoricoPedido(
        pedido_id=pedido.id, funcionario_id=funcionario.id if funcionario else None,
        status_anterior=anterior, status_novo=novo_status, observacao=observacao,
    ))
    db.session.commit()


def alterar_status_pedido(*, pedido, novo_status, funcionario=None, observacao=None):
    """RF18/RF20, RN13/RN14/RN17/RN19/RN20 - único caminho para mudar o status."""
    if pedido.status in STATUS_FINAIS:
        raise ErroRegraNegocio('Pedido finalizado não pode ser alterado.')
    if novo_status not in STATUS_PEDIDO_VALIDOS:
        raise ErroRegraNegocio('Status inválido.')

    if novo_status == STATUS_CANCELADO:
        if pedido.status in (STATUS_EM_PREPARO, STATUS_PRONTO, STATUS_SAIU_PARA_ENTREGA):
            # RN20: cancelar pedido já em preparo exige gerência.
            if funcionario is None or not funcionario.usuario.is_gerencia:
                raise ErroRegraNegocio('Somente gerente ou administrador pode cancelar um pedido em preparo.')
        _registrar_transicao(pedido, STATUS_CANCELADO, funcionario, observacao or 'Pedido cancelado.')
        pagamento = pedido.pagamento_atual
        if pagamento is not None and pagamento.status == STATUS_APROVADO:
            pagamento.status = STATUS_ESTORNADO  # RN19
            db.session.commit()
        return pedido

    if novo_status == STATUS_SAIU_PARA_ENTREGA and pedido.tipo != TIPO_DELIVERY:
        raise ErroRegraNegocio('Só pedidos delivery usam o status "saiu para entrega".')  # RN14

    if novo_status == STATUS_CONFIRMADO and pedido.tipo == TIPO_DELIVERY:
        endereco = pedido.endereco_entrega
        if endereco is None or endereco.regiao_entrega is None or not endereco.regiao_entrega.ativo:
            raise ErroRegraNegocio('Endereço fora da área de entrega atendida.')  # RN06

    # RN13/RN14: cada tipo de pedido tem seu próprio fluxo (retirada/salão pulam
    # "saiu_para_entrega"), e só se pode avançar uma posição por vez.
    fluxo = FLUXO_PEDIDO_POR_TIPO[pedido.tipo]
    posicao_atual = fluxo.index(pedido.status) if pedido.status in fluxo else -1
    posicao_novo = fluxo.index(novo_status) if novo_status in fluxo else -1
    if posicao_novo != posicao_atual + 1:
        raise ErroRegraNegocio(f'Não é possível ir de "{pedido.status}" direto para "{novo_status}".')

    _registrar_transicao(pedido, novo_status, funcionario, observacao)
    return pedido


def cliente_cancelar_pedido(*, pedido, cliente, observacao=None):
    if pedido.cliente_id != cliente.id:
        raise ErroRegraNegocio('Este pedido não pertence a este cliente.')
    if not pedido.pode_cliente_cancelar_diretamente():
        # RN11: depois do início do preparo, só o gerente cancela (alterar_status_pedido).
        raise ErroRegraNegocio('O preparo já começou. Fale com o atendimento para cancelar.')
    _registrar_transicao(pedido, STATUS_CANCELADO, None, observacao or 'Cancelado pelo cliente.')
    return pedido
