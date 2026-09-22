document.addEventListener('DOMContentLoaded', () => {
  const form = document.querySelector('.auth-form');
  if (!form) return;

  const isRegister = Boolean(form.querySelector('#confirmacao_senha'));
  const card = document.querySelector('.auth-card');
  card?.classList.add('js-reveal');
  requestAnimationFrame(() => card?.classList.add('is-visible'));

  form.querySelectorAll('input').forEach((input) => {
    input.addEventListener('focus', () => input.parentElement?.classList.add('js-pulse'));
    input.addEventListener('blur', () => input.parentElement?.classList.remove('js-pulse'));
  });

  form.addEventListener('submit', () => {
    form.classList.add('js-loading');
    const submit = form.querySelector('button[type="submit"]');
    if (submit) submit.textContent = isRegister ? 'Criando conta...' : 'Entrando...';
  });
});