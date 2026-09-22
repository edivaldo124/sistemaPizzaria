from config import db

REGRA_PRECO_MAIOR_VALOR = 'maior_valor'
REGRA_PRECO_MEDIA = 'media'
REGRAS_PRECO_VALIDAS = (REGRA_PRECO_MAIOR_VALOR, REGRA_PRECO_MEDIA)

FORA_HORARIO_BLOQUEAR = 'bloquear'
FORA_HORARIO_AGENDAR = 'agendar'
FORA_HORARIO_OPCOES_VALIDAS = (FORA_HORARIO_BLOQUEAR, FORA_HORARIO_AGENDAR)


class ConfiguracaoLoja(db.Model):
    """Configuração única da loja (RF27, RN03, RN08, RN18).

    Sempre há exatamente uma linha (id=1). Não existe DAO de criação: a linha é
    garantida por `ConfiguracaoLoja.obter()`.
    """
    __tablename__ = 'configuracao_loja'

    id = db.Column(db.Integer, primary_key=True)

    horario_abertura = db.Column(db.Time, nullable=True)
    horario_fechamento = db.Column(db.Time, nullable=True)
    valor_minimo_pedido = db.Column(db.Numeric(10, 2), nullable=False, default=0)

    # RN03: preço da pizza com múltiplos sabores.
    regra_preco_multiplos_sabores = db.Column(db.String(20), nullable=False, default=REGRA_PRECO_MAIOR_VALOR)

    # RN18: pedido fora do horário de atendimento.
    fora_horario = db.Column(db.String(20), nullable=False, default=FORA_HORARIO_BLOQUEAR)

    # RN08: cupons não se acumulam, salvo permissão explícita do administrador.
    permite_cupom_acumulado = db.Column(db.Boolean, nullable=False, default=False)

    __table_args__ = (
        db.CheckConstraint(
            f"regra_preco_multiplos_sabores in {REGRAS_PRECO_VALIDAS!r}",
            name='ck_config_regra_preco_valida',
        ),
        db.CheckConstraint(
            f"fora_horario in {FORA_HORARIO_OPCOES_VALIDAS!r}",
            name='ck_config_fora_horario_valida',
        ),
    )

    @staticmethod
    def obter():
        from config import db as _db
        config = _db.session.get(ConfiguracaoLoja, 1)
        if config is None:
            config = ConfiguracaoLoja(id=1)
            _db.session.add(config)
            _db.session.commit()
        return config
