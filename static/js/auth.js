document.addEventListener('DOMContentLoaded', () => {
  const form = document.querySelector('.auth-form');
  if (!form) return;

  const cadastro = Boolean(form.querySelector('#confirmacao_senha'));
  form.addEventListener('submit', () => {
    const botao = form.querySelector('button[type="submit"]');
    if (botao) botao.textContent = cadastro ? 'Criando conta...' : 'Entrando...';
  });
});
