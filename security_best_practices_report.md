# Relatório de Segurança

Data da revisão: 21/09/2026  
Escopo: aplicação Flask/Python, templates Jinja, JavaScript vanilla, autenticação, sessão, carrinho, pedidos, pagamentos e integrações externas.

## Resumo executivo

Foi confirmado um problema de controle de acesso no carrinho que permite alterar ou remover itens usando apenas um `item_id` de outro carrinho. Também foi identificada uma fragilidade no webhook de pagamento, que não valida assinatura/autenticidade antes de aceitar chamadas externas.

Os controles de senha, CSRF, autorização de pedidos/endereço, rate limit de autenticação e cabeçalhos básicos estão presentes. Não foi encontrado código React neste repositório; as recomendações React foram aplicadas apenas como referência para uma futura SPA.

## Achados prioritários

### SEC-001 - IDOR no carrinho

- Regra: OWASP A01 / ASVS 5.0 8.2.1-8.3.1 / FLASK-ACCESS-001
- Severidade: **Alta**
- Status: confirmado no código
- Localização: [blueprints/carrinho_bp.py](blueprints/carrinho_bp.py#L93-L104), [dao/carrinho_dao.py](dao/carrinho_dao.py#L63-L82)
- Evidência:

```python
@carrinho_bp.route('/item/<int:item_id>/quantidade', methods=['POST'])
def atualizar_quantidade(item_id):
    CarrinhoDAO.atualizar_quantidade(item_id, quantidade)

@carrinho_bp.route('/item/<int:item_id>/remover', methods=['POST'])
def remover_item(item_id):
    CarrinhoDAO.remover_item(item_id)
```

```python
item = db.session.get(ItemCarrinho, item_id)
```

- Impacto: um usuário pode tentar IDs incrementais e modificar ou remover itens pertencentes a outro carrinho. O risco afeta visitantes e clientes autenticados; CSRF não corrige autorização de objeto.
- Correção: resolver o carrinho atual com `obter_carrinho_atual(usuario)` e atualizar/remover somente quando `item.carrinho_id == carrinho.id`. A regra deve ficar também no DAO/consulta, para não depender apenas da rota.
- Mitigação: usar identificadores públicos aleatórios e registrar tentativas de acesso a itens fora do carrinho. Isso não substitui a verificação de ownership.
- Nota: os IDs inteiros incrementais tornam a enumeração prática, mas o problema principal é a ausência de conferência de propriedade.

### SEC-002 - Webhook de pagamento sem autenticação de origem

- Regra: OWASP A08/A09 / ASVS 5.0 13.2.1 / FLASK-CSRF-001 como endpoint externo
- Severidade: **Média**
- Status: confirmado; impacto exato depende do contrato de webhook configurado no Mercado Pago
- Localização: [blueprints/pagamento_bp.py](blueprints/pagamento_bp.py#L17-L47)
- Evidência:

```python
@csrf.exempt
def webhook_mercado_pago():
    pagamento_id = dados.get('data', {}).get('id') or request.args.get('data.id')
    resposta = consultar_pagamento_mercado_pago(str(pagamento_id))
```

- Impacto: qualquer origem pode enviar chamadas repetidas com um identificador de pagamento conhecido. A consulta ao Mercado Pago impede forjar livremente o status, mas não impede replay, carga desnecessária ou processamento de notificações não autenticadas.
- Correção: validar `x-signature` e `x-request-id` conforme a documentação do Mercado Pago usando comparação constante; conferir também se `external_reference` pertence ao pedido esperado e tornar a transição de status idempotente.
- Mitigação: limitar taxa por IP/assinatura, aceitar apenas métodos e content types esperados, rejeitar payloads sem `data.id` e registrar falhas de assinatura sem expor detalhes.
- Nota: a isenção de CSRF é apropriada para um webhook externo, desde que substituída por autenticação própria do provedor.

## Achados condicionais de produção

### SEC-003 - Configuração de debug e cookie seguro pode ser promovida para produção

- Regra: OWASP A02 / FLASK-DEPLOY-002 / FLASK-SESS-001
- Severidade: **Alta se `DEBUG=true` for usado em produção; Média para o cookie**
- Status: configuração de risco; confirmar ambiente de deploy
- Localização: [servidor.py](servidor.py#L26-L35), [servidor.py](servidor.py#L137-L138), [.env.example](.env.example#L1-L11)
- Evidência:

```python
SESSION_COOKIE_SECURE=cookie_secure
...
debug=os.environ.get('DEBUG', 'false').lower() == 'true'
```

```env
DEBUG=true
COOKIE_SECURE=false
```

- Impacto: se o arquivo de exemplo for copiado sem alteração ou `DEBUG=true` chegar ao processo produtivo, o servidor de desenvolvimento/debug pode expor informações sensíveis e potencial execução remota pelo debugger. Com HTTPS, `COOKIE_SECURE=false` permite envio do cookie em conexão HTTP.
- Correção: exigir `DEBUG=false` em produção, bloquear inicialização produtiva com debug ativo, usar WSGI/ASGI de produção e derivar `SESSION_COOKIE_SECURE=true` do ambiente produtivo.
- Mitigação: pipeline deve validar variáveis antes do deploy e o proxy deve redirecionar HTTP para HTTPS.
- Nota: o `.env.example` é documentação de desenvolvimento, portanto não é prova de que a produção está vulnerável.

### SEC-004 - Hosts confiáveis não estão explicitamente configurados

- Regra: OWASP A02 / Flask 3.1 secure configuration
- Severidade: **Média**
- Status: ausência confirmada no código; verificar proteção no proxy
- Localização: [servidor.py](servidor.py#L14-L36)
- Evidência: não há configuração de `TRUSTED_HOSTS`.
- Impacto: dependendo do proxy e de como URLs absolutas são construídas, um `Host` arbitrário pode causar roteamento incorreto, links absolutos malformados ou ataques de envenenamento de host.
- Correção: configurar `TRUSTED_HOSTS` com os domínios reais em produção e rejeitar hosts desconhecidos no proxy.
- Mitigação: validar o host no balanceador/reverse proxy e não usar `request.host` sem validação para links de recuperação, callbacks ou integrações.
- Nota: o risco final depende da topologia de deploy, que não está no repositório.

### SEC-005 - Campos de autenticação sem limites de tamanho específicos

- Regra: OWASP A06/A10 / ASVS 5.0 2.2.1 e 6.3.1
- Severidade: **Média**
- Status: confirmado no fluxo
- Localização: [blueprints/auth_bp.py](blueprints/auth_bp.py#L29-L36), [blueprints/auth_bp.py](blueprints/auth_bp.py#L54-L57), [servidor.py](servidor.py#L34-L35)
- Evidência: `MAX_CONTENT_LENGTH` limita a requisição inteira a 10 MB, mas não há limite de tamanho para `senha`, `nome`, `email` e `telefone` antes do Argon2 ou das consultas.
- Impacto: requisições grandes podem consumir CPU/memória no hash Argon2, especialmente em login/cadastro, apesar do rate limit. Também podem provocar erros de banco por strings acima do tamanho das colunas.
- Correção: aplicar limites explícitos por campo antes da autenticação/hash, por exemplo senha até 256 caracteres, nome/email/telefone conforme o modelo, e rejeitar JSON que exceda o schema esperado.
- Mitigação: manter rate limit por IP e adicionar limites por conta/email, timeout e monitoramento de respostas 4xx/429.

## Controles verificados

- Senhas usam Argon2id em [servicos/senhas.py](servicos/senhas.py#L1-L24).
- Login limpa a sessão anterior e grava apenas identificadores/credencial derivada em [servicos/autorizacao.py](servicos/autorizacao.py#L39-L47).
- CSRF global está habilitado em [servidor.py](servidor.py#L38-L40), e formulários possuem token.
- As APIs de autenticação exigem CSRF via cookie e header em [blueprints/auth_bp.py](blueprints/auth_bp.py#L20-L26).
- Pedidos conferem proprietário antes de exibir em [blueprints/pedido_bp.py](blueprints/pedido_bp.py#L109-L117).
- Endereços conferem `cliente_id` antes de remover ou usar no checkout.
- Rotas administrativas usam `papel_requerido`.
- SQLAlchemy/ORM é usado no acesso observado; não foi encontrado SQL concatenado.
- CSP, `X-Content-Type-Options`, `X-Frame-Options` e `Referrer-Policy` são definidos em [servidor.py](servidor.py#L95-L108).
- No JavaScript revisado não foram encontrados `innerHTML`, `eval`, `document.write`, `postMessage` ou armazenamento de tokens.
- Integrações externas usam timeout configurável e não retornam tokens nas respostas HTML/JSON observadas.

## Limitações

Esta foi uma revisão estática do repositório e dos testes existentes. Não foram acessados o ambiente de produção, proxy, DNS, banco real, painel do Mercado Pago, logs, dependências transitivas completas ou testes de penetração externos. Os achados condicionais devem ser confirmados nos headers e variáveis do ambiente publicado.

## Skills utilizadas

1. **OWASP Security** (`owasp-security`): análise pelo OWASP Top 10 2025, ASVS 5.0, autenticação, sessão, CSRF, controle de acesso, injeção, headers e integrações externas.
2. **Security Best Practices** (`security-best-practices`): revisão específica para Python/Flask e frontend JavaScript, formato de achados, evidências com linhas, classificação de severidade e recomendações de correção.
3. Referências carregadas da skill Security Best Practices:
   - `python-flask-web-server-security.md`
   - `javascript-general-web-frontend-security.md`
   - `javascript-typescript-react-web-frontend-security.md`
