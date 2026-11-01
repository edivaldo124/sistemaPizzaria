// Hero da página inicial: o vídeo do forno avança conforme a rolagem (sem travar a página:
// o palco só "gruda" no topo enquanto a trilha alta passa) e as manchetes trocam por etapa.
(() => {
  const hero = document.querySelector('[data-hero]');
  if (!hero) return;

  const topo = document.querySelector('.topo');
  const trilha = hero.querySelector('.hero__trilha');
  const video = hero.querySelector('.hero__video');
  const manchetes = [...hero.querySelectorAll('[data-manchete]')];
  const num = hero.querySelector('[data-hero-num]');
  const carregando = hero.querySelector('[data-hero-carregando]');
  const reduzirMovimento = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  const limitar = (v, min, max) => Math.min(max, Math.max(min, v));

  // O topo flutua sobre o vídeo e ganha fundo claro quando o hero termina.
  const atualizarTopo = () => {
    if (!topo) return;
    topo.classList.toggle('topo--solido', hero.getBoundingClientRect().bottom <= topo.offsetHeight + 4);
  };
  window.addEventListener('scroll', atualizarTopo, { passive: true });
  window.addEventListener('resize', atualizarTopo);
  atualizarTopo();

  const esconderAbertura = () => {
    if (carregando) carregando.classList.add('is-pronto');
  };

  // Sem rolagem animada: poster, última manchete e botões à vista.
  const modoEstatico = () => {
    hero.classList.add('is-estatico');
    manchetes.forEach((m, i) => m.classList.toggle('is-ativa', i === manchetes.length - 1));
    esconderAbertura();
    atualizarTopo();
  };

  if (reduzirMovimento || !video) {
    modoEstatico();
    return;
  }

  let duracao = 0;
  let alvo = 0;
  let atual = 0;
  let ativa = -1;
  let agendado = false;
  let ultimoNumero = '';

  const progresso = () => {
    const r = trilha.getBoundingClientRect();
    const total = r.height - window.innerHeight;
    return total > 0 ? limitar(-r.top / total, 0, 1) : 0;
  };

  const mostrarManchete = (indice) => {
    if (indice === ativa) return;
    ativa = indice;
    manchetes.forEach((m, i) => {
      m.classList.toggle('is-ativa', i === indice);
      m.classList.toggle('is-saiu', i < indice);
      m.setAttribute('aria-hidden', i === indice ? 'false' : 'true');
    });
    hero.classList.toggle('is-final', indice === manchetes.length - 1);
  };

  const quadro = () => {
    agendado = false;
    alvo = progresso();
    atual += (alvo - atual) * 0.2;
    if (Math.abs(alvo - atual) < 0.0004) atual = alvo;

    if (duracao && !video.seeking) {
      const tempo = atual * (duracao - 0.04);
      if (Math.abs(video.currentTime - tempo) > 0.016) {
        if (typeof video.fastSeek === 'function') video.fastSeek(tempo);
        else video.currentTime = tempo;
      }
    }

    mostrarManchete(Math.min(manchetes.length - 1, Math.floor(alvo * manchetes.length)));
    hero.classList.toggle('is-rolando', alvo > 0.01);
    hero.style.setProperty('--p', atual.toFixed(4));
    const texto = String(Math.round(atual * 100)).padStart(2, '0');
    if (num && texto !== ultimoNumero) {
      num.textContent = texto;
      ultimoNumero = texto;
    }

    if (atual !== alvo) pedirQuadro();
  };

  function pedirQuadro() {
    if (agendado) return;
    agendado = true;
    window.requestAnimationFrame(quadro);
  }

  window.addEventListener('scroll', pedirQuadro, { passive: true });
  window.addEventListener('resize', pedirQuadro);

  let pronto = false;
  const aoCarregar = () => {
    if (pronto) return;
    pronto = true;
    duracao = video.duration || 0;
    // Safari/iOS só libera a busca por quadros depois de uma reprodução curta.
    const tentativa = video.play();
    if (tentativa && typeof tentativa.then === 'function') {
      tentativa.then(() => video.pause()).catch(() => {});
    }
    esconderAbertura();
    pedirQuadro();
  };

  video.addEventListener('loadeddata', aoCarregar);
  if (video.readyState >= 2) aoCarregar();

  // Se o vídeo não carregar em 4 s, o hero vira estático em vez de ficar preso na abertura.
  window.setTimeout(() => {
    if (!pronto) modoEstatico();
  }, 4000);
  video.addEventListener('error', modoEstatico);

  mostrarManchete(0);
  pedirQuadro();
})();
