import os
import secrets
from datetime import timedelta

from dotenv import load_dotenv
from flask import Flask, g, render_template, request
from flask_wtf.csrf import CSRFError
from werkzeug.exceptions import TooManyRequests

load_dotenv()

from config import csrf, db, limiter, migrate

app = Flask(__name__)

app.secret_key = os.environ.get('SECRET_KEY')
if not app.secret_key:
    raise RuntimeError('A variável de ambiente SECRET_KEY é obrigatória.')

database_url = os.environ.get('DATABASE_URL')
if not database_url:
    raise RuntimeError('A variável de ambiente DATABASE_URL é obrigatória.')
# Alguns provedores ainda entregam o esquema antigo "postgres://", que o SQLAlchemy 2 recusa.
if database_url.startswith('postgres://'):
    database_url = 'postgresql://' + database_url[len('postgres://'):]
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
if database_url.startswith('postgresql'):
    if os.environ.get('VERCEL'):
        # Serverless: cada instância é congelada entre requisições, então não vale manter
        # pool próprio; o pooler do Supabase (porta 6543) é quem reaproveita as conexões.
        from sqlalchemy.pool import NullPool
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'poolclass': NullPool}
    else:
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_pre_ping': True}

cookie_secure = (os.environ.get('COOKIE_SECURE', 'false').strip().lower() == 'true')

app.config.update(
    PERMANENT_SESSION_LIFETIME=timedelta(days=7),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_SECURE=cookie_secure,
    SESSION_REFRESH_EACH_REQUEST=True,
    MAX_CONTENT_LENGTH=10 * 1024 * 1024,
    RATELIMIT_STORAGE_URI=os.environ.get('RATELIMIT_STORAGE_URI', 'memory://'),
)

db.init_app(app)
migrate.init_app(app, db)
csrf.init_app(app)
limiter.init_app(app)

# Todos os modelos precisam estar importados antes das migrations enxergarem o schema
# completo. Cada import é usado por algum blueprint/DAO logo abaixo - isto só garante
# que o Alembic veja a tabela mesmo se a ordem de import mudar.
from modelos import (  # noqa: E402,F401
    caixa, carrinho, categoria, configuracao, cupom, endereco, entrega, estoque,
    log, mesa, pagamento, pedido, pizza, produto, usuario,
)

from blueprints.auth_bp import auth_bp  # noqa: E402
from blueprints.cardapio_bp import cardapio_bp  # noqa: E402
from blueprints.carrinho_bp import carrinho_bp  # noqa: E402
from blueprints.pedido_bp import pedido_bp  # noqa: E402
from blueprints.cozinha_bp import cozinha_bp  # noqa: E402
from blueprints.admin_bp import admin_bp  # noqa: E402
from blueprints.endereco_bp import endereco_bp  # noqa: E402
from blueprints.entrega_bp import entrega_bp  # noqa: E402
from blueprints.pagamento_bp import pagamento_bp  # noqa: E402

app.register_blueprint(auth_bp)
app.register_blueprint(cardapio_bp)
app.register_blueprint(carrinho_bp)
app.register_blueprint(pedido_bp)
app.register_blueprint(cozinha_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(endereco_bp)
app.register_blueprint(entrega_bp)
app.register_blueprint(pagamento_bp)

from comandos import registrar_comandos  # noqa: E402

registrar_comandos(app)

from servicos.formatacao import formatar_moeda, rotulo_forma_pagamento, rotulo_status_pedido, rotulo_tipo_pedido  # noqa: E402
from servicos.integracoes import url_google_maps  # noqa: E402

app.jinja_env.filters['moeda'] = formatar_moeda
app.jinja_env.filters['forma_pagamento'] = rotulo_forma_pagamento
app.jinja_env.filters['status_pedido'] = rotulo_status_pedido
app.jinja_env.filters['tipo_pedido'] = rotulo_tipo_pedido
app.jinja_env.globals['url_google_maps'] = url_google_maps


@app.before_request
def preparar_nonce_csp():
    g.csp_nonce = secrets.token_urlsafe(18)


app.jinja_env.globals['csp_nonce'] = lambda: getattr(g, 'csp_nonce', '')


@app.context_processor
def usuario_da_sessao():
    from servicos.autorizacao import usuario_logado
    return {'usuario_logado': usuario_logado()}


@app.after_request
def adicionar_cabecalhos_de_seguranca(resposta):
    nonce = getattr(g, 'csp_nonce', '')
    resposta.headers.setdefault('X-Content-Type-Options', 'nosniff')
    resposta.headers.setdefault('X-Frame-Options', 'SAMEORIGIN')
    resposta.headers.setdefault('Referrer-Policy', 'same-origin')
    resposta.headers.setdefault(
        'Content-Security-Policy',
        "default-src 'self'; "
        f"script-src 'self' 'nonce-{nonce}'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; connect-src 'self'; object-src 'none'; "
        "base-uri 'self'; form-action 'self'; frame-ancestors 'self'",
    )
    return resposta


@app.errorhandler(CSRFError)
def erro_csrf(_erro):
    mensagem = 'Sua sessão de segurança expirou. Atualize a página e tente novamente.'
    if request.path.startswith('/api/'):
        return {'erro': mensagem}, 400
    return mensagem, 400


@app.errorhandler(403)
def acesso_negado(_erro):
    return render_template('erro.html', titulo='Acesso negado', mensagem='Você não tem permissão para acessar esta página.'), 403


@app.errorhandler(404)
def nao_encontrado(_erro):
    return render_template('erro.html', titulo='Não encontrado', mensagem='Página não encontrada.'), 404


@app.errorhandler(TooManyRequests)
def tentativas_demais(_erro):
    mensagem = 'Muitas tentativas. Aguarde alguns minutos e tente novamente.'
    if request.path.startswith('/api/'):
        return {'erro': mensagem}, 429, {'Retry-After': '60'}
    return render_template('erro.html', titulo='Muitas tentativas', mensagem=mensagem), 429


@app.route('/health')
def health():
    return {'status': 'ok'}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=os.environ.get('DEBUG', 'false').lower() == 'true')
