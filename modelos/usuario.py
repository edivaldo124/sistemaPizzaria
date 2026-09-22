from servicos.tempo import agora_utc

from config import db
from servicos.senhas import conferir_hash, gerar_hash

# RF01/Perfis: cada conta pertence a exatamente um tipo. O tipo decide o que a conta
# pode fazer (servicos/autorizacao.py) - nunca o frontend.
TIPO_CLIENTE = 'cliente'
TIPO_ATENDENTE = 'atendente'
TIPO_COZINHA = 'cozinha'
TIPO_ENTREGADOR = 'entregador'
TIPO_GERENTE = 'gerente'
TIPO_ADMIN = 'admin'

TIPOS_FUNCIONARIO = (TIPO_ATENDENTE, TIPO_COZINHA, TIPO_ENTREGADOR, TIPO_GERENTE, TIPO_ADMIN)
TIPOS_VALIDOS = (TIPO_CLIENTE,) + TIPOS_FUNCIONARIO


class Usuario(db.Model):
    """Conta de acesso única para clientes e funcionários (RF01).

    Dados específicos de cada papel (endereços do cliente, cargo do funcionário) ficam
    em tabelas satélite (Cliente, Funcionario) ligadas 1:1 - assim o login, a senha e o
    tipo continuam num único lugar, sem duplicar coluna por papel.
    """
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    telefone = db.Column(db.String(20), nullable=True)
    senha_hash = db.Column(db.String(255), nullable=False)
    tipo = db.Column(db.String(20), nullable=False, default=TIPO_CLIENTE)
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    criado_em = db.Column(db.DateTime, nullable=False, default=agora_utc)

    cliente = db.relationship('Cliente', backref='usuario', uselist=False, cascade='all, delete-orphan')
    funcionario = db.relationship('Funcionario', backref='usuario', uselist=False, cascade='all, delete-orphan')

    __table_args__ = (
        db.CheckConstraint(f"tipo in {TIPOS_VALIDOS!r}", name='ck_usuarios_tipo_valido'),
    )

    def set_senha(self, senha_texto_puro):
        self.senha_hash = gerar_hash(senha_texto_puro)

    def verificar_senha(self, senha_texto_puro):
        return conferir_hash(self.senha_hash, senha_texto_puro)

    @property
    def is_funcionario(self):
        return self.tipo in TIPOS_FUNCIONARIO

    @property
    def is_gerencia(self):
        # RN20: só gerente/admin altera preço, concede desconto manual ou cancela pedido em preparo.
        return self.tipo in (TIPO_GERENTE, TIPO_ADMIN)


class Cliente(db.Model):
    """Dados complementares de quem compra (RF03)."""
    __tablename__ = 'clientes'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), unique=True, nullable=False)
    cpf = db.Column(db.String(14), unique=True, nullable=True)
    data_nascimento = db.Column(db.Date, nullable=True)

    enderecos = db.relationship('Endereco', backref='cliente', cascade='all, delete-orphan')
    pedidos = db.relationship('Pedido', backref='cliente', lazy='dynamic')


class Funcionario(db.Model):
    """Dados complementares de quem trabalha na pizzaria (RF02)."""
    __tablename__ = 'funcionarios'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), unique=True, nullable=False)
    cargo = db.Column(db.String(80), nullable=True)
    data_admissao = db.Column(db.Date, nullable=True)
