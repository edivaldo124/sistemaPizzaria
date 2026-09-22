from config import db


class Categoria(db.Model):
    """Categoria de produto: pizzas, bebidas, sobremesas, combos... (RF05)."""
    __tablename__ = 'categorias'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(80), nullable=False, unique=True)
    descricao = db.Column(db.String(255), nullable=True)
    ordem_exibicao = db.Column(db.Integer, nullable=False, default=0)
    ativo = db.Column(db.Boolean, nullable=False, default=True)

    produtos = db.relationship('Produto', backref='categoria')

    def __str__(self):
        return self.nome
