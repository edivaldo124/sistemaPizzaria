from servicos.tempo import agora_utc

from config import db

STATUS_CARRINHO_ABERTO = 'aberto'
STATUS_CARRINHO_CONVERTIDO = 'convertido'


class Carrinho(db.Model):
    """Carrinho de compras (RF10). Nunca guarda preço - é sempre recalculado pelo
    backend (servicos/precos.py) na hora de exibir ou finalizar."""
    __tablename__ = 'carrinhos'

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=True)
    session_key = db.Column(db.String(64), nullable=True, index=True)  # carrinho de visitante
    status = db.Column(db.String(12), nullable=False, default=STATUS_CARRINHO_ABERTO)
    criado_em = db.Column(db.DateTime, nullable=False, default=agora_utc)
    atualizado_em = db.Column(
        db.DateTime, nullable=False,
        default=agora_utc,
        onupdate=agora_utc,
    )

    itens = db.relationship('ItemCarrinho', backref='carrinho', cascade='all, delete-orphan')


class ItemCarrinho(db.Model):
    """Um item do carrinho: produto simples OU pizza montada (tamanho+sabores+massa+borda)."""
    __tablename__ = 'itens_carrinho'

    id = db.Column(db.Integer, primary_key=True)
    carrinho_id = db.Column(db.Integer, db.ForeignKey('carrinhos.id'), nullable=False)
    produto_id = db.Column(db.Integer, db.ForeignKey('produtos.id'), nullable=True)
    tamanho_id = db.Column(db.Integer, db.ForeignKey('tamanhos_pizza.id'), nullable=True)
    massa_id = db.Column(db.Integer, db.ForeignKey('massas.id'), nullable=True)
    borda_id = db.Column(db.Integer, db.ForeignKey('bordas.id'), nullable=True)
    quantidade = db.Column(db.Integer, nullable=False, default=1)
    observacoes = db.Column(db.String(300), nullable=True)

    produto = db.relationship('Produto')
    tamanho = db.relationship('TamanhoPizza')
    massa = db.relationship('Massa')
    borda = db.relationship('Borda')
    sabores = db.relationship('ItemCarrinhoSabor', cascade='all, delete-orphan')
    adicionais = db.relationship('ItemCarrinhoAdicional', cascade='all, delete-orphan')

    __table_args__ = (
        db.CheckConstraint('quantidade > 0', name='ck_item_carrinho_quantidade_positiva'),
    )

    @property
    def eh_pizza(self):
        return self.tamanho_id is not None


class ItemCarrinhoSabor(db.Model):
    __tablename__ = 'itens_carrinho_sabores'

    id = db.Column(db.Integer, primary_key=True)
    item_carrinho_id = db.Column(db.Integer, db.ForeignKey('itens_carrinho.id'), nullable=False)
    sabor_id = db.Column(db.Integer, db.ForeignKey('sabores.id'), nullable=False)

    sabor = db.relationship('Sabor')


class ItemCarrinhoAdicional(db.Model):
    __tablename__ = 'itens_carrinho_adicionais'

    id = db.Column(db.Integer, primary_key=True)
    item_carrinho_id = db.Column(db.Integer, db.ForeignKey('itens_carrinho.id'), nullable=False)
    adicional_id = db.Column(db.Integer, db.ForeignKey('adicionais.id'), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False, default=1)

    adicional = db.relationship('Adicional')
