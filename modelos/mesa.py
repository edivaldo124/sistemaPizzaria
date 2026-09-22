from servicos.tempo import agora_utc

from config import db

STATUS_COMANDA_ABERTA = 'aberta'
STATUS_COMANDA_FECHADA = 'fechada'


class Mesa(db.Model):
    """Mesa do salão (RF29)."""
    __tablename__ = 'mesas'

    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.Integer, nullable=False, unique=True)
    capacidade = db.Column(db.Integer, nullable=True)
    ativo = db.Column(db.Boolean, nullable=False, default=True)


class Comanda(db.Model):
    """Comanda aberta para uma mesa (RF29, RN15, RN16)."""
    __tablename__ = 'comandas'

    id = db.Column(db.Integer, primary_key=True)
    mesa_id = db.Column(db.Integer, db.ForeignKey('mesas.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default=STATUS_COMANDA_ABERTA)
    aberta_em = db.Column(db.DateTime, nullable=False, default=agora_utc)
    fechada_em = db.Column(db.DateTime, nullable=True)
    funcionario_abertura_id = db.Column(db.Integer, db.ForeignKey('funcionarios.id'), nullable=True)

    mesa = db.relationship('Mesa')
    pedidos = db.relationship('Pedido', backref='comanda')

    __table_args__ = (
        # RN16: só uma comanda ABERTA por mesa ao mesmo tempo. Índice parcial (Postgres/
        # SQLite aceitam WHERE em índice único) em vez de UniqueConstraint simples,
        # porque comandas FECHADAS da mesma mesa são histórico e podem se repetir.
        db.Index(
            'uq_comanda_aberta_por_mesa', 'mesa_id',
            unique=True,
            postgresql_where=db.text("status = 'aberta'"),
            sqlite_where=db.text("status = 'aberta'"),
        ),
    )
