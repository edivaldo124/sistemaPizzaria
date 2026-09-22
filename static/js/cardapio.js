document.addEventListener('DOMContentLoaded', () => {
  document.querySelector('.menu-hero')?.classList.add('js-reveal', 'is-visible');

  document.querySelectorAll('.menu-section').forEach((section, index) => {
    section.classList.add('js-reveal');
    section.style.transitionDelay = `${index * 80}ms`;
    requestAnimationFrame(() => section.classList.add('is-visible'));
  });

  document.querySelectorAll('.product-row').forEach((row, index) => {
    row.classList.add('js-reveal');
    row.style.transitionDelay = `${Math.min(index * 35, 280)}ms`;
    requestAnimationFrame(() => row.classList.add('is-visible'));

    row.querySelector('form')?.addEventListener('submit', () => {
      row.classList.add('js-loading');
      row.querySelector('button')?.classList.add('js-pulse');
    });
  });
});