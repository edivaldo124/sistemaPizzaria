"""Integrações externas opcionais: Mercado Pago, Gmail API e Google Maps."""
import base64
import json
import os
from email.message import EmailMessage
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def _config(nome):
    valor = os.environ.get(nome, '').strip()
    if not valor:
        raise IntegracaoIndisponivel(f'{nome} não configurada.')
    return valor


class IntegracaoIndisponivel(RuntimeError):
    """A integração não foi configurada no ambiente."""


class IntegracaoExternaError(RuntimeError):
    """A integração foi configurada, mas o provedor recusou a requisição."""


def _json_request(url, *, method='GET', payload=None, headers=None):
    request_headers = {'Accept': 'application/json', **(headers or {})}
    data = None
    if payload is not None:
        data = json.dumps(payload).encode('utf-8')
        request_headers.setdefault('Content-Type', 'application/json')
    request = Request(url, data=data, headers=request_headers, method=method)
    try:
        with urlopen(request, timeout=int(_config('INTEGRATION_HTTP_TIMEOUT'))) as response:
            body = response.read().decode('utf-8')
    except Exception as erro:
        raise IntegracaoExternaError('Não foi possível comunicar com o serviço externo.') from erro
    try:
        return json.loads(body) if body else {}
    except json.JSONDecodeError as erro:
        raise IntegracaoExternaError('O serviço externo retornou uma resposta inválida.') from erro


def mercado_pago_configurado():
    return bool(os.environ.get('MERCADOPAGO_ACCESS_TOKEN'))


def criar_preferencia_mercado_pago(pedido):
    token = os.environ.get('MERCADOPAGO_ACCESS_TOKEN')
    if not token:
        raise IntegracaoIndisponivel('Mercado Pago não configurado.')
    base_url = _config('PUBLIC_BASE_URL').rstrip('/')
    api_url = _config('MERCADOPAGO_API_URL').rstrip('/')

    payload = {
        'items': [{
            'id': f'pedido-{pedido.numero}',
            'title': f'Pedido {pedido.numero}',
            'quantity': 1,
            'unit_price': float(pedido.total),
            'currency_id': _config('PAYMENT_CURRENCY'),
        }],
        'external_reference': pedido.numero,
        'notification_url': f'{base_url}/pagamentos/mercadopago/webhook',
        'back_urls': {
            'success': f'{base_url}/pedidos/{pedido.numero}',
            'failure': f'{base_url}/pedidos/{pedido.numero}',
            'pending': f'{base_url}/pedidos/{pedido.numero}',
        },
        'auto_return': 'approved',
    }
    return _json_request(
        f"{api_url}{_config('MERCADOPAGO_CHECKOUT_PATH')}",
        method='POST', payload=payload,
        headers={'Authorization': f'Bearer {token}'},
    )


def consultar_pagamento_mercado_pago(pagamento_id):
    token = os.environ.get('MERCADOPAGO_ACCESS_TOKEN')
    if not token:
        raise IntegracaoIndisponivel('Mercado Pago não configurado.')
    api_url = _config('MERCADOPAGO_API_URL').rstrip('/')
    return _json_request(
        f"{api_url}{_config('MERCADOPAGO_PAYMENT_PATH').rstrip('/')}/{pagamento_id}",
        headers={'Authorization': f'Bearer {token}'},
    )


def _obter_access_token_google_oauth():
    client_id = os.environ.get('GOOGLE_CLIENT_ID', '').strip()
    client_secret = os.environ.get('GOOGLE_CLIENT_SECRET', '').strip()
    refresh_token = os.environ.get('GOOGLE_REFRESH_TOKEN', '').strip()
    if not all([client_id, client_secret, refresh_token]):
        raise IntegracaoIndisponivel('Credenciais OAuth do Google não configuradas.')

    dados = urlencode({
        'client_id': client_id,
        'client_secret': client_secret,
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token',
    }).encode('utf-8')

    request = Request(
        'https://oauth2.googleapis.com/token',
        data=dados,
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        method='POST',
    )
    try:
        with urlopen(request, timeout=int(_config('INTEGRATION_HTTP_TIMEOUT'))) as response:
            resposta = json.loads(response.read().decode('utf-8'))
    except Exception as erro:
        raise IntegracaoExternaError('Não foi possível obter o token OAuth do Google.') from erro

    token = resposta.get('access_token')
    if not token:
        raise IntegracaoExternaError('Google OAuth não retornou um access token válido.')
    return token


def gmail_configurado():
    token = os.environ.get('GMAIL_ACCESS_TOKEN', '').strip()
    oauth_configurado = all([
        os.environ.get('GOOGLE_CLIENT_ID', '').strip(),
        os.environ.get('GOOGLE_CLIENT_SECRET', '').strip(),
        os.environ.get('GOOGLE_REFRESH_TOKEN', '').strip(),
    ])
    return bool((token or oauth_configurado) and os.environ.get('GMAIL_FROM', '').strip())


def enviar_email_gmail(*, destinatario, assunto, corpo):
    token = os.environ.get('GMAIL_ACCESS_TOKEN', '').strip() or _obter_access_token_google_oauth()
    remetente = os.environ.get('GMAIL_FROM', '').strip()
    if not token or not remetente:
        raise IntegracaoIndisponivel('Gmail API não configurada.')

    mensagem = EmailMessage()
    mensagem['To'] = destinatario
    mensagem['From'] = remetente
    mensagem['Subject'] = assunto
    mensagem.set_content(corpo)
    raw = base64.urlsafe_b64encode(mensagem.as_bytes()).decode('ascii')
    api_url = _config('GMAIL_API_URL').rstrip('/')
    user_id = _config('GMAIL_USER_ID')
    return _json_request(
        f'{api_url}/users/{user_id}/messages/send',
        method='POST', payload={'raw': raw},
        headers={'Authorization': f'Bearer {token}'},
    )


def endereco_formatado(endereco):
    partes = [f'{endereco.logradouro}, {endereco.numero}', endereco.bairro, endereco.cidade]
    if endereco.uf:
        partes.append(endereco.uf)
    if endereco.cep:
        partes.append(endereco.cep)
    return ', '.join(parte for parte in partes if parte)


def calcular_rota_google_maps(endereco):
    chave = _config('GOOGLE_MAPS_API_KEY')
    origem = _config('DELIVERY_ORIGIN')

    query = urlencode({
        'origins': origem,
        'destinations': endereco_formatado(endereco),
        'key': chave,
        'language': _config('GOOGLE_MAPS_LANGUAGE'),
        'units': _config('GOOGLE_MAPS_UNITS'),
    })
    resposta = _json_request(f'{_config("GOOGLE_MAPS_API_URL")}?{query}')
    if resposta.get('status') != 'OK' or not resposta.get('rows'):
        raise IntegracaoExternaError('Google Maps não encontrou uma rota.')
    elemento = resposta['rows'][0].get('elements', [{}])[0]
    if elemento.get('status') != 'OK':
        raise IntegracaoExternaError('Google Maps não encontrou uma rota.')
    return {
        'distancia': elemento.get('distance', {}).get('text'),
        'duracao': elemento.get('duration', {}).get('text'),
    }


def url_google_maps(endereco):
    destino = urlencode({'api': 1, 'destination': endereco_formatado(endereco)})
    return f'{_config("GOOGLE_MAPS_WEB_URL").rstrip("/")}/?{destino}'
