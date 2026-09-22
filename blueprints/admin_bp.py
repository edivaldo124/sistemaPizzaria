from datetime import datetime, timedelta
from decimal import Decimal

from flask import Blueprint, flash, redirect, render_template, request, url_for

from dao.catalogo_dao import CategoriaDAO, ProdutoDAO
from dao.pedido_dao import PedidoDAO
from dao.usuario_dao import UsuarioDAO
from modelos.categoria import Categoria
from modelos.configuracao import ConfiguracaoLoja, FORA_HORARIO_OPCOES_VALIDAS, REGRAS_PRECO_VALIDAS
from modelos.entrega import RegiaoEntrega
from modelos.produto import Produto
from modelos.usuario import TIPO_ADMIN, TIPO_GERENTE, TIPOS_FUNCIONARIO
from servicos.autorizacao import papel_requerido
from servicos.relatorios import relatorio_vendas
from servicos.tempo import agora_utc

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

_PAPEIS_GERENCIA = (TIPO_GERENTE, TIPO_ADMIN)


@admin_bp.route('/')
@papel_requerido(*_PAPEIS_GERENCIA)
def painel(usuario):
    agora = agora_utc()
    pedidos_hoje = PedidoDAO.listar_por_periodo(agora - timedelta(days=1), agora, apenas_finalizados=False)
    return render_template('admin/painel.html', pedidos_hoje=pedidos_hoje)


# --- Categorias (RF05) ---------------------------------------------------

@admin_bp.route('/categorias', methods=['GET', 'POST'])
@papel_requerido(*_PAPEIS_GERENCIA)
def categorias(usuario):
    if request.method == 'POST':
        nome = (request.form.get('nome') or '').strip()
        if not nome:
            flash('Informe o nome da categoria.', 'erro')
        else:
            CategoriaDAO.salvar(Categoria(nome=nome, descricao=request.form.get('descricao')))
            flash('Categoria criada.', 'sucesso')
        return redirect(url_for('admin.categorias'))
    return render_template('admin/categorias.html', categorias=CategoriaDAO.listar(apenas_ativas=False))


# --- Produtos (RF06) -------------------------------------------------------

@admin_bp.route('/produtos', methods=['GET', 'POST'])
@papel_requerido(*_PAPEIS_GERENCIA)
def produtos(usuario):
    if request.method == 'POST':
        nome = (request.form.get('nome') or '').strip()
        categoria_id = request.form.get('categoria_id', type=int)
        preco_texto = (request.form.get('preco') or '').replace(',', '.')
        try:
            preco = Decimal(preco_texto)
        except Exception:
            preco = None
        if not nome or not categoria_id or preco is None or preco < 0:
            flash('Preencha nome, categoria e um preço válido.', 'erro')
        else:
            ProdutoDAO.salvar(Produto(
                nome=nome, categoria_id=categoria_id, preco=preco,
                descricao=request.form.get('descricao'),
            ))
            flash('Produto criado.', 'sucesso')
        return redirect(url_for('admin.produtos'))
    return render_template(
        'admin/produtos.html', produtos=ProdutoDAO.listar_todos(), categorias=CategoriaDAO.listar(apenas_ativas=False),
    )


@admin_bp.route('/produtos/<int:produto_id>/disponibilidade', methods=['POST'])
@papel_requerido(*_PAPEIS_GERENCIA)
def alternar_disponibilidade_produto(usuario, produto_id):
    produto = ProdutoDAO.buscar_por_id(produto_id)
    if produto:
        ProdutoDAO.definir_disponibilidade(produto_id, not produto.disponivel)
        flash('Disponibilidade atualizada.', 'sucesso')
    return redirect(url_for('admin.produtos'))


# --- Regiões de entrega (RF26) ---------------------------------------------

@admin_bp.route('/regioes-entrega', methods=['GET', 'POST'])
@papel_requerido(*_PAPEIS_GERENCIA)
def regioes_entrega(usuario):
    from config import db
    if request.method == 'POST':
        nome = (request.form.get('nome') or '').strip()
        taxa_texto = (request.form.get('taxa_entrega') or '0').replace(',', '.')
        try:
            taxa = Decimal(taxa_texto)
        except Exception:
            taxa = None
        if not nome or taxa is None or taxa < 0:
            flash('Informe nome e uma taxa de entrega válida.', 'erro')
        else:
            db.session.add(RegiaoEntrega(nome=nome, taxa_entrega=taxa))
            db.session.commit()
            flash('Região de entrega criada.', 'sucesso')
        return redirect(url_for('admin.regioes_entrega'))
    return render_template('admin/regioes_entrega.html', regioes=RegiaoEntrega.query.order_by(RegiaoEntrega.nome).all())


