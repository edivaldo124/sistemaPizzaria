"""Filtros de exibição usados pelos templates - formatação, nunca regra de negócio."""


def formatar_moeda(valor):
    if valor is None:
        return 'R$ 0,00'
    texto = f'{float(valor):,.2f}'.replace(',', '_').replace('.', ',').replace('_', '.')
    return f'R$ {texto}'


ROTULOS_FORMA_PAGAMENTO = {
    'dinheiro': 'Dinheiro',
    'pix': 'Pix',
    'cartao': 'Cartão',
    'presencial': 'Presencial',
}

ROTULOS_STATUS_PEDIDO = {
    'recebido': 'Recebido',
    'confirmado': 'Confirmado',
    'em_preparo': 'Em preparo',
    'pronto': 'Pronto',
    'saiu_para_entrega': 'Saiu para entrega',
    'entregue': 'Entregue',
    'cancelado': 'Cancelado',
}

ROTULOS_TIPO_PEDIDO = {
    'delivery': 'Delivery',
    'retirada': 'Retirada no balcão',
    'salao': 'Consumo no salão',
}


def rotulo_forma_pagamento(forma):
    return ROTULOS_FORMA_PAGAMENTO.get(forma, forma)


def rotulo_status_pedido(status):
    return ROTULOS_STATUS_PEDIDO.get(status, status)


def rotulo_tipo_pedido(tipo):
    return ROTULOS_TIPO_PEDIDO.get(tipo, tipo)
