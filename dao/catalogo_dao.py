from config import db
from modelos.categoria import Categoria
from modelos.produto import Produto
from modelos.pizza import Adicional, Borda, Massa, Sabor, SaborPreco, TamanhoPizza


class CategoriaDAO:
    @staticmethod
    def listar(*, apenas_ativas=True):
        query = Categoria.query
        if apenas_ativas:
            query = query.filter_by(ativo=True)
        return query.order_by(Categoria.ordem_exibicao.asc(), Categoria.nome.asc()).all()

    @staticmethod
    def buscar_por_id(categoria_id):
        return db.session.get(Categoria, categoria_id)

    @staticmethod
    def salvar(categoria):
        db.session.add(categoria)
        db.session.commit()
        return categoria


class ProdutoDAO:
    @staticmethod
    def listar_cardapio():
        """Só o que pode ser vendido agora - RN01."""
        return (
            Produto.query
            .filter_by(ativo=True, disponivel=True)
            .join(Categoria)
            .filter(Categoria.ativo.is_(True))
            .order_by(Categoria.ordem_exibicao.asc(), Produto.nome.asc())
            .all()
        )

    @staticmethod
    def listar_todos():
        return Produto.query.order_by(Produto.nome.asc()).all()

    @staticmethod
    def buscar_por_id(produto_id):
        return db.session.get(Produto, produto_id)

    @staticmethod
    def salvar(produto):
        db.session.add(produto)
        db.session.commit()
        return produto

    @staticmethod
    def definir_disponibilidade(produto_id, disponivel):
        produto = db.session.get(Produto, produto_id)
        if not produto:
            return False
        produto.disponivel = disponivel
        db.session.commit()
        return True


class TamanhoDAO:
    @staticmethod
    def listar(*, apenas_ativos=True):
        query = TamanhoPizza.query
        if apenas_ativos:
            query = query.filter_by(ativo=True)
        return query.order_by(TamanhoPizza.ordem_exibicao.asc()).all()

    @staticmethod
    def buscar_por_id(tamanho_id):
        return db.session.get(TamanhoPizza, tamanho_id)

    @staticmethod
    def salvar(tamanho):
        db.session.add(tamanho)
        db.session.commit()
        return tamanho


class SaborDAO:
    @staticmethod
    def listar_cardapio():
        return Sabor.query.filter_by(ativo=True, disponivel=True).order_by(Sabor.nome.asc()).all()

    @staticmethod
    def listar_todos():
        return Sabor.query.order_by(Sabor.nome.asc()).all()

    @staticmethod
    def buscar_por_id(sabor_id):
        return db.session.get(Sabor, sabor_id)

    @staticmethod
    def buscar_varios(ids):
        if not ids:
            return []
        return Sabor.query.filter(Sabor.id.in_(ids)).all()

    @staticmethod
    def salvar(sabor):
        db.session.add(sabor)
        db.session.commit()
        return sabor

    @staticmethod
    def definir_preco(sabor_id, tamanho_id, preco):
        registro = SaborPreco.query.filter_by(sabor_id=sabor_id, tamanho_id=tamanho_id).first()
        if registro is None:
            registro = SaborPreco(sabor_id=sabor_id, tamanho_id=tamanho_id, preco=preco)
            db.session.add(registro)
        else:
            registro.preco = preco
        db.session.commit()
        return registro


class MassaDAO:
    @staticmethod
    def listar(*, apenas_ativas=True):
        query = Massa.query
        if apenas_ativas:
            query = query.filter_by(ativo=True)
        return query.order_by(Massa.nome.asc()).all()

    @staticmethod
    def buscar_por_id(massa_id):
        return db.session.get(Massa, massa_id)

    @staticmethod
    def salvar(massa):
        db.session.add(massa)
        db.session.commit()
        return massa


class BordaDAO:
    @staticmethod
    def listar(*, apenas_ativas=True):
        query = Borda.query
        if apenas_ativas:
            query = query.filter_by(ativo=True)
        return query.order_by(Borda.nome.asc()).all()

    @staticmethod
    def buscar_por_id(borda_id):
        return db.session.get(Borda, borda_id)

    @staticmethod
    def salvar(borda):
        db.session.add(borda)
        db.session.commit()
        return borda


class AdicionalDAO:
    @staticmethod
    def listar(*, apenas_disponiveis=True):
        query = Adicional.query.filter_by(ativo=True)
        if apenas_disponiveis:
            query = query.filter_by(disponivel=True)
        return query.order_by(Adicional.nome.asc()).all()

    @staticmethod
    def buscar_varios(ids):
        if not ids:
            return []
        return Adicional.query.filter(Adicional.id.in_(ids)).all()

    @staticmethod
    def buscar_por_id(adicional_id):
        return db.session.get(Adicional, adicional_id)

    @staticmethod
    def salvar(adicional):
        db.session.add(adicional)
        db.session.commit()
        return adicional
