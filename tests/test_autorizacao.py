"""servicos/autorizacao.py: controle de acesso por papel, nunca confiando só no
frontend - toda checagem é revalidada no backend a cada requisição."""
from dao.usuario_dao import UsuarioDAO


def test_rota_de_cozinha_bloqueada_para_cliente(client, db):
    UsuarioDAO.criar_cliente(nome='Ana', email='ana@example.com', senha='senha-forte-123')
    client.post('/login', data={'email': 'ana@example.com', 'senha': 'senha-forte-123'})

    resposta = client.get('/cozinha/')
    assert resposta.status_code == 403


def test_rota_de_cozinha_redireciona_anonimo_para_login(client, db):
    resposta = client.get('/cozinha/', follow_redirects=False)
    assert resposta.status_code == 302
    assert '/login' in resposta.headers['Location']


def test_papel_correto_acessa_a_rota(client, db):
    UsuarioDAO.criar_funcionario(nome='Beto', email='beto@pizzaria.com', senha='senha-forte-123', tipo='cozinha')
    client.post('/login', data={'email': 'beto@pizzaria.com', 'senha': 'senha-forte-123'})

    resposta = client.get('/cozinha/')
    assert resposta.status_code == 200


def test_trocar_senha_invalida_sessao_aberta(client, db):
    """A 'impressão de credencial' guardada na sessão precisa bater com o hash atual."""
    usuario = UsuarioDAO.criar_cliente(nome='Ana', email='ana@example.com', senha='senha-forte-123')
    client.post('/login', data={'email': 'ana@example.com', 'senha': 'senha-forte-123'})

    # Confirma que a sessão está válida antes da troca.
    resposta = client.get('/minha-conta')
    assert resposta.status_code == 200

    usuario.set_senha('outra-senha-ainda-mais-forte')
    db.session.commit()

    # A mesma sessão (cookie) não deve mais autenticar - a "impressão" antiga não bate
    # com o hash novo, então a rota deve tratar como anônimo e redirecionar.
    resposta = client.get('/minha-conta', follow_redirects=False)
    assert resposta.status_code == 302


def test_usuario_inativo_perde_acesso_mesmo_com_sessao_valida(client, db):
    usuario = UsuarioDAO.criar_cliente(nome='Ana', email='ana@example.com', senha='senha-forte-123')
    client.post('/login', data={'email': 'ana@example.com', 'senha': 'senha-forte-123'})

    UsuarioDAO.definir_ativo(usuario.id, False)

    resposta = client.get('/minha-conta', follow_redirects=False)
    assert resposta.status_code == 302
