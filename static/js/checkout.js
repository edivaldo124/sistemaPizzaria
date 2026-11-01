document.addEventListener('DOMContentLoaded', () => {
  const form = document.querySelector('.fechamento');
  if (!form) return;

  const resumo = [...form.querySelectorAll('.fechamento__dados dd')];
  const grupoEndereco = form.querySelector('[data-grupo-endereco]');
  const campoTroco = form.querySelector('[data-campo-troco]');

  const rotulo = (input) => input.closest('label')?.querySelector('strong')?.textContent.trim() || 'Selecionado';

  const atualizar = () => {
    const tipo = form.querySelector('input[name="tipo"]:checked');
    const pagamento = form.querySelector('input[name="forma_pagamento"]:checked');
    const endereco = form.querySelector('input[name="endereco_id"]:checked');

    if (tipo && resumo[0]) {
      const nomeEndereco = tipo.value === 'delivery' && endereco ? rotulo(endereco) : '';
      resumo[0].textContent = nomeEndereco ? `${rotulo(tipo)} (${nomeEndereco})` : rotulo(tipo);
    }
    if (pagamento && resumo[1]) resumo[1].textContent = rotulo(pagamento);
    if (grupoEndereco) grupoEndereco.hidden = tipo?.value === 'retirada';
    if (campoTroco) campoTroco.hidden = pagamento?.value !== 'dinheiro';
  };

  form.addEventListener('change', atualizar);
  atualizar();

  form.addEventListener('submit', () => {
    const botao = form.querySelector('button[type="submit"]');
    if (botao) botao.textContent = 'Confirmando...';
  });
});
