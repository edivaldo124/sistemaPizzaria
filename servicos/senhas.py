"""Hash de senha com Argon2id e validação básica de força.

Argon2id (via argon2-cffi) em vez do PBKDF2 padrão do Werkzeug porque é a exigência de
segurança explícita deste projeto. `PasswordHasher` já usa a variante id por padrão.
"""
import hmac

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError

_ph = PasswordHasher()

SENHAS_COMUNS = {
    '12345678', '123456789', '1234567890', 'password', 'senha123',
    'pizzaria', 'admin123', 'qwerty123',
}

MSG_CONFIRMACAO_DIVERGENTE = 'A senha e a confirmação não são iguais. Digite a mesma senha nos dois campos.'


def gerar_hash(senha_texto_puro):
    return _ph.hash(senha_texto_puro)


def conferir_hash(hash_armazenado, senha_texto_puro):
    if not hash_armazenado:
        return False
    try:
        return _ph.verify(hash_armazenado, senha_texto_puro)
    except (VerifyMismatchError, InvalidHashError):
        return False


def precisa_rehash(hash_armazenado):
    """True quando os parâmetros do Argon2 mudaram desde que o hash foi gerado."""
    return _ph.check_needs_rehash(hash_armazenado)


def erro_validacao_senha(senha, *identificadores):
    """Retorna uma mensagem quando a senha é curta, comum ou igual a um identificador."""
    if len(senha or '') < 8:
        return 'A senha deve ter pelo menos 8 caracteres.'

    normalizada = senha.casefold()
    if normalizada in SENHAS_COMUNS:
        return 'Escolha uma senha menos comum.'

    identificadores_validos = {
        (valor or '').strip().casefold() for valor in identificadores if (valor or '').strip()
    }
    if normalizada in identificadores_validos:
        return 'A senha não pode ser igual ao seu nome ou e-mail.'
    return None


def erro_confirmacao_senha(senha, confirmacao):
    if not hmac.compare_digest((senha or '').encode('utf-8'), (confirmacao or '').encode('utf-8')):
        return MSG_CONFIRMACAO_DIVERGENTE
    return None
