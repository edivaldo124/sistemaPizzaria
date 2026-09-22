"""RF31-RF33: baixa automática de estoque a partir dos itens vendidos e aviso de
estoque mínimo. Roda dentro da mesma transação que cria o pedido (servicos/pedidos.py)
- se o pedido falhar, a baixa de estoque tem que falhar junto."""
from config import db
from modelos.estoque import MOVIMENTO_SAIDA, MovimentacaoEstoque, ReceitaItem


def _receitas_do_item(item_pedido):
    if item_pedido.produto_id:
        return ReceitaItem.query.filter_by(produto_id=item_pedido.produto_id).all()
    # Pizza: desconta a receita de cada sabor usado no item (RF32).
    receitas = []
    for sabor_item in item_pedido.sabores:
        receitas.extend(ReceitaItem.query.filter_by(sabor_id=sabor_item.sabor_id).all())
    return receitas


def descontar_estoque_do_pedido(pedido):
    """Chamada dentro da transação de criação do pedido - nunca faz commit sozinha."""
    ingredientes_abaixo_do_minimo = []

    for item in pedido.itens:
        for receita in _receitas_do_item(item):
            ingrediente = receita.ingrediente
            quantidade_consumida = receita.quantidade * item.quantidade
            ingrediente.quantidade_atual -= quantidade_consumida

            db.session.add(MovimentacaoEstoque(
                ingrediente_id=ingrediente.id, tipo=MOVIMENTO_SAIDA,
                quantidade=quantidade_consumida, pedido_id=pedido.id,
                motivo=f'Baixa automática - pedido {pedido.numero}',
            ))

            if ingrediente.abaixo_do_minimo:  # RF33
                ingredientes_abaixo_do_minimo.append(ingrediente)

    return ingredientes_abaixo_do_minimo
