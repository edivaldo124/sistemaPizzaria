# AGENTS.md

## Visão geral do projeto
Este repositório é uma aplicação web Flask para gestão de pizzaria, com rotas em `blueprints/`, modelos de domínio em `modelos/`, acesso a dados em `dao/`, regras de negócio em `servicos/` e templates em `templates/`.

A aplicação é iniciada em `servidor.py` e a configuração global fica em `config.py`.

## Como trabalhar no código
- Preserve a separação de responsabilidades:
  - `blueprints/`: endpoints HTTP e fluxo de requisição
  - `servicos/`: regras de negócio, validações e transformações
  - `dao/`: consultas e operações persistentes
  - `modelos/`: entidades SQLAlchemy
  - `templates/`: HTML/Jinja
  - `tests/`: testes automatizados
- Prefira atualizar a camada certa em vez de misturar regras de negócio com código de rota.
- Quando alterar o esquema do banco, revise `migrations/` e mantenha compatibilidade com o modelo atual.
- O arquivo `servidor.py` importa todos os modelos antes das migrações, então não remova imports sem entender o impacto.

## Ambiente e comandos
Use o ambiente virtual do projeto antes de rodar comandos:

```bash
cd /home/edivaldo/PycharmProjects/SistemaPizzariaTO
source venv/bin/activate
```

Testes:

```bash
pytest -q
```

Se for testar um conjunto específico:

```bash
pytest tests/test_regras_pedido.py -q
```

## Variáveis de ambiente e configuração
A aplicação espera variáveis fundamentais em runtime:
- `SECRET_KEY`
- `DATABASE_URL`
- `COOKIE_SECURE`
- `RATELIMIT_STORAGE_URI`

No ambiente de testes, `tests/conftest.py` já define valores seguros para uso em memória (`sqlite:///:memory:`).

## Convenções do projeto
- A lógica de autenticação e autorização fica em `servicos/autorizacao.py` e em `dao/usuario_dao.py`.
- O sistema usa Flask-Limiter em rotas sensíveis (login, cadastro, ações de pedido).
- O padrão de validação de regras de negócio geralmente aparece em `servicos/` e é testado em `tests/`.
- Os templates usam Jinja e a aplicação registra filtros globais em `servidor.py`.

## Testes e validação
- Escreva/ajuste testes para cobrir a regra alterada antes de considerar a correção concluída.
- A suíte usa `pytest` e a fixture `app` expõe a aplicação Flask em contexto de teste.
- Quando mexer em regras de pedido, cupom, entrega ou autorização, priorize os testes em `tests/test_regras_pedido.py` e os módulos relacionados.

## Observações importantes
- O projeto não possui documentação central de arquitetura no repositório, então a estrutura acima é a referência mais importante para agentes automatizados.
- Mantenha nomes em português e siga o estilo já usado no código e nos templates.
- Antes de introduzir bibliotecas novas, confirme se o projeto já usa uma solução equivalente no mesmo domínio.
