"""Convenção de data/hora do projeto: sempre UTC 'naive' (sem tzinfo).

SQLite (usado em desenvolvimento/teste) não preserva timezone-aware datetimes na
volta do banco - um valor gravado como aware volta como naive na leitura seguinte.
Comparar um datetime aware (ex.: `datetime.now(timezone.utc)`) com um naive lido do
banco (ex.: `cupom.validade_fim`) levanta `TypeError`. Para não depender de qual
coluna já passou por um ciclo de leitura, todo timestamp do sistema é naive e
representa sempre UTC - nunca hora local.
"""
from datetime import datetime, timezone


def agora_utc():
    return datetime.now(timezone.utc).replace(tzinfo=None)
