"""Resolve o carrinho da requisição atual: do cliente logado, ou de um visitante
identificado por uma chave aleatória guardada na sessão assinada do Flask (nunca um
cookie próprio, então não há nada novo para o CSRF/segurança da sessão proteger)."""
import secrets

from flask import session

from dao.carrinho_dao import CarrinhoDAO

CHAVE_SESSAO_CARRINHO = 'carrinho_chave'


def obter_carrinho_atual(usuario):
    if usuario is not None and usuario.tipo == 'cliente':
        return CarrinhoDAO.obter_ou_criar(cliente_id=usuario.cliente.id)

    chave = session.get(CHAVE_SESSAO_CARRINHO)
    if not chave:
        chave = secrets.token_urlsafe(16)
        session[CHAVE_SESSAO_CARRINHO] = chave
    return CarrinhoDAO.obter_ou_criar(session_key=chave)


def migrar_carrinho_do_login(usuario):
    chave = session.pop(CHAVE_SESSAO_CARRINHO, None)
    if chave and usuario.tipo == 'cliente':
        CarrinhoDAO.migrar_carrinho_visitante_para_cliente(chave, usuario.cliente.id)
