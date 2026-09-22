"""Ponto de entrada WSGI usado em produção (gunicorn app:app)."""

from servidor import app


__all__ = ['app']
