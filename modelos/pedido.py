import uuid
from servicos.tempo import agora_utc

from config import db

TIPO_DELIVERY = 'delivery'
TIPO_RETIRADA = 'retirada'
TIPO_SALAO = 'salao'
TIPOS_PEDIDO_VALIDOS = (TIPO_DELIVERY, TIPO_RETIRADA, TIPO_SALAO)

# RF21/RN13: fluxo normal recebido -> confirmado -> em_preparo -> pronto ->
# saiu_para_entrega -> entregue. RN14: retirada/salão nunca usam saiu_para_entrega.
STATUS_RECEBIDO = 'recebido'
STATUS_CONFIRMADO = 'confirmado'
STATUS_EM_PREPARO = 'em_preparo'
STATUS_PRONTO = 'pronto'
STATUS_SAIU_PARA_ENTREGA = 'saiu_para_entrega'
STATUS_ENTREGUE = 'entregue'
STATUS_CANCELADO = 'cancelado'

STATUS_PEDIDO_VALIDOS = (
    STATUS_RECEBIDO, STATUS_CONFIRMADO, STATUS_EM_PREPARO, STATUS_PRONTO,
    STATUS_SAIU_PARA_ENTREGA, STATUS_ENTREGUE, STATUS_CANCELADO,
)

# Estados que não podem mais ser alterados (RN17: finalizados não podem ser apagados,
# e não fazem mais sentido para transição de status).
STATUS_FINAIS = (STATUS_ENTREGUE, STATUS_CANCELADO)

# RN13: fluxo completo, só para delivery (é o único tipo que passa por
# "saiu_para_entrega"). RN14: retirada/salão vão direto de "pronto" para "entregue" -
# não existe estado de entrega para quem retira no balcão ou come no salão.
FLUXO_DELIVERY = (
    STATUS_RECEBIDO, STATUS_CONFIRMADO, STATUS_EM_PREPARO, STATUS_PRONTO,
    STATUS_SAIU_PARA_ENTREGA, STATUS_ENTREGUE,
)
FLUXO_RETIRADA_OU_SALAO = (
    STATUS_RECEBIDO, STATUS_CONFIRMADO, STATUS_EM_PREPARO, STATUS_PRONTO, STATUS_ENTREGUE,
)
FLUXO_PEDIDO_POR_TIPO = {
    TIPO_DELIVERY: FLUXO_DELIVERY,
    TIPO_RETIRADA: FLUXO_RETIRADA_OU_SALAO,
    TIPO_SALAO: FLUXO_RETIRADA_OU_SALAO,
}


class Pedido(db.Model):
    __tablename__ = 'pedidos'

    id = db.Column(db.Integer, primary_key=True)
    # RF17: identificador único e curto para o cliente acompanhar/citar o pedido,
    # independente do id sequencial interno.
    numero = db.Column(db.String(36), nullable=False, unique=True, default=lambda: uuid.uuid4().hex[:10].upper())

    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=True)
    tipo = db.Column(db.String(10), nullable=False)
    status = db.Column(db.String(20), nullable=False, default=STATUS_RECEBIDO)

    endereco_entrega_id = db.Column(db.Integer, db.ForeignKey('enderecos.id'), nullable=True)
    comanda_id = db.Column(db.Integer, db.ForeignKey('comandas.id'), nullable=True)

    subtotal = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    desconto = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    taxa_entrega = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    total = db.Column(db.Numeric(10, 2), nullable=False, default=0)

    cupom_id = db.Column(db.Integer, db.ForeignKey('cupons.id'), nullable=True)
    observacoes = db.Column(db.String(500), nullable=True)

    atendente_id = db.Column(db.Integer, db.ForeignKey('funcionarios.id'), nullable=True)
    prioridade = db.Column(db.Integer, nullable=False, default=0)  # RF19
    horario_agendado = db.Column(db.DateTime, nullable=True)  # RN18

    criado_em = db.Column(db.DateTime, nullable=False, default=agora_utc, index=True)
    atualizado_em = db.Column(
        db.DateTime, nullable=False,
        default=agora_utc,
        onupdate=agora_utc,
    )

    endereco_entrega = db.relationship('Endereco')
    cupom = db.relationship('Cupom')
    atendente = db.relationship('Funcionario')
    itens = db.relationship('ItemPedido', backref='pedido', cascade='all, delete-orphan')
    pagamentos = db.relationship('Pagamento', backref='pedido', cascade='all, delete-orphan')
    historico = db.relationship(
        'HistoricoPedido', backref='pedido', cascade='all, delete-orphan',
        order_by='HistoricoPedido.criado_em',
    )
    entrega = db.relationship('Entrega', uselist=False, backref='pedido')

    __table_args__ = (
        db.CheckConstraint(f"tipo in {TIPOS_PEDIDO_VALIDOS!r}", name='ck_pedido_tipo_valido'),
        db.CheckConstraint(f"status in {STATUS_PEDIDO_VALIDOS!r}", name='ck_pedido_status_valido'),
    )

    @property
    def pagamento_atual(self):
        return self.pagamentos[-1] if self.pagamentos else None

    def pode_cliente_cancelar_diretamente(self):
        # RN11: cliente só cancela sozinho antes do início do preparo.
        return self.status in (STATUS_RECEBIDO, STATUS_CONFIRMADO)

    def __repr__(self):
        return f'<Pedido {self.numero} {self.status}>'


