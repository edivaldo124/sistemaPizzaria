document.addEventListener('DOMContentLoaded', () => {
  document.body.classList.add('page-ready');

  const revealObserver = new IntersectionObserver((entries, observer) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      entry.target.classList.add('is-visible');
      observer.unobserve(entry.target);
    });
  }, { threshold: 0.12 });

  document.querySelectorAll('.js-reveal').forEach((element) => revealObserver.observe(element));

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
});
