from servicos.tempo import agora_utc

from config import db

STATUS_ENTREGA_AGUARDANDO = 'aguardando'
STATUS_ENTREGA_EM_ROTA = 'em_rota'
STATUS_ENTREGA_ENTREGUE = 'entregue'


class RegiaoEntrega(db.Model):
    """Bairro/região atendida e sua taxa de entrega (RF26)."""
    __tablename__ = 'regioes_entrega'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, unique=True)
    taxa_entrega = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    tempo_estimado_min = db.Column(db.Integer, nullable=True)
    ativo = db.Column(db.Boolean, nullable=False, default=True)


class Entregador(db.Model):
    """Perfil de entrega vinculado a um usuário do tipo entregador (RF24)."""
    __tablename__ = 'entregadores'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), unique=True, nullable=False)
    veiculo = db.Column(db.String(60), nullable=True)
    placa = db.Column(db.String(10), nullable=True)
    ativo = db.Column(db.Boolean, nullable=False, default=True)

    usuario = db.relationship('Usuario')


class Entrega(db.Model):
    """Acompanhamento da entrega de um pedido (RF24, RF25)."""
    __tablename__ = 'entregas'

    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedidos.id'), unique=True, nullable=False)
    entregador_id = db.Column(db.Integer, db.ForeignKey('entregadores.id'), nullable=True)
    status = db.Column(db.String(20), nullable=False, default=STATUS_ENTREGA_AGUARDANDO)
    saiu_em = db.Column(db.DateTime, nullable=True)
    entregue_em = db.Column(db.DateTime, nullable=True)
    criado_em = db.Column(db.DateTime, nullable=False, default=agora_utc)

    entregador = db.relationship('Entregador')
