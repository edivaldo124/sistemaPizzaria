from decimal import Decimal

from flask import Blueprint, redirect, render_template, request, url_for

from dao.carrinho_dao import CarrinhoDAO
from dao.catalogo_dao import AdicionalDAO, BordaDAO, MassaDAO, ProdutoDAO, SaborDAO, TamanhoDAO
from servicos.autorizacao import usuario_logado
from servicos.carrinho import obter_carrinho_atual
from servicos.erros import ErroRegraNegocio
from servicos.precos import calcular_preco_item_carrinho

carrinho_bp = Blueprint('carrinho', __name__, url_prefix='/carrinho')


def _itens_com_preco(carrinho):
    itens = []
    subtotal = Decimal('0')
    for item in carrinho.itens:
        try:
            preco_unitario = calcular_preco_item_carrinho(item)
        except ErroRegraNegocio as erro:
            preco_unitario = None
            aviso = str(erro)
        else:
            aviso = None
        linha_total = preco_unitario * item.quantidade if preco_unitario is not None else None
        if linha_total is not None:
            subtotal += linha_total
        itens.append({'item': item, 'preco_unitario': preco_unitario, 'total': linha_total, 'aviso': aviso})
    return itens, subtotal


@carrinho_bp.route('/')
def ver_carrinho():
    usuario = usuario_logado()
    carrinho = obter_carrinho_atual(usuario)
    itens, subtotal = _itens_com_preco(carrinho)
    return render_template('carrinho/carrinho.html', carrinho=carrinho, itens=itens, subtotal=subtotal)


@carrinho_bp.route('/adicionar-produto', methods=['POST'])
def adicionar_produto():
    usuario = usuario_logado()
    carrinho = obter_carrinho_atual(usuario)

    produto_id = request.form.get('produto_id', type=int)
    quantidade = request.form.get('quantidade', default=1, type=int) or 1
    observacoes = (request.form.get('observacoes') or '').strip() or None

    produto = ProdutoDAO.buscar_por_id(produto_id)
    if produto is None or not produto.pode_ser_vendido:  # RN01
        return render_template('erro.html', titulo='Produto indisponível', mensagem='Este produto não está disponível.'), 400

    CarrinhoDAO.adicionar_item(carrinho.id, produto_id=produto.id, quantidade=quantidade, observacoes=observacoes)
    return redirect(url_for('carrinho.ver_carrinho'))


@carrinho_bp.route('/adicionar-pizza', methods=['POST'])
def adicionar_pizza():
    usuario = usuario_logado()
    carrinho = obter_carrinho_atual(usuario)

    tamanho_id = request.form.get('tamanho_id', type=int)
    massa_id = request.form.get('massa_id', type=int) or None
    borda_id = request.form.get('borda_id', type=int) or None
    quantidade = request.form.get('quantidade', default=1, type=int) or 1
    observacoes = (request.form.get('observacoes') or '').strip() or None
    sabores_ids = [int(v) for v in request.form.getlist('sabores_ids') if v]
    adicionais_ids = [int(v) for v in request.form.getlist('adicionais_ids') if v]

    tamanho = TamanhoDAO.buscar_por_id(tamanho_id)
    if tamanho is None:
        return render_template('erro.html', titulo='Tamanho inválido', mensagem='Escolha um tamanho de pizza válido.'), 400

    sabores = SaborDAO.buscar_varios(sabores_ids)
    try:
        from servicos.precos import calcular_preco_pizza
        massa = MassaDAO.buscar_por_id(massa_id) if massa_id else None
        borda = BordaDAO.buscar_por_id(borda_id) if borda_id else None
        adicionais = [(a, 1) for a in AdicionalDAO.buscar_varios(adicionais_ids)]
        calcular_preco_pizza(tamanho, sabores, massa, borda, adicionais)  # valida RN01-RN04 já aqui
    except ErroRegraNegocio as erro:
        return render_template('erro.html', titulo='Não foi possível montar a pizza', mensagem=str(erro)), 400

    CarrinhoDAO.adicionar_item(
        carrinho.id, tamanho_id=tamanho_id, massa_id=massa_id, borda_id=borda_id,
        quantidade=quantidade, observacoes=observacoes,
        sabores_ids=sabores_ids, adicionais=[(a_id, 1) for a_id in adicionais_ids],
    )
    return redirect(url_for('carrinho.ver_carrinho'))


@carrinho_bp.route('/item/<int:item_id>/quantidade', methods=['POST'])
def atualizar_quantidade(item_id):
    quantidade = request.form.get('quantidade', type=int)
    if quantidade is None:
        return render_template('erro.html', titulo='Dados inválidos', mensagem='Quantidade inválida.'), 400
    CarrinhoDAO.atualizar_quantidade(item_id, quantidade)
    return redirect(url_for('carrinho.ver_carrinho'))


@carrinho_bp.route('/item/<int:item_id>/remover', methods=['POST'])
def remover_item(item_id):
    CarrinhoDAO.remover_item(item_id)
    return redirect(url_for('carrinho.ver_carrinho'))
