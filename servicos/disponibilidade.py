"""RF27/RN18: horário de funcionamento e valor mínimo do pedido."""
from modelos.configuracao import ConfiguracaoLoja, FORA_HORARIO_AGENDAR
from servicos.erros import ErroRegraNegocio


def dentro_do_horario(config, agora):
    if config.horario_abertura is None or config.horario_fechamento is None:
        return True  # sem horário configurado = atende o tempo todo
    hora_atual = agora.time()
    if config.horario_abertura <= config.horario_fechamento:
        return config.horario_abertura <= hora_atual <= config.horario_fechamento
    # horário que cruza a meia-noite (ex.: abre 18h, fecha 1h)
    return hora_atual >= config.horario_abertura or hora_atual <= config.horario_fechamento


def validar_horario_pedido(agora, horario_agendado=None):
    """Levanta ErroRegraNegocio quando o pedido não pode ser feito agora.

    Se `horario_agendado` for informado e a loja permitir agendamento fora do
    horário, o pedido é aceito - a checagem de horário nesse caso é responsabilidade
    de quem for iniciar o preparo, não desta função.
    """
    config = ConfiguracaoLoja.obter()
    if dentro_do_horario(config, agora):
        return
    if horario_agendado is not None and config.fora_horario == FORA_HORARIO_AGENDAR:
        return
    raise ErroRegraNegocio('A pizzaria está fechada no momento. Tente novamente durante o horário de atendimento.')


def validar_valor_minimo(subtotal):
    config = ConfiguracaoLoja.obter()
    if subtotal < config.valor_minimo_pedido:
        raise ErroRegraNegocio(
            f'O valor mínimo do pedido é R$ {config.valor_minimo_pedido:.2f}.'
        )
