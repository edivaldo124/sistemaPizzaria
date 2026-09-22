from servicos.tempo import agora_utc

from config import db

FORMA_DINHEIRO = 'dinheiro'
FORMA_PIX = 'pix'
FORMA_CARTAO = 'cartao'
FORMA_PRESENCIAL = 'presencial'
FORMAS_PAGAMENTO_VALIDAS = (FORMA_DINHEIRO, FORMA_PIX, FORMA_CARTAO, FORMA_PRESENCIAL)

STATUS_PENDENTE = 'pendente'
STATUS_APROVADO = 'aprovado'
STATUS_RECUSADO = 'recusado'
STATUS_ESTORNADO = 'estornado'
STATUS_PAGAMENTO_VALIDOS = (STATUS_PENDENTE, STATUS_APROVADO, STATUS_RECUSADO, STATUS_ESTORNADO)


class Pagamento(db.Model):
    """Pagamento de um pedido (RF14-RF16). Nunca guarda dados completos de cartão -
    só forma, status e valor; a maquininha/gateway ficam fora do escopo do MVP."""
    __tablename__ = 'pagamentos'

    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedidos.id'), nullable=False)
    forma = db.Column(db.String(12), nullable=False)
    status = db.Column(db.String(12), nullable=False, default=STATUS_PENDENTE)
    valor = db.Column(db.Numeric(10, 2), nullable=False)
    troco_para = db.Column(db.Numeric(10, 2), nullable=True)  # RF15, só faz sentido para dinheiro
    referencia_externa = db.Column(db.String(120), nullable=True)  # p/ integração futura (RF23)
    criado_em = db.Column(db.DateTime, nullable=False, default=agora_utc)
    atualizado_em = db.Column(
        db.DateTime, nullable=False,
        default=agora_utc,
        onupdate=agora_utc,
    )

    __table_args__ = (
        db.CheckConstraint(f"forma in {FORMAS_PAGAMENTO_VALIDAS!r}", name='ck_pagamento_forma_valida'),
        db.CheckConstraint(f"status in {STATUS_PAGAMENTO_VALIDOS!r}", name='ck_pagamento_status_valido'),
    )
