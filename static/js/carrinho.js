document.addEventListener('DOMContentLoaded', () => {
  // Quantidade zero remove o item: pede confirmação antes.
  document.querySelectorAll('.sacola-item__qtd').forEach((form) => {
    form.addEventListener('submit', (evento) => {
      const quantidade = Number(form.querySelector('input[name="quantidade"]')?.value);
      if (quantidade === 0 && !window.confirm('Quantidade zero tira o item da sacola. Continuar?')) {
        evento.preventDefault();
      }
    });
  });
});