class ItemPedido(db.Model):
    """Item do pedido - fotografia do carrinho no momento da confirmação, com o preço
    já calculado e congelado pelo backend (nunca recalculado depois)."""
    __tablename__ = 'itens_pedido'

    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedidos.id'), nullable=False)
    produto_id = db.Column(db.Integer, db.ForeignKey('produtos.id'), nullable=True)
    tamanho_id = db.Column(db.Integer, db.ForeignKey('tamanhos_pizza.id'), nullable=True)
    massa_id = db.Column(db.Integer, db.ForeignKey('massas.id'), nullable=True)
    borda_id = db.Column(db.Integer, db.ForeignKey('bordas.id'), nullable=True)

    quantidade = db.Column(db.Integer, nullable=False, default=1)
    preco_unitario = db.Column(db.Numeric(10, 2), nullable=False)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    observacoes = db.Column(db.String(300), nullable=True)

    produto = db.relationship('Produto')
    tamanho = db.relationship('TamanhoPizza')
    massa = db.relationship('Massa')
    borda = db.relationship('Borda')
    sabores = db.relationship('ItemPedidoSabor', cascade='all, delete-orphan')
    adicionais = db.relationship('ItemPedidoAdicional', cascade='all, delete-orphan')

    __table_args__ = (
        db.CheckConstraint('quantidade > 0', name='ck_item_pedido_quantidade_positiva'),
    )

    @property
    def descricao(self):
        if self.produto_id:
            return self.produto.nome
        sabores = ' + '.join(s.sabor.nome for s in self.sabores)
        return f'Pizza {self.tamanho.nome} ({sabores})'


class ItemPedidoSabor(db.Model):
    __tablename__ = 'itens_pedido_sabores'

    id = db.Column(db.Integer, primary_key=True)
    item_pedido_id = db.Column(db.Integer, db.ForeignKey('itens_pedido.id'), nullable=False)
    sabor_id = db.Column(db.Integer, db.ForeignKey('sabores.id'), nullable=False)

    sabor = db.relationship('Sabor')


class ItemPedidoAdicional(db.Model):
    __tablename__ = 'itens_pedido_adicionais'

    id = db.Column(db.Integer, primary_key=True)
    item_pedido_id = db.Column(db.Integer, db.ForeignKey('itens_pedido.id'), nullable=False)
    adicional_id = db.Column(db.Integer, db.ForeignKey('adicionais.id'), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False, default=1)
    preco_unitario = db.Column(db.Numeric(10, 2), nullable=False)

    adicional = db.relationship('Adicional')


class HistoricoPedido(db.Model):
    """Trilha de auditoria do pedido (RF38, RN17): nada é apagado, só registrado."""
    __tablename__ = 'historico_pedidos'

    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedidos.id'), nullable=False)
    funcionario_id = db.Column(db.Integer, db.ForeignKey('funcionarios.id'), nullable=True)
    status_anterior = db.Column(db.String(20), nullable=True)
    status_novo = db.Column(db.String(20), nullable=False)
    observacao = db.Column(db.String(300), nullable=True)
    criado_em = db.Column(db.DateTime, nullable=False, default=agora_utc)

    funcionario = db.relationship('Funcionario')
