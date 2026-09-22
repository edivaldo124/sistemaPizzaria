from config import db
from modelos.pedido import (
    STATUS_CONFIRMADO, STATUS_EM_PREPARO, STATUS_FINAIS, STATUS_PRONTO, STATUS_RECEBIDO,
    STATUS_SAIU_PARA_ENTREGA, Pedido,
)


class PedidoDAO:
    @staticmethod
    def buscar_por_id(pedido_id):
        return db.session.get(Pedido, pedido_id)

    @staticmethod
    def buscar_por_numero(numero):
        return Pedido.query.filter_by(numero=numero).first()

    @staticmethod
    def listar_por_cliente(cliente_id):
        return Pedido.query.filter_by(cliente_id=cliente_id).order_by(Pedido.criado_em.desc()).all()

    @staticmethod
    def listar_fila_cozinha():
        """RF19: fila ordenada por prioridade e depois por horário de chegada."""
        return (
            Pedido.query
            .filter(Pedido.status.in_((STATUS_RECEBIDO, STATUS_CONFIRMADO, STATUS_EM_PREPARO)))
            .order_by(Pedido.prioridade.desc(), Pedido.criado_em.asc())
            .all()
        )

    @staticmethod
    def listar_prontos_para_entrega():
        return (
            Pedido.query
            .filter_by(status=STATUS_PRONTO)
            .order_by(Pedido.criado_em.asc())
            .all()
        )

    @staticmethod
    def listar_em_rota(entregador_id=None):
        query = Pedido.query.filter_by(status=STATUS_SAIU_PARA_ENTREGA)
        if entregador_id is not None:
            query = query.join(Pedido.entrega).filter_by(entregador_id=entregador_id)
        return query.order_by(Pedido.criado_em.asc()).all()

    @staticmethod
    def listar_por_periodo(inicio, fim, *, apenas_finalizados=True):
        """RF34: base para relatórios de venda por período."""
        query = Pedido.query.filter(Pedido.criado_em >= inicio, Pedido.criado_em <= fim)
        if apenas_finalizados:
            query = query.filter(Pedido.status.in_(STATUS_FINAIS))
        return query.order_by(Pedido.criado_em.asc()).all()
