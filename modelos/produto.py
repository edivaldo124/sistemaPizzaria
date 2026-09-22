from config import db


class Produto(db.Model):
    """Item de cardápio com preço fixo: bebida, sobremesa, combo etc. (RF06).

    Pizza montada NÃO é um Produto - ela é composta em tempo de pedido a partir de
    TamanhoPizza + Sabor(es) + Massa + Borda + Adicionais (RF07-RF09), porque o preço
    depende da combinação escolhida e não de um valor fixo cadastrado aqui.
    """
    __tablename__ = 'produtos'

    id = db.Column(db.Integer, primary_key=True)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias.id'), nullable=False)
    nome = db.Column(db.String(120), nullable=False)
    descricao = db.Column(db.String(500), nullable=True)
    foto_arquivo = db.Column(db.String(120), nullable=True)
    preco = db.Column(db.Numeric(10, 2), nullable=False)
    disponivel = db.Column(db.Boolean, nullable=False, default=True)  # RN12: sem estoque -> indisponível
    ativo = db.Column(db.Boolean, nullable=False, default=True)

    def __str__(self):
        return self.nome

    @property
    def pode_ser_vendido(self):
        # RN01: só produto ativo e disponível entra no pedido.
        return self.ativo and self.disponivel
