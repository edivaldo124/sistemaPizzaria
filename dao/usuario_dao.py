from config import db
from modelos.entrega import Entregador
from modelos.usuario import TIPO_ENTREGADOR, Cliente, Funcionario, Usuario
from servicos.senhas import conferir_hash, gerar_hash

_HASH_DESCARTAVEL = gerar_hash('senha-descartavel-para-equalizar-tempo')


class UsuarioDAO:
    @staticmethod
    def buscar_por_id(usuario_id):
        return db.session.get(Usuario, usuario_id)

    @staticmethod
    def buscar_por_email(email):
        alvo = (email or '').strip().lower()
        return Usuario.query.filter(Usuario.email == alvo).first() if alvo else None

    @staticmethod
    def autenticar(email, senha):
        usuario = UsuarioDAO.buscar_por_email(email)
        # Mantém uma verificação de hash mesmo quando a conta não existe, reduzindo a
        # diferença de tempo usada para enumerar e-mails cadastrados.
        if usuario:
            senha_valida = usuario.verificar_senha(senha)
        else:
            conferir_hash(_HASH_DESCARTAVEL, senha)
            senha_valida = False
        if usuario and usuario.ativo and senha_valida:
            return usuario
        return None

    @staticmethod
    def criar_cliente(*, nome, email, senha, telefone=None, cpf=None):
        usuario = Usuario(nome=nome, email=email.strip().lower(), telefone=telefone, tipo='cliente')
        usuario.set_senha(senha)
        db.session.add(usuario)
        db.session.flush()  # garante usuario.id antes de criar o Cliente

        cliente = Cliente(usuario_id=usuario.id, cpf=cpf)
        db.session.add(cliente)
        db.session.commit()
        return usuario

    @staticmethod
    def criar_funcionario(*, nome, email, senha, tipo, telefone=None, cargo=None, veiculo=None, placa=None):
        from modelos.usuario import TIPOS_FUNCIONARIO
        if tipo not in TIPOS_FUNCIONARIO:
            raise ValueError(f'Tipo de funcionário inválido: {tipo}')

        usuario = Usuario(nome=nome, email=email.strip().lower(), telefone=telefone, tipo=tipo)
        usuario.set_senha(senha)
        db.session.add(usuario)
        db.session.flush()

        db.session.add(Funcionario(usuario_id=usuario.id, cargo=cargo))
        if tipo == TIPO_ENTREGADOR:
            # RF24: todo entregador também tem um perfil de entrega (veículo/placa)
            # além do perfil de funcionário (cargo/admissão) que todo o staff tem.
            db.session.add(Entregador(usuario_id=usuario.id, veiculo=veiculo, placa=placa))

        db.session.commit()
        return usuario

    @staticmethod
    def listar_funcionarios(*, apenas_ativos=False):
        query = Usuario.query.filter(Usuario.tipo != 'cliente')
        if apenas_ativos:
            query = query.filter(Usuario.ativo.is_(True))
        return query.order_by(Usuario.nome.asc()).all()

    @staticmethod
    def listar_clientes(*, apenas_ativos=False, busca=None):
        query = Usuario.query.filter(Usuario.tipo == 'cliente')
        if apenas_ativos:
            query = query.filter(Usuario.ativo.is_(True))
        if busca:
            termo = f'%{busca.strip()}%'
            query = query.filter(db.or_(Usuario.nome.ilike(termo), Usuario.email.ilike(termo)))
        return query.order_by(Usuario.nome.asc()).all()

    @staticmethod
    def definir_ativo(usuario_id, ativo):
        usuario = db.session.get(Usuario, usuario_id)
        if not usuario:
            return False
        usuario.ativo = ativo
        db.session.commit()
        return True
