class ErroRegraNegocio(Exception):
    """Violação de uma regra de negócio (RN*).

    Vira mensagem de erro para quem fez a requisição - nunca um 500. Rotas capturam
    esta exceção e devolvem a mensagem tal como está: o texto já é escrito pensando em
    quem vai ler (cliente ou funcionário), não em quem vai debugar.
    """
