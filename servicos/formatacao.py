"""Filtros de exibição usados pelos templates - formatação, nunca regra de negócio."""
from datetime import timedelta, timezone

# Tocantins não tem horário de verão: UTC-3 fixo.
FUSO_LOCAL = timezone(timedelta(hours=-3), 'BRT')


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


def formatar_data_hora(valor, formato='%d/%m/%Y %H:%M'):
    """Converte o timestamp UTC naive do banco (ver servicos/tempo.py) para hora local."""
    if valor is None:
        return '-'
    if valor.tzinfo is None:
        valor = valor.replace(tzinfo=timezone.utc)
    return valor.astimezone(FUSO_LOCAL).strftime(formato)


def etapas_do_pedido(pedido):
    """Sequência de status que o pedido percorre, conforme o tipo (RN13/RN14)."""
    from modelos.pedido import FLUXO_PEDIDO_POR_TIPO, FLUXO_RETIRADA_OU_SALAO
    return FLUXO_PEDIDO_POR_TIPO.get(pedido.tipo, FLUXO_RETIRADA_OU_SALAO)
