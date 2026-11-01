document.addEventListener('DOMContentLoaded', () => {
  // Ações destrutivas pedem confirmação: <button data-confirmar="Texto da pergunta">
  document.querySelectorAll('[data-confirmar]').forEach((botao) => {
    botao.form?.addEventListener('submit', (evento) => {
      if (evento.submitter === botao && !window.confirm(botao.dataset.confirmar)) evento.preventDefault();
    });
  });

  // Evita envio duplo: trava o formulário enquanto a próxima página carrega.
  document.querySelectorAll('form[method="post"]').forEach((form) => {
    form.addEventListener('submit', (evento) => {
      // Espera os outros listeners: se algum cancelou o envio, não trava.
      requestAnimationFrame(() => {
        if (!evento.defaultPrevented) form.classList.add('js-loading');
      });
    });
  });

  const modal = document.getElementById('site-modal');
  const modalTitle = document.getElementById('modal-title');
  const modalBody = document.getElementById('modal-text');
  const closeButton = document.getElementById('modal-close');
  const toast = document.getElementById('site-toast');

  const openModal = (title, message) => {
    if (!modal || !modalTitle || !modalBody) return;
    modalTitle.textContent = title;
    modalBody.textContent = message;
    modal.classList.add('is-open');
    modal.setAttribute('aria-hidden', 'false');
    closeButton?.focus();
  };

  const closeModal = () => {
    if (!modal) return;
    modal.classList.remove('is-open');
    modal.setAttribute('aria-hidden', 'true');
  };

  const showToast = (message) => {
    if (!toast) return;
    toast.textContent = message;
    toast.classList.add('is-visible');
    clearTimeout(showToast.timer);
    showToast.timer = setTimeout(() => toast.classList.remove('is-visible'), 2200);
  };

  document.querySelectorAll('[data-modal-title]').forEach((button) => {
    button.addEventListener('click', () => {
      const title = button.dataset.modalTitle || 'Detalhes';
      const text = button.dataset.modalText || 'Informação disponível.';
      openModal(title, text);
    });
  });

  document.querySelectorAll('[data-toast]').forEach((button) => {
    button.addEventListener('click', () => {
      const message = button.dataset.toast || 'Ação concluída.';
      showToast(message);
    });
  });

  closeButton?.addEventListener('click', closeModal);
  modal?.addEventListener('click', (event) => {
    if (event.target === modal) closeModal();
  });
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') closeModal();
  });

  // Em Equipe (/admin/funcionarios), destaca ou recolhe os dados de veículo conforme o papel.
  const seletorPapel = document.querySelector('select[name="tipo"]');
  const grupoEntregador = document.querySelector('[data-grupo-entregador]');
  if (seletorPapel && grupoEntregador) {
    const atualizarPapel = () => {
      grupoEntregador.hidden = seletorPapel.value !== 'entregador';
    };
    seletorPapel.addEventListener('change', atualizarPapel);
    atualizarPapel();
  }
});
