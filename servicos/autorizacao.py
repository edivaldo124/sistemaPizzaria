"""Autorização das rotas protegidas.

A sessão diz quem *afirmou* ser quem; quem decide se esse acesso ainda vale é sempre o
banco, a cada requisição (nunca confiar só no frontend - regra de segurança do
projeto). Duas verificações acontecem juntas: o usuário ainda está ativo, e a
"impressão" da senha guardada no login ainda bate com o hash atual - trocar a senha
invalida em bloco qualquer sessão aberta com a senha anterior.
"""
import hashlib
import hmac
from functools import wraps

from flask import abort, redirect, session, url_for

CHAVE_CREDENCIAL = 'credencial'


def impressao_credencial(senha_hash):
    """Resumo curto e não reversível do hash da senha, guardado na sessão."""
    if not senha_hash:
        return None
    return hashlib.sha256(senha_hash.encode('utf-8')).hexdigest()[:32]


def registrar_credencial(senha_hash):
    session[CHAVE_CREDENCIAL] = impressao_credencial(senha_hash)


def _credencial_confere(senha_hash):
    esperada = impressao_credencial(senha_hash)
    guardada = session.get(CHAVE_CREDENCIAL)
    if esperada is None or guardada is None:
        return False
    return hmac.compare_digest(str(guardada), esperada)


def encerrar_sessao():
    session.clear()


def usuario_logado():
    """Usuário da sessão, revalidado no banco a cada chamada, ou None."""
    from config import db
    from modelos.usuario import Usuario

    usuario_id = session.get('usuario_id')
    if not usuario_id:
        return None

    usuario = db.session.get(Usuario, usuario_id)
    if usuario is None or not usuario.ativo or not _credencial_confere(usuario.senha_hash):
        encerrar_sessao()
        return None
    return usuario


def iniciar_sessao(usuario):
    # Limpa qualquer sessão anterior para evitar fixação de sessão.
    session.clear()
    session['usuario_id'] = usuario.id
    session['tipo_usuario'] = usuario.tipo
    registrar_credencial(usuario.senha_hash)
    session.permanent = True


def login_requerido(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        usuario = usuario_logado()
        if usuario is None:
            return redirect(url_for('auth.pagina_login', proximo=request_path()))
        return view(usuario, *args, **kwargs)
    return wrapper


def request_path():
    from flask import request
    return request.path


def papel_requerido(*tipos_permitidos):
    """Fábrica de decorators: exige um dos papéis informados e injeta o usuário logado.

    Ex.: @papel_requerido(TIPO_GERENTE, TIPO_ADMIN) só deixa gerência passar; qualquer
    outro tipo (inclusive cliente autenticado) recebe 403, nunca um redirecionamento
    silencioso que disfarçaria a negação de acesso como se a rota não existisse.
    """
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            usuario = usuario_logado()
            if usuario is None:
                return redirect(url_for('auth.pagina_login', proximo=request_path()))
            if usuario.tipo not in tipos_permitidos:
                abort(403)
            return view(usuario, *args, **kwargs)
        return wrapper
    return decorator
