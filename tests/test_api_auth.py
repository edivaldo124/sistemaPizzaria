def _csrf(client):
    return client.get('/api/auth/csrf').get_json()['csrf_token']


def test_api_register_cria_sessao_e_retorna_redirect(client):
    token = _csrf(client)
    resposta = client.post(
        '/api/auth/register',
        json={
            'nome': 'Cliente API',
            'email': 'api@example.com',
            'senha': 'SenhaForte123!',
            'confirmacao_senha': 'SenhaForte123!',
        },
        headers={'X-CSRFToken': token},
    )

    assert resposta.status_code == 201
    assert resposta.get_json()['redirect'] == '/cardapio'
    assert resposta.get_json()['usuario']['email'] == 'api@example.com'


def test_api_login_rejeita_credencial_invalida(client, db):
    token = _csrf(client)
    resposta = client.post(
        '/api/auth/login',
        json={'email': 'ausente@example.com', 'senha': 'incorreta'},
        headers={'X-CSRFToken': token},
    )

    assert resposta.status_code == 401
    assert resposta.get_json()['erro'] == 'E-mail ou senha inválidos.'