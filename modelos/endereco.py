from config import db


class Endereco(db.Model):
    """Endereço de entrega do cliente - um cliente pode ter vários (RF04)."""
    __tablename__ = 'enderecos'

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    apelido = db.Column(db.String(40), nullable=True)  # "Casa", "Trabalho"...
    logradouro = db.Column(db.String(150), nullable=False)
    numero = db.Column(db.String(20), nullable=False)
    complemento = db.Column(db.String(100), nullable=True)
    bairro = db.Column(db.String(100), nullable=False)
    cidade = db.Column(db.String(100), nullable=False)
    uf = db.Column(db.String(2), nullable=False)
    cep = db.Column(db.String(9), nullable=True)
    referencia = db.Column(db.String(150), nullable=True)
    principal = db.Column(db.Boolean, nullable=False, default=False)

    # RN05/RN06: a taxa de entrega e a validação da área atendida vêm da região, não do
    # texto livre do bairro digitado pelo cliente.
    regiao_entrega_id = db.Column(db.Integer, db.ForeignKey('regioes_entrega.id'), nullable=True)
    regiao_entrega = db.relationship('RegiaoEntrega')

    def __str__(self):
        return f'{self.logradouro}, {self.numero} - {self.bairro}'
