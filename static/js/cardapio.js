document.addEventListener('DOMContentLoaded', () => {
  // Resposta imediata ao adicionar: o botão confirma enquanto a página recarrega.
  document.querySelectorAll('.cardapio-item__form').forEach((form) => {
    form.addEventListener('submit', () => {
      const botao = form.querySelector('button');
      if (botao) botao.textContent = 'Adicionando...';
    });
  });
});
