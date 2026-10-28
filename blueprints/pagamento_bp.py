from decimal import Decimal, InvalidOperation

from flask import Blueprint, abort, current_app, flash, redirect, request, url_for

from config import csrf, db
from dao.pedido_dao import PedidoDAO
from modelos.pagamento import STATUS_APROVADO, STATUS_ESTORNADO, STATUS_PENDENTE, STATUS_RECUSADO
from modelos.usuario import TIPO_ADMIN, TIPO_ATENDENTE, TIPO_GERENTE
from servicos.autorizacao import papel_requerido
from servicos.erros import ErroRegraNegocio
from servicos.pagamentos import aprovar_pagamento, recusar_pagamento
from servicos.integracoes import consultar_pagamento_mercado_pago, moeda_pagamento

pagamento_bp = Blueprint('pagamento', __name__, url_prefix='/pagamentos')

_PAPEIS_CAIXA = (TIPO_ATENDENTE, TIPO_GERENTE, TIPO_ADMIN)


@pagamento_bp.route('/mercadopago/webhook', methods=['POST'])
@csrf.exempt
def webhook_mercado_pago():
    """Confirma o pagamento consultando o Mercado Pago, nunca pelo payload recebido."""
    dados = request.get_json(silent=True) or {}
    pagamento_id = dados.get('data', {}).get('id') or request.args.get('data.id')
    # O id vai para a URL da API do Mercado Pago junto com o token: só aceita números.
    if not pagamento_id or not str(pagamento_id).isdigit():
        return {'status': 'ignored'}, 200
    try:
        resposta = consultar_pagamento_mercado_pago(str(pagamento_id))
    except Exception:
        current_app.logger.exception('Falha ao consultar webhook Mercado Pago')
        return {'status': 'retry'}, 502

    numero = resposta.get('external_reference')
    pedido = PedidoDAO.buscar_por_numero(numero) if numero else None
    if pedido is None or pedido.pagamento_atual is None:
        return {'status': 'ignored'}, 200

    status = resposta.get('status')
    pagamento = pedido.pagamento_atual
    if status == 'approved':
        # Só confirma se o valor pago cobre o pedido (RN10).
        try:
            valor_pago = Decimal(str(resposta.get('transaction_amount')))
        except (InvalidOperation, ValueError):
            valor_pago = Decimal('0')
        if valor_pago < pagamento.valor or resposta.get('currency_id') != moeda_pagamento():
            current_app.logger.warning('Pagamento %s com valor divergente do pedido %s', pagamento_id, numero)
            return {'status': 'ignored'}, 200
        novo_status = STATUS_APROVADO
    elif status in ('refunded', 'charged_back'):
        novo_status = STATUS_ESTORNADO
    elif status in ('rejected', 'cancelled'):
        novo_status = STATUS_RECUSADO
    elif status in ('pending', 'in_process', 'in_mediation'):
        novo_status = STATUS_PENDENTE
    else:
        return {'status': 'ignored'}, 200
    # Notificações chegam fora de ordem: um "pendente" atrasado não desfaz uma aprovação.
    if pagamento.status in (STATUS_APROVADO, STATUS_ESTORNADO) and novo_status in (STATUS_PENDENTE, STATUS_RECUSADO):
        return {'status': 'ignored'}, 200
    pagamento.status = novo_status
    pagamento.referencia_externa = str(pagamento_id)[:120]
    db.session.commit()
    return {'status': 'ok'}, 200


@pagamento_bp.route('/<int:pedido_id>/aprovar', methods=['POST'])
@papel_requerido(*_PAPEIS_CAIXA)
def aprovar(usuario, pedido_id):
    """RF16: atendente confirma o recebimento (dinheiro/Pix/cartão presencial)."""
    pedido = PedidoDAO.buscar_por_id(pedido_id)
    if pedido is None:
        abort(404)
    try:
        aprovar_pagamento(pedido)
        flash('Pagamento aprovado.', 'sucesso')
    except ErroRegraNegocio as erro:
        flash(str(erro), 'erro')
    return redirect(url_for('pedido.acompanhar', numero=pedido.numero))


@pagamento_bp.route('/<int:pedido_id>/recusar', methods=['POST'])
@papel_requerido(*_PAPEIS_CAIXA)
def recusar(usuario, pedido_id):
    pedido = PedidoDAO.buscar_por_id(pedido_id)
    if pedido is None:
        abort(404)
    try:
        recusar_pagamento(pedido)
        flash('Pagamento recusado.', 'sucesso')
    except ErroRegraNegocio as erro:
        flash(str(erro), 'erro')
    return redirect(url_for('pedido.acompanhar', numero=pedido.numero))
