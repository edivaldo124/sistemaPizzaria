import servicos.integracoes as integracoes


def test_gmail_configurado_aceita_oauth_google(monkeypatch):
    monkeypatch.delenv('GMAIL_ACCESS_TOKEN', raising=False)
    monkeypatch.setenv('GMAIL_FROM', 'pedidos@teste.com')
    monkeypatch.setenv('GOOGLE_CLIENT_ID', 'client-id')
    monkeypatch.setenv('GOOGLE_CLIENT_SECRET', 'client-secret')
    monkeypatch.setenv('GOOGLE_REFRESH_TOKEN', 'refresh-token')

    assert integracoes.gmail_configurado() is True


def test_enviar_email_gmail_usa_token_oauth_refresh(monkeypatch):
    monkeypatch.delenv('GMAIL_ACCESS_TOKEN', raising=False)
    monkeypatch.setenv('GMAIL_FROM', 'pedidos@teste.com')
    monkeypatch.setenv('GOOGLE_CLIENT_ID', 'client-id')
    monkeypatch.setenv('GOOGLE_CLIENT_SECRET', 'client-secret')
    monkeypatch.setenv('GOOGLE_REFRESH_TOKEN', 'refresh-token')

    captured = {}

    def fake_json_request(url, **kwargs):
        if url.endswith('/messages/send'):
            captured['auth'] = kwargs['headers']['Authorization']
            return {'id': 'abc123'}
        raise AssertionError(f'URL inesperada: {url}')

    monkeypatch.setattr(integracoes, '_json_request', fake_json_request)
    monkeypatch.setattr(integracoes, '_obter_access_token_google_oauth', lambda: 'token-azure')

    resposta = integracoes.enviar_email_gmail(
        destinatario='cliente@teste.com',
        assunto='Pedido confirmado',
        corpo='Olá',
    )

    assert resposta == {'id': 'abc123'}
    assert captured['auth'] == 'Bearer token-azure'


def test_enderecos_publicos_tem_padrao_sem_variavel_de_ambiente(monkeypatch):
    monkeypatch.delenv('GOOGLE_MAPS_WEB_URL', raising=False)
    monkeypatch.delenv('GMAIL_API_URL', raising=False)

    class Endereco:
        logradouro, numero, bairro, cidade, uf, cep = 'Rua A', '10', 'Centro', 'Palmas', 'TO', ''

    assert integracoes.url_google_maps(Endereco()).startswith('https://www.google.com/maps/dir/?api=1')
    assert integracoes._config('GMAIL_API_URL') == 'https://gmail.googleapis.com/gmail/v1'
