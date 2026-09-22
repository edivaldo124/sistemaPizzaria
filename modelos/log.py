from servicos.tempo import agora_utc

from config import db


class LogAuditoria(db.Model):
    """Registro de operações administrativas importantes (RF38, item 11 de Segurança).

    Cobre alterações fora do fluxo de pedidos (preço, cadastro, permissões, estoque,
    caixa...) - o histórico de status de pedido tem sua própria tabela (HistoricoPedido)
    porque é consultado com muito mais frequência e por um público diferente.
    """
    __tablename__ = 'logs_auditoria'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    acao = db.Column(db.String(80), nullable=False)
    entidade = db.Column(db.String(60), nullable=False)
    entidade_id = db.Column(db.Integer, nullable=True)
    detalhes = db.Column(db.Text, nullable=True)
    criado_em = db.Column(db.DateTime, nullable=False, default=agora_utc, index=True)

    usuario = db.relationship('Usuario')
