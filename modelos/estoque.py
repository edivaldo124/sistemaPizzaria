from datetime import datetime, timezone

from config import db

MOVIMENTO_ENTRADA = 'entrada'
MOVIMENTO_SAIDA = 'saida'
MOVIMENTO_AJUSTE = 'ajuste'
TIPOS_MOVIMENTO_VALIDOS = (MOVIMENTO_ENTRADA, MOVIMENTO_SAIDA, MOVIMENTO_AJUSTE)


class Ingrediente(db.Model):
    """Ingrediente controlado em estoque (RF31). A quantidade atual mora aqui mesmo -
    uma tabela 'Estoque' 1:1 separada só duplicaria a chave sem ganhar nada."""
    __tablename__ = 'ingredientes'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, unique=True)
    unidade_medida = db.Column(db.String(10), nullable=False, default='un')  # un, kg, g, l, ml
    quantidade_atual = db.Column(db.Numeric(10, 3), nullable=False, default=0)
    estoque_minimo = db.Column(db.Numeric(10, 3), nullable=False, default=0)  # RF33
    ativo = db.Column(db.Boolean, nullable=False, default=True)

    def __str__(self):
        return self.nome

    @property
    def abaixo_do_minimo(self):
        return self.quantidade_atual <= self.estoque_minimo


class ReceitaItem(db.Model):
    """Quanto de um ingrediente um produto ou sabor consome (RF32).

    Exatamente um entre produto_id/sabor_id é preenchido - a receita é sempre de um
    item vendável específico, nunca dos dois ao mesmo tempo.
    """
    __tablename__ = 'receita_itens'

    id = db.Column(db.Integer, primary_key=True)
    produto_id = db.Column(db.Integer, db.ForeignKey('produtos.id'), nullable=True)
    sabor_id = db.Column(db.Integer, db.ForeignKey('sabores.id'), nullable=True)
    ingrediente_id = db.Column(db.Integer, db.ForeignKey('ingredientes.id'), nullable=False)
    quantidade = db.Column(db.Numeric(10, 3), nullable=False)

    ingrediente = db.relationship('Ingrediente')

    __table_args__ = (
        db.CheckConstraint(
            '(produto_id IS NOT NULL AND sabor_id IS NULL) OR (produto_id IS NULL AND sabor_id IS NOT NULL)',
            name='ck_receita_item_produto_xor_sabor',
        ),
    )


class MovimentacaoEstoque(db.Model):
    """Histórico de entradas/saídas/ajustes de estoque (RF31, RF32)."""
    __tablename__ = 'movimentacoes_estoque'

    id = db.Column(db.Integer, primary_key=True)
    ingrediente_id = db.Column(db.Integer, db.ForeignKey('ingredientes.id'), nullable=False)
    tipo = db.Column(db.String(10), nullable=False)
    quantidade = db.Column(db.Numeric(10, 3), nullable=False)
    motivo = db.Column(db.String(200), nullable=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedidos.id'), nullable=True)
    funcionario_id = db.Column(db.Integer, db.ForeignKey('funcionarios.id'), nullable=True)
    criado_em = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    ingrediente = db.relationship('Ingrediente')

    __table_args__ = (
        db.CheckConstraint(f"tipo in {TIPOS_MOVIMENTO_VALIDOS!r}", name='ck_movimentacao_estoque_tipo'),
    )
