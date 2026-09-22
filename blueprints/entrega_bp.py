from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from dao.entrega_dao import EntregaDAO, EntregadorDAO
from dao.pedido_dao import PedidoDAO
from modelos.pedido import STATUS_ENTREGUE, STATUS_SAIU_PARA_ENTREGA, TIPO_DELIVERY
from modelos.usuario import TIPO_ADMIN, TIPO_ATENDENTE, TIPO_ENTREGADOR, TIPO_GERENTE
from servicos.autorizacao import papel_requerido
from servicos.erros import ErroRegraNegocio
from servicos.pedidos import alterar_status_pedido

entrega_bp = Blueprint('entrega', __name__, url_prefix='/entregas')

_PAPEIS_DESPACHO = (TIPO_ATENDENTE, TIPO_GERENTE, TIPO_ADMIN)


@entrega_bp.route('/')
@papel_requerido(*_PAPEIS_DESPACHO)
def despacho(usuario):
    """RF24: atendente associa um entregador aos pedidos delivery prontos."""
    pedidos_prontos = [p for p in PedidoDAO.listar_prontos_para_entrega() if p.tipo == TIPO_DELIVERY]
    entregadores = EntregadorDAO.listar()
    return render_template('entrega/despacho.html', pedidos=pedidos_prontos, entregadores=entregadores)


@entrega_bp.route('/<int:pedido_id>/atribuir', methods=['POST'])
@papel_requerido(*_PAPEIS_DESPACHO)
def atribuir(usuario, pedido_id):
    pedido = PedidoDAO.buscar_por_id(pedido_id)
    entregador_id = request.form.get('entregador_id', type=int)
    if pedido is None or not entregador_id:
        abort(404)
    try:
        EntregaDAO.criar(pedido_id=pedido.id, entregador_id=entregador_id)
        alterar_status_pedido(
            pedido=pedido, novo_status=STATUS_SAIU_PARA_ENTREGA, funcionario=usuario.funcionario,
            observacao='Saiu para entrega.',
        )
        flash('Entregador atribuído.', 'sucesso')
    except ErroRegraNegocio as erro:
        flash(str(erro), 'erro')
    return redirect(url_for('entrega.despacho'))


@entrega_bp.route('/minhas')
@papel_requerido(TIPO_ENTREGADOR)
def minhas_entregas(usuario):
    """RF25: entregador consulta endereço, contato, forma de pagamento e observações."""
    entregador = EntregadorDAO.buscar_por_usuario(usuario.id)
    entregas = EntregaDAO.listar_do_entregador(entregador.id) if entregador else []
    return render_template('entrega/minhas_entregas.html', entregas=entregas)


@entrega_bp.route('/<int:pedido_id>/entregue', methods=['POST'])
@papel_requerido(TIPO_ENTREGADOR)
def marcar_entregue(usuario, pedido_id):
    pedido = PedidoDAO.buscar_por_id(pedido_id)
    entrega = EntregaDAO.buscar_por_pedido(pedido_id)
    entregador = EntregadorDAO.buscar_por_usuario(usuario.id)
    if pedido is None or entrega is None or entregador is None or entrega.entregador_id != entregador.id:
        abort(404)
    try:
        EntregaDAO.marcar_entregue(entrega)
        alterar_status_pedido(pedido=pedido, novo_status=STATUS_ENTREGUE, funcionario=usuario.funcionario)
        flash('Entrega concluída.', 'sucesso')
    except ErroRegraNegocio as erro:
        flash(str(erro), 'erro')
    return redirect(url_for('entrega.minhas_entregas'))
