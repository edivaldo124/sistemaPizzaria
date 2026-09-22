from flask import Blueprint, render_template

from dao.catalogo_dao import (
    AdicionalDAO, BordaDAO, CategoriaDAO, MassaDAO, ProdutoDAO, SaborDAO, TamanhoDAO,
)

cardapio_bp = Blueprint('cardapio', __name__)


@cardapio_bp.route('/')
def pagina_cardapio():
    """RF05/RF06: cardápio público com categorias e produtos disponíveis."""
    categorias = CategoriaDAO.listar()
    produtos = ProdutoDAO.listar_cardapio()
    return render_template('cardapio/cardapio.html', categorias=categorias, produtos=produtos)


@cardapio_bp.route('/montar-pizza')
def montar_pizza():
    """RF07-RF09: tela de montagem de pizza (tamanho, sabores, massa, borda, adicionais)."""
    return render_template(
        'cardapio/montar_pizza.html',
        tamanhos=TamanhoDAO.listar(),
        sabores=SaborDAO.listar_cardapio(),
        massas=MassaDAO.listar(),
        bordas=BordaDAO.listar(),
        adicionais=AdicionalDAO.listar(),
    )
