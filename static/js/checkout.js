document.addEventListener('DOMContentLoaded', () => {
  const form = document.querySelector('.checkout-form');
  if (!form) return;

  form.querySelectorAll('.checkout-fieldset, .field-stack').forEach((section, index) => {
    section.classList.add('js-reveal');
    section.style.transitionDelay = `${index * 65}ms`;
    requestAnimationFrame(() => section.classList.add('is-visible'));
  });

  const paymentSummary = [...document.querySelectorAll('.summary-row strong')][1];
  form.querySelectorAll('input[name="forma_pagamento"]').forEach((input) => {
    input.addEventListener('change', () => {
      if (paymentSummary) paymentSummary.textContent = input.closest('label')?.textContent.trim() || 'Selecionado';
    });
  });

  form.addEventListener('submit', () => {
    form.classList.add('js-loading');
    const submit = form.querySelector('button[type="submit"]');
    if (submit) submit.textContent = 'Confirmando...';
  });
});