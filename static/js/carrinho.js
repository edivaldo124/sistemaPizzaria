document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.cart-table tbody tr').forEach((row, index) => {
    row.classList.add('js-reveal');
    row.style.transitionDelay = `${Math.min(index * 50, 250)}ms`;
    requestAnimationFrame(() => row.classList.add('is-visible'));
  });

  document.querySelectorAll('.qty-form, .cart-table td:last-child form').forEach((form) => {
    form.addEventListener('submit', () => {
      form.closest('tr')?.classList.add('js-loading');
      form.querySelector('button')?.classList.add('js-pulse');
    });
  });
});