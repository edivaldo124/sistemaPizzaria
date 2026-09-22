from decimal import Decimal, InvalidOperation

from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, url_for

from config import db
from dao.pedido_dao import PedidoDAO
from modelos.endereco import Endereco
from modelos.pedido import TIPO_DELIVERY
from servicos.autorizacao import login_requerido
from servicos.carrinho import obter_carrinho_atual
from servicos.erros import ErroRegraNegocio
from servicos.integracoes import (
    IntegracaoExternaError,
    IntegracaoIndisponivel,
    calcular_rota_google_maps,
    criar_preferencia_mercado_pago,
    enviar_email_gmail,
)
from servicos.pedidos import cliente_cancelar_pedido, finalizar_pedido

pedido_bp = Blueprint('pedido', __name__)


@pedido_bp.route('/checkout', methods=['GET', 'POST'])
@login_requerido
def checkout(usuario):
    if usuario.cliente is None:
        abort(403)  # só cliente finaliza o próprio pedido pelo site

    carrinho = obter_carrinho_atual(usuario)
    enderecos = usuario.cliente.enderecos

    if request.method == 'POST':
        tipo = request.form.get('tipo')
        forma_pagamento = request.form.get('forma_pagamento')
        endereco_id = request.form.get('endereco_id', type=int)
        cupom_codigo = (request.form.get('cupom_codigo') or '').strip() or None
        observacoes = (request.form.get('observacoes') or '').strip() or None
        troco_texto = (request.form.get('troco_para') or '').strip()

        endereco = None
        if tipo == TIPO_DELIVERY:
            endereco = db.session.get(Endereco, endereco_id) if endereco_id else None
            if endereco is None or endereco.cliente_id != usuario.cliente.id:
                return render_template(
                    'pedido/checkout.html', carrinho=carrinho, enderecos=enderecos,
                    erro='Selecione um endereço de entrega válido.',
                ), 400

        troco_para = None
        if troco_texto:
            try:
                troco_para = Decimal(troco_texto.replace(',', '.'))
            except InvalidOperation:
                return render_template(
                    'pedido/checkout.html', carrinho=carrinho, enderecos=enderecos,
                    erro='Valor de troco inválido.',
                ), 400

        try:
            pedido = finalizar_pedido(
                carrinho=carrinho, tipo=tipo, forma_pagamento=forma_pagamento,
                cliente=usuario.cliente, endereco=endereco, troco_para=troco_para,
                cupom_codigo=cupom_codigo, observacoes=observacoes,
            )
        except ErroRegraNegocio as erro:
            return render_template(
                'pedido/checkout.html', carrinho=carrinho, enderecos=enderecos, erro=str(erro),
            ), 400

        pagamento_url = None
        if forma_pagamento in ('pix', 'cartao'):
            try:
                preferencia = criar_preferencia_mercado_pago(pedido)
                pagamento_url = preferencia.get('init_point') or preferencia.get('sandbox_init_point')
                if pagamento_url:
                    pedido.pagamento_atual.referencia_externa = str(preferencia.get('id', ''))[:120]
                    db.session.commit()
            except (IntegracaoIndisponivel, IntegracaoExternaError):
                current_app.logger.warning('Mercado Pago indisponível para o pedido %s', pedido.numero)

        if usuario.cliente.usuario.email:
            rota = None
            if endereco is not None:
                try:
                    rota = calcular_rota_google_maps(endereco)
                except (IntegracaoIndisponivel, IntegracaoExternaError):
                    current_app.logger.info('Google Maps indisponível para o pedido %s', pedido.numero)
            corpo = f'Pedido {pedido.numero} recebido. Total: R$ {pedido.total:.2f}. Status: recebido.'
            if rota:
                corpo += f" Rota estimada: {rota['distancia']} ({rota['duracao']})."
            try:
                enviar_email_gmail(
                    destinatario=usuario.cliente.usuario.email,
                    assunto=f'Pedido {pedido.numero} recebido',
                    corpo=corpo,
                )
            except (IntegracaoIndisponivel, IntegracaoExternaError):
                current_app.logger.info('Gmail indisponível para o pedido %s', pedido.numero)

        if pagamento_url:
            return redirect(pagamento_url)
        flash('Pedido recebido com sucesso.', 'sucesso')
        return redirect(url_for('pedido.acompanhar', numero=pedido.numero))

    return render_template('pedido/checkout.html', carrinho=carrinho, enderecos=enderecos)


@pedido_bp.route('/pedidos/<numero>')
@login_requerido
def acompanhar(usuario, numero):
    """RF22: cliente acompanha o andamento do próprio pedido."""
    pedido = PedidoDAO.buscar_por_numero(numero)
    if pedido is None:
        abort(404)
    eh_dono = usuario.cliente is not None and pedido.cliente_id == usuario.cliente.id
    if not eh_dono and not usuario.is_funcionario:
        abort(403)
    return render_template('pedido/acompanhar.html', pedido=pedido)


@pedido_bp.route('/meus-pedidos')
@login_requerido
def meus_pedidos(usuario):
    if usuario.cliente is None:
        abort(403)
    pedidos = PedidoDAO.listar_por_cliente(usuario.cliente.id)
    return render_template('pedido/meus_pedidos.html', pedidos=pedidos)


@pedido_bp.route('/pedidos/<numero>/cancelar', methods=['POST'])
@login_requerido
def cancelar(usuario, numero):
    """RN11: cliente só cancela sozinho antes do início do preparo."""
    pedido = PedidoDAO.buscar_por_numero(numero)
    if pedido is None:
        abort(404)
    try:
        cliente_cancelar_pedido(pedido=pedido, cliente=usuario.cliente)
    except ErroRegraNegocio as erro:
        return render_template('pedido/acompanhar.html', pedido=pedido, erro=str(erro)), 400
    return redirect(url_for('pedido.acompanhar', numero=numero))
