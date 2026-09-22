from config import db


class TamanhoPizza(db.Model):
    """Tamanho de pizza e quantas frações de sabor ele aceita (RF07, RN02)."""
    __tablename__ = 'tamanhos_pizza'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(40), nullable=False, unique=True)  # "Pequena", "Média", "Grande"...
    max_sabores = db.Column(db.Integer, nullable=False, default=1)
    numero_fatias = db.Column(db.Integer, nullable=True)
    ordem_exibicao = db.Column(db.Integer, nullable=False, default=0)
    ativo = db.Column(db.Boolean, nullable=False, default=True)

    def __str__(self):
        return self.nome


class Sabor(db.Model):
    """Sabor de pizza (RF09). O preço varia por tamanho - ver SaborPreco."""
    __tablename__ = 'sabores'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, unique=True)
    descricao = db.Column(db.String(300), nullable=True)
    foto_arquivo = db.Column(db.String(120), nullable=True)
    disponivel = db.Column(db.Boolean, nullable=False, default=True)  # RN12
    ativo = db.Column(db.Boolean, nullable=False, default=True)

    precos = db.relationship('SaborPreco', backref='sabor', cascade='all, delete-orphan')

    def __str__(self):
        return self.nome

    @property
    def pode_ser_vendido(self):
        return self.ativo and self.disponivel

    def preco_no_tamanho(self, tamanho_id):
        for p in self.precos:
            if p.tamanho_id == tamanho_id:
                return p.preco
        return None


class SaborPreco(db.Model):
    """Preço de um sabor para um tamanho específico de pizza."""
    __tablename__ = 'sabores_precos'

    id = db.Column(db.Integer, primary_key=True)
    sabor_id = db.Column(db.Integer, db.ForeignKey('sabores.id'), nullable=False)
    tamanho_id = db.Column(db.Integer, db.ForeignKey('tamanhos_pizza.id'), nullable=False)
    preco = db.Column(db.Numeric(10, 2), nullable=False)

    tamanho = db.relationship('TamanhoPizza')

    __table_args__ = (
        db.UniqueConstraint('sabor_id', 'tamanho_id', name='uq_sabor_tamanho'),
    )


class Massa(db.Model):
    """Tipo de massa da pizza (RF08)."""
    __tablename__ = 'massas'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(60), nullable=False, unique=True)
    preco_adicional = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    ativo = db.Column(db.Boolean, nullable=False, default=True)

    def __str__(self):
        return self.nome


class Borda(db.Model):
    """Borda recheada (RF08, RN04)."""
    __tablename__ = 'bordas'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(60), nullable=False, unique=True)
    preco_adicional = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    ativo = db.Column(db.Boolean, nullable=False, default=True)

    def __str__(self):
        return self.nome


class Adicional(db.Model):
    """Ingrediente extra que pode ser somado ao item do pedido (RF08, RN04)."""
    __tablename__ = 'adicionais'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(80), nullable=False, unique=True)
    preco = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    disponivel = db.Column(db.Boolean, nullable=False, default=True)
    ativo = db.Column(db.Boolean, nullable=False, default=True)

    def __str__(self):
        return self.nome
