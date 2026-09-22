from flask import Blueprint, abort, flash, redirect, render_template, url_for

from dao.pedido_dao import PedidoDAO
from modelos.pedido import STATUS_EM_PREPARO, STATUS_PRONTO
from modelos.usuario import TIPO_ADMIN, TIPO_COZINHA, TIPO_GERENTE
from servicos.autorizacao import papel_requerido
from servicos.erros import ErroRegraNegocio
from servicos.pedidos import alterar_status_pedido

cozinha_bp = Blueprint('cozinha', __name__, url_prefix='/cozinha')

_PAPEIS_COZINHA = (TIPO_COZINHA, TIPO_GERENTE, TIPO_ADMIN)


@cozinha_bp.route('/')
@papel_requerido(*_PAPEIS_COZINHA)
def fila_pedidos(usuario):
    """RF19: fila de pedidos ordenada por prioridade e horário."""
    pedidos = PedidoDAO.listar_fila_cozinha()
    return render_template('cozinha/fila.html', pedidos=pedidos)


def _mudar_status(usuario, pedido_id, novo_status):
    pedido = PedidoDAO.buscar_por_id(pedido_id)
    if pedido is None:
        abort(404)
    try:
        alterar_status_pedido(pedido=pedido, novo_status=novo_status, funcionario=usuario.funcionario)
        flash('Status atualizado.', 'sucesso')
    except ErroRegraNegocio as erro:
        flash(str(erro), 'erro')
    return redirect(url_for('cozinha.fila_pedidos'))


@cozinha_bp.route('/pedidos/<int:pedido_id>/confirmar', methods=['POST'])
@papel_requerido(*_PAPEIS_COZINHA)
def confirmar(usuario, pedido_id):
    from modelos.pedido import STATUS_CONFIRMADO
    return _mudar_status(usuario, pedido_id, STATUS_CONFIRMADO)


@cozinha_bp.route('/pedidos/<int:pedido_id>/em-preparo', methods=['POST'])
@papel_requerido(*_PAPEIS_COZINHA)
def marcar_em_preparo(usuario, pedido_id):
    """RF20."""
    return _mudar_status(usuario, pedido_id, STATUS_EM_PREPARO)


@cozinha_bp.route('/pedidos/<int:pedido_id>/pronto', methods=['POST'])
@papel_requerido(*_PAPEIS_COZINHA)
def marcar_pronto(usuario, pedido_id):
    """RF20."""
    return _mudar_status(usuario, pedido_id, STATUS_PRONTO)
