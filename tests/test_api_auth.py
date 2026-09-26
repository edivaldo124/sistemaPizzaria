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

def test_comando_criar_admin_cria_conta_de_administrador(app, monkeypatch):
    from dao.usuario_dao import UsuarioDAO

    monkeypatch.setattr('comandos.getpass.getpass', lambda _rotulo: 'Forno-a-lenha-2026')
    resultado = app.test_cli_runner().invoke(
        args=['criar-admin', '--nome', 'Dona Maria', '--email', 'Admin@Example.com'],
    )

    assert resultado.exit_code == 0, resultado.output
    usuario = UsuarioDAO.buscar_por_email('admin@example.com')
    assert usuario.tipo == 'admin'
    assert usuario.is_gerencia


def test_comando_criar_admin_recusa_senha_fraca(app, monkeypatch):
    monkeypatch.setattr('comandos.getpass.getpass', lambda _rotulo: '123')
    resultado = app.test_cli_runner().invoke(
        args=['criar-admin', '--nome', 'Dona Maria', '--email', 'admin@example.com'],
    )

    assert resultado.exit_code != 0
    assert 'pelo menos 8' in resultado.output
