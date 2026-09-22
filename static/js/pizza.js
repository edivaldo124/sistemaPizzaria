document.addEventListener('DOMContentLoaded', () => {
  const builder = document.querySelector('.pizza-builder');
  if (!builder) return;

  builder.querySelectorAll('.choice-group').forEach((group, index) => {
    group.classList.add('js-reveal');
    group.style.transitionDelay = `${index * 70}ms`;
    requestAnimationFrame(() => group.classList.add('is-visible'));
  });

  const flavors = [...builder.querySelectorAll('input[name="sabores_ids"]')];
  const sizes = [...builder.querySelectorAll('input[name="tamanho_id"]')];
  const updateFlavorLimit = () => {
    const size = sizes.find((input) => input.checked)?.closest('label');
    const match = size?.textContent.match(/até\s+(\d+)/i);
    const maximum = match ? Number(match[1]) : Infinity;
    const selected = flavors.filter((input) => input.checked).length;
    flavors.forEach((input) => { input.disabled = !input.checked && selected >= maximum; });
  };

  sizes.forEach((input) => input.addEventListener('change', updateFlavorLimit));
  flavors.forEach((input) => input.addEventListener('change', () => {
    input.closest('label')?.classList.add('js-pulse');
    updateFlavorLimit();
  }));
  updateFlavorLimit();

  builder.addEventListener('submit', () => {
    builder.classList.add('js-loading');
    const submit = builder.querySelector('button[type="submit"]');
    if (submit) submit.textContent = 'Adicionando...';
  });
});