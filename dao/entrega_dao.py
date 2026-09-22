from config import db
from modelos.entrega import STATUS_ENTREGA_AGUARDANDO, STATUS_ENTREGA_EM_ROTA, Entrega, Entregador
from modelos.pedido import STATUS_SAIU_PARA_ENTREGA, Pedido


class EntregadorDAO:
    @staticmethod
    def buscar_por_usuario(usuario_id):
        return Entregador.query.filter_by(usuario_id=usuario_id).first()

    @staticmethod
    def listar(*, apenas_ativos=True):
        query = Entregador.query
        if apenas_ativos:
            query = query.filter_by(ativo=True)
        return query.all()


class EntregaDAO:
    @staticmethod
    def criar(*, pedido_id, entregador_id):
        entrega = Entrega(pedido_id=pedido_id, entregador_id=entregador_id, status=STATUS_ENTREGA_EM_ROTA)
        db.session.add(entrega)
        db.session.commit()
        return entrega

    @staticmethod
    def buscar_por_pedido(pedido_id):
        return Entrega.query.filter_by(pedido_id=pedido_id).first()

    @staticmethod
    def listar_do_entregador(entregador_id):
        """RF24/RF25: entregas em andamento atribuídas a este entregador."""
        return (
            Entrega.query
            .filter_by(entregador_id=entregador_id)
            .filter(Entrega.status.in_((STATUS_ENTREGA_AGUARDANDO, STATUS_ENTREGA_EM_ROTA)))
            .join(Pedido)
            .filter(Pedido.status == STATUS_SAIU_PARA_ENTREGA)
            .all()
        )

    @staticmethod
    def marcar_entregue(entrega):
        from modelos.entrega import STATUS_ENTREGA_ENTREGUE
        from servicos.tempo import agora_utc
        entrega.status = STATUS_ENTREGA_ENTREGUE
        entrega.entregue_em = agora_utc()
        db.session.commit()
