from config import db

DESCONTO_PERCENTUAL = 'percentual'
DESCONTO_FIXO = 'fixo'
TIPOS_DESCONTO_VALIDOS = (DESCONTO_PERCENTUAL, DESCONTO_FIXO)


class Cupom(db.Model):
    """Cupom de desconto (RF28, RN07, RN08)."""
    __tablename__ = 'cupons'

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(40), nullable=False, unique=True)
    tipo_desconto = db.Column(db.String(20), nullable=False, default=DESCONTO_PERCENTUAL)
    valor = db.Column(db.Numeric(10, 2), nullable=False)
    valor_minimo_pedido = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    validade_inicio = db.Column(db.DateTime, nullable=True)
    validade_fim = db.Column(db.DateTime, nullable=True)
    quantidade_disponivel = db.Column(db.Integer, nullable=True)  # None = ilimitado
    quantidade_utilizada = db.Column(db.Integer, nullable=False, default=0)
    ativo = db.Column(db.Boolean, nullable=False, default=True)

    __table_args__ = (
        db.CheckConstraint(f"tipo_desconto in {TIPOS_DESCONTO_VALIDOS!r}", name='ck_cupom_tipo_desconto'),
    )

    def esta_valido(self, agora, valor_pedido):
        if not self.ativo:
            return False
        if self.validade_inicio and agora < self.validade_inicio:
            return False
        if self.validade_fim and agora > self.validade_fim:
            return False
        if self.quantidade_disponivel is not None and self.quantidade_utilizada >= self.quantidade_disponivel:
            return False
        if valor_pedido < self.valor_minimo_pedido:
            return False
        return True

    def calcular_desconto(self, valor_pedido):
        if self.tipo_desconto == DESCONTO_PERCENTUAL:
            return (valor_pedido * self.valor) / 100
        return min(self.valor, valor_pedido)
