"""RF34/RF35: relatórios de vendas por período, produto, forma de pagamento, sabor e
horário. Só lê dados já persistidos - nenhuma regra de negócio nova mora aqui."""
from collections import defaultdict
from decimal import Decimal

from dao.pedido_dao import PedidoDAO
from modelos.pedido import STATUS_CANCELADO


def relatorio_vendas(inicio, fim):
    pedidos = [p for p in PedidoDAO.listar_por_periodo(inicio, fim, apenas_finalizados=False) if p.status != STATUS_CANCELADO]

    total_vendas = sum((p.total for p in pedidos), Decimal('0'))

    por_forma_pagamento = defaultdict(lambda: Decimal('0'))
    for pedido in pedidos:
        pagamento = pedido.pagamento_atual
        forma = pagamento.forma if pagamento else 'não informada'
        por_forma_pagamento[forma] += pedido.total

    por_produto = defaultdict(lambda: {'quantidade': 0, 'total': Decimal('0')})
    por_sabor = defaultdict(lambda: {'quantidade': 0})
    por_hora = defaultdict(int)

    for pedido in pedidos:
        por_hora[pedido.criado_em.hour] += 1
        for item in pedido.itens:
            por_produto[item.descricao]['quantidade'] += item.quantidade
            por_produto[item.descricao]['total'] += item.subtotal
            for sabor_item in item.sabores:
                por_sabor[sabor_item.sabor.nome]['quantidade'] += item.quantidade

    return {
        'quantidade_pedidos': len(pedidos),
        'total_vendas': total_vendas,
        'por_forma_pagamento': dict(por_forma_pagamento),
        'por_produto': dict(sorted(por_produto.items(), key=lambda kv: kv[1]['total'], reverse=True)),
        'por_sabor': dict(sorted(por_sabor.items(), key=lambda kv: kv[1]['quantidade'], reverse=True)),
        'por_hora': dict(sorted(por_hora.items())),
    }
