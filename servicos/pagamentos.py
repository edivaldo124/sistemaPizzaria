"""RF14-RF16: transições de status do pagamento. Separado de servicos/pedidos.py
porque o pagamento tem seu próprio ciclo de vida (RN10: só é considerado pago após
confirmação), ainda que hoje a confirmação seja manual (dinheiro/Pix/cartão
presencial) - o texto de erro e a validação continuam os mesmos quando um gateway
eletrônico assumir a confirmação (RF23)."""
from config import db
from modelos.pagamento import STATUS_APROVADO, STATUS_PENDENTE, STATUS_RECUSADO
from servicos.erros import ErroRegraNegocio


def _pagamento_pendente_do_pedido(pedido):
    pagamento = pedido.pagamento_atual
    if pagamento is None:
        raise ErroRegraNegocio('Pedido sem pagamento registrado.')
    if pagamento.status != STATUS_PENDENTE:
        raise ErroRegraNegocio('Este pagamento já foi processado.')
    return pagamento


def aprovar_pagamento(pedido):
    pagamento = _pagamento_pendente_do_pedido(pedido)
    pagamento.status = STATUS_APROVADO
    db.session.commit()
    return pagamento


def recusar_pagamento(pedido):
    pagamento = _pagamento_pendente_do_pedido(pedido)
    pagamento.status = STATUS_RECUSADO
    db.session.commit()
    return pagamento
