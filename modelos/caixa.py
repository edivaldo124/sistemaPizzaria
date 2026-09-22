from servicos.tempo import agora_utc

from config import db

STATUS_CAIXA_ABERTO = 'aberto'
STATUS_CAIXA_FECHADO = 'fechado'

MOVIMENTO_CAIXA_ENTRADA = 'entrada'
MOVIMENTO_CAIXA_SAIDA = 'saida'
MOVIMENTO_CAIXA_SANGRIA = 'sangria'
MOVIMENTO_CAIXA_VENDA = 'venda'
TIPOS_MOVIMENTO_CAIXA_VALIDOS = (
    MOVIMENTO_CAIXA_ENTRADA, MOVIMENTO_CAIXA_SAIDA, MOVIMENTO_CAIXA_SANGRIA, MOVIMENTO_CAIXA_VENDA,
)


class Caixa(db.Model):
    """Período de caixa: abertura até fechamento (RF30)."""
    __tablename__ = 'caixas'

    id = db.Column(db.Integer, primary_key=True)
    funcionario_abertura_id = db.Column(db.Integer, db.ForeignKey('funcionarios.id'), nullable=False)
    funcionario_fechamento_id = db.Column(db.Integer, db.ForeignKey('funcionarios.id'), nullable=True)
    valor_abertura = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    valor_fechamento_informado = db.Column(db.Numeric(10, 2), nullable=True)
    aberto_em = db.Column(db.DateTime, nullable=False, default=agora_utc)
    fechado_em = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(10), nullable=False, default=STATUS_CAIXA_ABERTO)
    observacoes = db.Column(db.String(500), nullable=True)

    movimentacoes = db.relationship('MovimentacaoCaixa', backref='caixa', cascade='all, delete-orphan')

    __table_args__ = (
        db.Index(
            'uq_caixa_aberto_unico', 'status',
            unique=True,
            postgresql_where=db.text("status = 'aberto'"),
            sqlite_where=db.text("status = 'aberto'"),
        ),
    )

    @property
    def total_movimentado(self):
        entradas = sum(m.valor for m in self.movimentacoes if m.tipo in (MOVIMENTO_CAIXA_ENTRADA, MOVIMENTO_CAIXA_VENDA))
        saidas = sum(m.valor for m in self.movimentacoes if m.tipo in (MOVIMENTO_CAIXA_SAIDA, MOVIMENTO_CAIXA_SANGRIA))
        return entradas - saidas

    @property
    def valor_fechamento_calculado(self):
        return self.valor_abertura + self.total_movimentado


class MovimentacaoCaixa(db.Model):
    """Entrada, saída, sangria ou venda dentro de um caixa aberto (RF30)."""
    __tablename__ = 'movimentacoes_caixa'

    id = db.Column(db.Integer, primary_key=True)
    caixa_id = db.Column(db.Integer, db.ForeignKey('caixas.id'), nullable=False)
    tipo = db.Column(db.String(10), nullable=False)
    valor = db.Column(db.Numeric(10, 2), nullable=False)
    descricao = db.Column(db.String(200), nullable=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedidos.id'), nullable=True)
    funcionario_id = db.Column(db.Integer, db.ForeignKey('funcionarios.id'), nullable=True)
    criado_em = db.Column(db.DateTime, nullable=False, default=agora_utc)

    __table_args__ = (
        db.CheckConstraint(f"tipo in {TIPOS_MOVIMENTO_CAIXA_VALIDOS!r}", name='ck_movimentacao_caixa_tipo'),
    )
