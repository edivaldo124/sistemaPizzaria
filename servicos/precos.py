"""Motor de preços - único lugar do sistema que decide quanto um item custa.

O preço final é SEMPRE calculado aqui a partir do que está cadastrado no banco. O
frontend pode mandar um preço junto do formulário só para exibição otimista; ele nunca
é usado para gravar nada (RN da seção "Pedidos" do projeto).
"""
from decimal import Decimal, ROUND_HALF_UP

from modelos.configuracao import ConfiguracaoLoja, REGRA_PRECO_MEDIA
from servicos.erros import ErroRegraNegocio


def arredondar(valor):
    return Decimal(valor).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def _preco_adicionais(adicionais):
    total = Decimal('0')
    for adicional, quantidade in adicionais or []:
        if not (adicional.ativo and adicional.disponivel):
            raise ErroRegraNegocio(f'{adicional.nome} não está disponível no momento.')
        if quantidade <= 0:
            raise ErroRegraNegocio('Quantidade de adicional inválida.')
        total += adicional.preco * quantidade
    return total


def calcular_preco_sabores(tamanho, sabores):
    """RN02: respeita o máximo de sabores do tamanho. RN03: preço configurável para
    pizza com mais de um sabor (maior valor entre os sabores, ou a média)."""
    if not sabores:
        raise ErroRegraNegocio('Escolha ao menos um sabor para a pizza.')
    if len(sabores) > tamanho.max_sabores:
        raise ErroRegraNegocio(f'{tamanho.nome} aceita no máximo {tamanho.max_sabores} sabor(es).')

    precos = []
    for sabor in sabores:
        if not sabor.pode_ser_vendido:
            raise ErroRegraNegocio(f'{sabor.nome} não está disponível no momento.')
        preco = sabor.preco_no_tamanho(tamanho.id)
        if preco is None:
            raise ErroRegraNegocio(f'{sabor.nome} não tem preço cadastrado para o tamanho {tamanho.nome}.')
        precos.append(preco)

    if len(precos) == 1:
        return precos[0]

    config = ConfiguracaoLoja.obter()
    if config.regra_preco_multiplos_sabores == REGRA_PRECO_MEDIA:
        return sum(precos) / len(precos)
    return max(precos)


def calcular_preco_pizza(tamanho, sabores, massa=None, borda=None, adicionais=None):
    if not tamanho.ativo:
        raise ErroRegraNegocio(f'Tamanho {tamanho.nome} não está disponível.')
    preco = calcular_preco_sabores(tamanho, sabores)
    if massa is not None:
        if not massa.ativo:
            raise ErroRegraNegocio(f'{massa.nome} não está disponível.')
        preco += massa.preco_adicional
    if borda is not None:
        if not borda.ativo:
            raise ErroRegraNegocio(f'{borda.nome} não está disponível.')
        preco += borda.preco_adicional
    preco += _preco_adicionais(adicionais)
    return arredondar(preco)


def calcular_preco_produto(produto, adicionais=None):
    if not produto.pode_ser_vendido:
        raise ErroRegraNegocio(f'{produto.nome} não está disponível no momento.')
    preco = produto.preco + _preco_adicionais(adicionais)
    return arredondar(preco)


def calcular_preco_item_carrinho(item):
    """Preço unitário atual de um ItemCarrinho (produto simples ou pizza montada)."""
    adicionais = [(a.adicional, a.quantidade) for a in item.adicionais]
    if item.produto_id:
        return calcular_preco_produto(item.produto, adicionais=adicionais)
    sabores = [s.sabor for s in item.sabores]
    return calcular_preco_pizza(item.tamanho, sabores, item.massa, item.borda, adicionais=adicionais)


def calcular_totais(itens, taxa_entrega=None, cupom=None, agora=None):
    """itens: lista de (preco_unitario, quantidade). Retorna dict com subtotal,
    desconto, taxa_entrega e total - sempre em Decimal arredondado a centavos."""
    from servicos.tempo import agora_utc

    taxa_entrega = taxa_entrega if taxa_entrega is not None else Decimal('0')
    agora = agora or agora_utc()

    subtotal = sum((preco * quantidade for preco, quantidade in itens), Decimal('0'))

    desconto = Decimal('0')
    if cupom is not None:
        if not cupom.esta_valido(agora, subtotal):
            raise ErroRegraNegocio('Cupom inválido, expirado, esgotado ou abaixo do valor mínimo.')
        desconto = cupom.calcular_desconto(subtotal)

    total = subtotal - desconto + taxa_entrega
    if total < 0:
        total = Decimal('0')

    return {
        'subtotal': arredondar(subtotal),
        'desconto': arredondar(desconto),
        'taxa_entrega': arredondar(taxa_entrega),
        'total': arredondar(total),
    }
