from config import db
from modelos.carrinho import Carrinho, ItemCarrinho, ItemCarrinhoAdicional, ItemCarrinhoSabor
from modelos.carrinho import STATUS_CARRINHO_ABERTO


class CarrinhoDAO:
    @staticmethod
    def obter_ou_criar(*, cliente_id=None, session_key=None):
        """RF10: um carrinho aberto por cliente logado, ou por chave de sessão para
        quem ainda não entrou (o carrinho de visitante é migrado no login)."""
        query = Carrinho.query.filter_by(status=STATUS_CARRINHO_ABERTO)
        if cliente_id is not None:
            carrinho = query.filter_by(cliente_id=cliente_id).first()
        else:
            carrinho = query.filter_by(session_key=session_key).first()

        if carrinho is None:
            carrinho = Carrinho(cliente_id=cliente_id, session_key=session_key if cliente_id is None else None)
            db.session.add(carrinho)
            db.session.commit()
        return carrinho

    @staticmethod
    def migrar_carrinho_visitante_para_cliente(session_key, cliente_id):
        """No login, o carrinho anônimo vira o carrinho do cliente (se ele ainda não
        tiver um aberto) para não perder o que já estava montado."""
        if not session_key:
            return
        carrinho_visitante = Carrinho.query.filter_by(session_key=session_key, status=STATUS_CARRINHO_ABERTO).first()
        if carrinho_visitante is None:
            return
        carrinho_cliente = Carrinho.query.filter_by(cliente_id=cliente_id, status=STATUS_CARRINHO_ABERTO).first()
        if carrinho_cliente is None:
            carrinho_visitante.cliente_id = cliente_id
            carrinho_visitante.session_key = None
            db.session.commit()
        else:
            db.session.delete(carrinho_visitante)
            db.session.commit()

    @staticmethod
    def buscar_item(item_id):
        return db.session.get(ItemCarrinho, item_id)

    @staticmethod
    def adicionar_item(carrinho_id, *, produto_id=None, tamanho_id=None, massa_id=None,
                        borda_id=None, quantidade=1, observacoes=None, sabores_ids=None, adicionais=None):
        item = ItemCarrinho(
            carrinho_id=carrinho_id, produto_id=produto_id, tamanho_id=tamanho_id,
            massa_id=massa_id, borda_id=borda_id, quantidade=quantidade, observacoes=observacoes,
        )
        db.session.add(item)
        db.session.flush()

        for sabor_id in sabores_ids or []:
            db.session.add(ItemCarrinhoSabor(item_carrinho_id=item.id, sabor_id=sabor_id))
        for adicional_id, qtd in (adicionais or []):
            db.session.add(ItemCarrinhoAdicional(item_carrinho_id=item.id, adicional_id=adicional_id, quantidade=qtd))

        db.session.commit()
        return item

    @staticmethod
    def atualizar_quantidade(item_id, quantidade):
        item = db.session.get(ItemCarrinho, item_id)
        if not item:
            return False
        if quantidade <= 0:
            db.session.delete(item)
        else:
            item.quantidade = quantidade
        db.session.commit()
        return True

    @staticmethod
    def remover_item(item_id):
        item = db.session.get(ItemCarrinho, item_id)
        if not item:
            return False
        db.session.delete(item)
        db.session.commit()
        return True

    @staticmethod
    def esvaziar(carrinho_id):
        ItemCarrinho.query.filter_by(carrinho_id=carrinho_id).delete()
        db.session.commit()
