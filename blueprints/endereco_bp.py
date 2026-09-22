from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from config import db
from modelos.endereco import Endereco
from modelos.entrega import RegiaoEntrega
from servicos.autorizacao import login_requerido

endereco_bp = Blueprint('endereco', __name__, url_prefix='/enderecos')


@endereco_bp.route('/', methods=['GET', 'POST'])
@login_requerido
def listar(usuario):
    """RF04: cliente pode cadastrar mais de um endereço de entrega."""
    if usuario.cliente is None:
        abort(403)

    if request.method == 'POST':
        campos = {
            'apelido': (request.form.get('apelido') or '').strip() or None,
            'logradouro': (request.form.get('logradouro') or '').strip(),
            'numero': (request.form.get('numero') or '').strip(),
            'complemento': (request.form.get('complemento') or '').strip() or None,
            'bairro': (request.form.get('bairro') or '').strip(),
            'cidade': (request.form.get('cidade') or '').strip(),
            'uf': (request.form.get('uf') or '').strip().upper(),
            'cep': (request.form.get('cep') or '').strip() or None,
            'referencia': (request.form.get('referencia') or '').strip() or None,
        }
        regiao_entrega_id = request.form.get('regiao_entrega_id', type=int) or None

        obrigatorios = ('logradouro', 'numero', 'bairro', 'cidade', 'uf')
        if any(not campos[c] for c in obrigatorios):
            flash('Preencha logradouro, número, bairro, cidade e UF.', 'erro')
        else:
            endereco = Endereco(cliente_id=usuario.cliente.id, regiao_entrega_id=regiao_entrega_id, **campos)
            db.session.add(endereco)
            db.session.commit()
            flash('Endereço cadastrado.', 'sucesso')
        return redirect(url_for('endereco.listar'))

    return render_template(
        'auth/enderecos.html',
        enderecos=usuario.cliente.enderecos,
        regioes=RegiaoEntrega.query.filter_by(ativo=True).order_by(RegiaoEntrega.nome).all(),
    )


@endereco_bp.route('/<int:endereco_id>/remover', methods=['POST'])
@login_requerido
def remover(usuario, endereco_id):
    endereco = db.session.get(Endereco, endereco_id)
    if endereco is None or usuario.cliente is None or endereco.cliente_id != usuario.cliente.id:
        abort(404)
    db.session.delete(endereco)
    db.session.commit()
    flash('Endereço removido.', 'sucesso')
    return redirect(url_for('endereco.listar'))