# --- Funcionários (RF02) ----------------------------------------------------

@admin_bp.route('/funcionarios', methods=['GET', 'POST'])
@papel_requerido(TIPO_ADMIN)  # RN20-like: só admin cria/gerencia contas de funcionário
def funcionarios(usuario):
    if request.method == 'POST':
        nome = (request.form.get('nome') or '').strip()
        email = (request.form.get('email') or '').strip().lower()
        tipo = request.form.get('tipo')
        senha = request.form.get('senha') or ''

        if not nome or not email or tipo not in TIPOS_FUNCIONARIO or len(senha) < 8:
            flash('Preencha nome, e-mail, papel e uma senha com pelo menos 8 caracteres.', 'erro')
        elif UsuarioDAO.buscar_por_email(email):
            flash('Já existe uma conta com este e-mail.', 'erro')
        else:
            UsuarioDAO.criar_funcionario(
                nome=nome, email=email, senha=senha, tipo=tipo, cargo=request.form.get('cargo'),
                veiculo=request.form.get('veiculo'), placa=request.form.get('placa'),
            )
            flash('Funcionário cadastrado.', 'sucesso')
        return redirect(url_for('admin.funcionarios'))
    return render_template('admin/funcionarios.html', funcionarios=UsuarioDAO.listar_funcionarios())


# --- Pedidos (RF18) ---------------------------------------------------------

@admin_bp.route('/pedidos')
@papel_requerido(*_PAPEIS_GERENCIA)
def pedidos(usuario):
    agora = agora_utc()
    lista = PedidoDAO.listar_por_periodo(agora - timedelta(days=7), agora, apenas_finalizados=False)
    return render_template('admin/pedidos.html', pedidos=lista)


# --- Configuração da loja (RF27, RN03, RN18) --------------------------------

@admin_bp.route('/configuracao', methods=['GET', 'POST'])
@papel_requerido(TIPO_ADMIN)
def configuracao(usuario):
    from config import db
    config = ConfiguracaoLoja.obter()

    if request.method == 'POST':
        try:
            abertura = request.form.get('horario_abertura') or None
            fechamento = request.form.get('horario_fechamento') or None
            config.horario_abertura = datetime.strptime(abertura, '%H:%M').time() if abertura else None
            config.horario_fechamento = datetime.strptime(fechamento, '%H:%M').time() if fechamento else None
            config.valor_minimo_pedido = Decimal((request.form.get('valor_minimo_pedido') or '0').replace(',', '.'))

            regra = request.form.get('regra_preco_multiplos_sabores')
            fora_horario = request.form.get('fora_horario')
            if regra not in REGRAS_PRECO_VALIDAS or fora_horario not in FORA_HORARIO_OPCOES_VALIDAS:
                raise ValueError('Opção inválida.')
            config.regra_preco_multiplos_sabores = regra
            config.fora_horario = fora_horario
            config.permite_cupom_acumulado = bool(request.form.get('permite_cupom_acumulado'))

            db.session.commit()
            flash('Configuração atualizada.', 'sucesso')
        except (ValueError, TypeError):
            db.session.rollback()
            flash('Dados inválidos. Confira horários (HH:MM) e valores.', 'erro')
        return redirect(url_for('admin.configuracao'))

    return render_template('admin/configuracao.html', config=config)


# --- Relatórios (RF34, RF35) -------------------------------------------------

@admin_bp.route('/relatorios')
@papel_requerido(*_PAPEIS_GERENCIA)
def relatorios(usuario):
    fim = agora_utc()
    inicio_texto = request.args.get('inicio')
    fim_texto = request.args.get('fim')
    try:
        inicio = datetime.strptime(inicio_texto, '%Y-%m-%d') if inicio_texto else fim - timedelta(days=30)
        if fim_texto:
            fim = datetime.strptime(fim_texto, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
    except ValueError:
        inicio = fim - timedelta(days=30)
        flash('Datas inválidas - mostrando os últimos 30 dias.', 'erro')

    dados = relatorio_vendas(inicio, fim)
    return render_template('admin/relatorios.html', dados=dados, inicio=inicio, fim=fim)
