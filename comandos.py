"""Comandos de linha de comando da aplicação (flask --app servidor <comando>)."""
import getpass

import click

from dao.usuario_dao import UsuarioDAO
from modelos.usuario import TIPO_ADMIN
from servicos.senhas import erro_validacao_senha


def registrar_comandos(app):
    @app.cli.command('criar-admin')
    @click.option('--nome', prompt='Nome')
    @click.option('--email', prompt='E-mail')
    def criar_admin(nome, email):
        """Cria a primeira conta de administrador (o cadastro público só cria clientes)."""
        if UsuarioDAO.buscar_por_email(email):
            raise click.ClickException('Já existe uma conta com esse e-mail.')
        senha = getpass.getpass('Senha: ')
        erro = erro_validacao_senha(senha, email, nome)
        if erro:
            raise click.ClickException(erro)
        if senha != getpass.getpass('Confirme a senha: '):
            raise click.ClickException('As senhas não conferem.')
        UsuarioDAO.criar_funcionario(nome=nome, email=email, senha=senha, tipo=TIPO_ADMIN, cargo='Administrador')
        click.echo(f'Administrador {email} criado.')
