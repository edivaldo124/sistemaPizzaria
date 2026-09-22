from flask import Blueprint, jsonify, redirect, render_template, request, url_for
from flask_wtf.csrf import generate_csrf

from config import limiter
from dao.usuario_dao import UsuarioDAO
from servicos.autorizacao import encerrar_sessao, iniciar_sessao, usuario_logado
from servicos.carrinho import migrar_carrinho_do_login
from servicos.senhas import erro_confirmacao_senha, erro_validacao_senha

auth_bp = Blueprint('auth', __name__)


def _dados_json():
    return request.get_json(silent=True) or {}


def _usuario_json(usuario):
    return {'id': usuario.id, 'nome': usuario.nome, 'email': usuario.email, 'tipo': usuario.tipo}


@auth_bp.get('/api/auth/csrf')
def api_csrf():
    return jsonify({'csrf_token': generate_csrf()})


@auth_bp.post('/api/auth/register')
@limiter.limit('10 per minute')
def api_register():
    dados = _dados_json()
    nome = (dados.get('nome') or '').strip()
    email = (dados.get('email') or '').strip().lower()
    telefone = (dados.get('telefone') or '').strip() or None
    senha = dados.get('senha') or ''
    confirmacao = dados.get('confirmacao_senha') or dados.get('confirmacao') or ''

    if not nome or not email:
        return jsonify({'erro': 'Preencha nome e e-mail.'}), 400

    erro_senha = erro_validacao_senha(senha, nome, email) or erro_confirmacao_senha(senha, confirmacao)
    if erro_senha:
        return jsonify({'erro': erro_senha}), 400
    if UsuarioDAO.buscar_por_email(email):
        return jsonify({'erro': 'Este e-mail já está cadastrado.'}), 409

    usuario = UsuarioDAO.criar_cliente(nome=nome, email=email, senha=senha, telefone=telefone)
    migrar_carrinho_do_login(usuario)
    iniciar_sessao(usuario)
    return jsonify({'usuario': _usuario_json(usuario), 'redirect': url_for('cardapio.pagina_cardapio')}), 201


@auth_bp.post('/api/auth/login')
@limiter.limit('10 per minute')
def api_login():
    dados = _dados_json()
    email = (dados.get('email') or '').strip().lower()
    senha = dados.get('senha') or ''
    usuario = UsuarioDAO.autenticar(email, senha)
    if usuario is None:
        return jsonify({'erro': 'E-mail ou senha inválidos.'}), 401

    if usuario.tipo == 'cliente':
        migrar_carrinho_do_login(usuario)
    iniciar_sessao(usuario)
    destino = {
        'cliente': url_for('cardapio.pagina_cardapio'),
        'cozinha': url_for('cozinha.fila_pedidos'),
    }.get(usuario.tipo, url_for('admin.painel'))
    return jsonify({'usuario': _usuario_json(usuario), 'redirect': destino})


@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit('10 per minute', methods=['POST'])
def pagina_login():
    if request.method == 'POST':
        email = (request.form.get('email') or '').strip().lower()
        senha = request.form.get('senha') or ''

        usuario = UsuarioDAO.autenticar(email, senha)
        if usuario is None:
            return render_template('auth/login.html', erro='E-mail ou senha inválidos.', email=email), 401

        if usuario.tipo == 'cliente':
            migrar_carrinho_do_login(usuario)
        iniciar_sessao(usuario)

        if usuario.tipo == 'cliente':
            return redirect(url_for('cardapio.pagina_cardapio'))
        if usuario.tipo == 'cozinha':
            return redirect(url_for('cozinha.fila_pedidos'))
        return redirect(url_for('admin.painel'))

    return render_template('auth/login.html')


@auth_bp.route('/cadastro', methods=['GET', 'POST'])
@limiter.limit('10 per minute', methods=['POST'])
def pagina_cadastro():
    """RF01: cadastro de cliente. Funcionários são cadastrados pelo admin (RF02)."""
    if request.method == 'POST':
        nome = (request.form.get('nome') or '').strip()
        email = (request.form.get('email') or '').strip().lower()
        telefone = (request.form.get('telefone') or '').strip() or None
        senha = request.form.get('senha') or ''
        confirmacao = request.form.get('confirmacao_senha') or ''

        contexto = {'nome': nome, 'email': email, 'telefone': telefone}

        if not nome or not email:
            return render_template('auth/cadastro.html', erro='Preencha nome e e-mail.', **contexto), 400

        erro_senha = erro_validacao_senha(senha, nome, email) or erro_confirmacao_senha(senha, confirmacao)
        if erro_senha:
            return render_template('auth/cadastro.html', erro=erro_senha, **contexto), 400

        if UsuarioDAO.buscar_por_email(email):
            return render_template('auth/cadastro.html', erro='Este e-mail já está cadastrado.', **contexto), 400

        usuario = UsuarioDAO.criar_cliente(nome=nome, email=email, senha=senha, telefone=telefone)
        migrar_carrinho_do_login(usuario)
        iniciar_sessao(usuario)
        return redirect(url_for('cardapio.pagina_cardapio'))

    return render_template('auth/cadastro.html')


@auth_bp.route('/logout', methods=['POST'])
def logout():
    encerrar_sessao()
    return redirect(url_for('cardapio.pagina_cardapio'))


@auth_bp.route('/minha-conta')
def minha_conta():
    usuario = usuario_logado()
    if usuario is None:
        return redirect(url_for('auth.pagina_login'))
    return render_template('auth/minha_conta.html', usuario=usuario)
