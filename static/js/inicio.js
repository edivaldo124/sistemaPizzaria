/**
 * Mandacaru Pizzaria - Hero com vídeo scrubbeado por rolagem.
 * Port vanilla fiel da lógica React.
 */
(() => {
  function inicializarVideoHero() {
    const hero = document.querySelector('[data-video-hero]');
    if (!hero) return;

    const video = hero.querySelector('.video-hero__video');
    const titleEl = hero.querySelector('[data-hero-title]');
    const taglineEl = hero.querySelector('[data-hero-tagline]');
    const hintEl = hero.querySelector('[data-hero-hint]');
    const progressBarEl = hero.querySelector('[data-hero-progress]');
    const skipLinkEl = hero.querySelector('[data-hero-skip]');

    // Posiciona o botão "Ver cardápio" abaixo do cabeçalho, que muda de altura no mobile.
    const cabecalho = document.querySelector('.site-header');
    function atualizarAlturaCabecalho() {
      if (cabecalho) hero.style.setProperty('--altura-cabecalho', `${cabecalho.offsetHeight}px`);
    }
    atualizarAlturaCabecalho();
    window.addEventListener('resize', atualizarAlturaCabecalho);

    const scrubDistance = parseFloat(hero.dataset.scrubDistance) || 2400;
    const unlockThreshold = parseFloat(hero.dataset.unlockThreshold) || 220;

    // Estado do scrubber
    let duration = 0;
    let targetProgress = 0;
    let currentProgress = 0;
    let hasStartedScrolling = false;
    let isSeeking = false;
    let pendingTime = null;
    let locked = false;
    let lockedScrollY = 0;
    let touchStartY = 0;
    let overflowForward = 0;
    let completed = false;
    let rafId = null;

    // Detecção de introdução já vista ou preferência de movimento reduzido
    let skipIntro = false;
    try {
      if (sessionStorage.getItem('intro_vista') === '1') {
        skipIntro = true;
      }
    } catch (e) {}

    if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      skipIntro = true;
    }

    function applyStaticEndState() {
      if (titleEl) {
        titleEl.style.opacity = '0';
        titleEl.style.visibility = 'hidden';
        titleEl.style.pointerEvents = 'none';
      }
      if (taglineEl) {
        taglineEl.style.opacity = '1';
        taglineEl.style.visibility = 'visible';
        taglineEl.style.transform = 'translate3d(0, 0, 0)';
      }
      if (hintEl) {
        hintEl.style.opacity = '0';
        hintEl.style.visibility = 'hidden';
        hintEl.style.pointerEvents = 'none';
      }
      if (progressBarEl) {
        progressBarEl.style.transform = 'scaleX(1)';
      }
      if (hero) {
        hero.classList.remove('video-hero--locked');
      }
    }

    function engageLock() {
      if (locked || skipIntro) return;
      locked = true;
      lockedScrollY = window.scrollY || window.pageYOffset || 0;
      document.body.style.position = 'fixed';
      document.body.style.top = `-${lockedScrollY}px`;
      document.body.style.left = '0';
      document.body.style.right = '0';
      document.body.style.width = '100%';
      document.body.style.overscrollBehavior = 'none';
      hero.classList.add('video-hero--locked');
    }

    function releaseLock() {
      if (!locked) return;
      locked = false;
      const y = lockedScrollY;
      document.body.style.position = '';
      document.body.style.top = '';
      document.body.style.left = '';
      document.body.style.right = '';
      document.body.style.width = '';
      document.body.style.overscrollBehavior = '';
      hero.classList.remove('video-hero--locked');
      window.scrollTo(0, y);
    }

    function seekTo(time) {
      if (!video || !duration || isNaN(time)) return;
      const clampedTime = Math.min(Math.max(time, 0), duration);
      if (isSeeking) {
        pendingTime = clampedTime;
        return;
      }
      if (Math.abs(video.currentTime - clampedTime) < 0.01) {
        return;
      }
      isSeeking = true;
      try {
        video.currentTime = clampedTime;
      } catch (err) {
        isSeeking = false;
      }
    }

    if (video) {
      video.addEventListener('seeked', () => {
        isSeeking = false;
        if (pendingTime !== null) {
          const nextTime = pendingTime;
          pendingTime = null;
          seekTo(nextTime);
        }
      });
    }

    function addDelta(deltaY) {
      if (!locked) return;

      if (targetProgress >= 1 && deltaY > 0) {
        overflowForward += deltaY;
        if (overflowForward >= unlockThreshold) {
          releaseLock();
          overflowForward = 0;
          if (!completed) {
            completed = true;
            try {
              sessionStorage.setItem('intro_vista', '1');
            } catch (e) {}
          }
          return;
        }
      } else if (deltaY < 0) {
        overflowForward = 0;
      }

      const next = Math.min(Math.max(targetProgress + deltaY / scrubDistance, 0), 1);
      targetProgress = next;
      if (targetProgress > 0.001) {
        hasStartedScrolling = true;
      }
    }

    // Interações de rolagem (wheel)
    window.addEventListener('wheel', (e) => {
      if (skipIntro) return;
      const deltaY = e.deltaY;
      if (locked) {
        e.preventDefault();
        addDelta(deltaY);
      } else if (deltaY < 0 && (window.scrollY || window.pageYOffset || 0) <= 0) {
        e.preventDefault();
        engageLock();
        targetProgress = 1;
        currentProgress = 1;
        overflowForward = 0;
      }
    }, { passive: false });

    // Interações de toque móvel (touch)
    window.addEventListener('touchstart', (e) => {
      if (skipIntro) return;
      if (e.touches && e.touches.length > 0) {
        touchStartY = e.touches[0].clientY;
      }
    }, { passive: true });

    window.addEventListener('touchmove', (e) => {
      if (skipIntro) return;
      if (!e.touches || e.touches.length === 0) return;
      const currentY = e.touches[0].clientY;
      const deltaY = touchStartY - currentY;
      touchStartY = currentY;

      if (locked) {
        e.preventDefault();
        addDelta(deltaY);
      } else if (deltaY < 0 && (window.scrollY || window.pageYOffset || 0) <= 0) {
        e.preventDefault();
        engageLock();
        targetProgress = 1;
        currentProgress = 1;
        overflowForward = 0;
      }
    }, { passive: false });

    // Navegação por teclado acessível
    window.addEventListener('keydown', (e) => {
      if (!locked || skipIntro) return;

      const active = document.activeElement;
      if (active) {
        const tag = active.tagName ? active.tagName.toLowerCase() : '';
        if (
          tag === 'input' ||
          tag === 'button' ||
          tag === 'textarea' ||
          tag === 'select' ||
          active.closest('a') ||
          active.closest('[data-hero-skip]')
        ) {
          return;
        }
      }

      let delta = 0;
      switch (e.key) {
        case 'ArrowDown':
          delta = 120;
          break;
        case 'ArrowUp':
          delta = -120;
          break;
        case 'PageDown':
        case ' ': // Espaço
          delta = 600;
          break;
        case 'PageUp':
          delta = -600;
          break;
        case 'Home':
          delta = -scrubDistance;
          break;
        case 'End':
          delta = scrubDistance;
          break;
        default:
          return;
      }

      e.preventDefault();
      addDelta(delta);
    });

    // Loop de renderização com requestAnimationFrame
    function tick() {
      if (skipIntro) return;

      currentProgress += (targetProgress - currentProgress) * 0.18;

      if (duration > 0) {
        seekTo(currentProgress * duration);
      }

      if (video) {
        const scale = 1 + currentProgress * 0.06;
        video.style.transform = `scale(${scale.toFixed(4)})`;
      }

      // Título: fade de opacidade, translate e blur nos primeiros 35%
      if (titleEl) {
        const titleProgress = Math.min(Math.max(currentProgress / 0.35, 0), 1);
        const opacity = 1 - titleProgress;
        const translateY = -(titleProgress * 30);
        const blur = titleProgress * 8;
        titleEl.style.opacity = opacity.toFixed(3);
        titleEl.style.transform = `translate3d(0, ${translateY.toFixed(1)}px, 0)`;
        titleEl.style.filter = blur > 0.1 ? `blur(${blur.toFixed(1)}px)` : 'none';
        titleEl.style.visibility = opacity < 0.01 ? 'hidden' : 'visible';
      }

      // Dica de rolagem: oculta assim que inicia
      if (hintEl) {
        if (hasStartedScrolling || currentProgress > 0.01) {
          hintEl.style.opacity = '0';
          hintEl.style.pointerEvents = 'none';
        } else {
          hintEl.style.opacity = '1';
          hintEl.style.pointerEvents = 'auto';
        }
      }

      // Tagline: surge entre 82% e 100%
      if (taglineEl) {
        const taglineProgress = Math.min(Math.max((currentProgress - 0.82) / 0.18, 0), 1);
        taglineEl.style.opacity = taglineProgress.toFixed(3);
        taglineEl.style.transform = `translate3d(0, ${((1 - taglineProgress) * 16).toFixed(1)}px, 0)`;
        taglineEl.style.visibility = taglineProgress < 0.01 ? 'hidden' : 'visible';
      }

      // Barra de progresso inferior
      if (progressBarEl) {
        progressBarEl.style.transform = `scaleX(${currentProgress.toFixed(4)})`;
      }

      rafId = requestAnimationFrame(tick);
    }

    // Carregamento do vídeo e iOS priming
    let isReady = false;
    function markReady() {
      if (isReady) return;
      isReady = true;

      duration = (video && video.duration) ? video.duration : 0;
      if (video) {
        video.classList.add('is-ready');

        // Priming para reprodução no iOS
        const p = video.play();
        if (p && typeof p.then === 'function') {
          p.then(() => video.pause()).catch(() => {});
        }
      }

      if (skipIntro) {
        if (video && duration > 0) {
          video.currentTime = Math.max(0, duration - 0.05);
        }
        applyStaticEndState();
      } else {
        if ((window.scrollY || window.pageYOffset || 0) <= 10) {
          engageLock();
        }
        rafId = requestAnimationFrame(tick);
      }
    }

    if (video) {
      video.addEventListener('loadedmetadata', () => {
        if (video.duration && !isNaN(video.duration)) duration = video.duration;
      });
      video.addEventListener('loadeddata', () => {
        if (video.duration && !isNaN(video.duration)) duration = video.duration;
        video.classList.add('is-ready');
        if (skipIntro && duration > 0) video.currentTime = Math.max(0, duration - 0.05);
      });

      video.addEventListener('error', () => {
        skipIntro = true;
        releaseLock();
        if (rafId) {
          cancelAnimationFrame(rafId);
          rafId = null;
        }
        applyStaticEndState();
      });

      if (video.readyState >= 2 && !isNaN(video.duration)) {
        markReady();
      } else {
        video.addEventListener('loadeddata', markReady, { once: true });
        // Fallback defensivo caso o vídeo demore excessivamente para carregar
        setTimeout(() => {
          if (!isReady) {
            markReady();
          }
        }, 3500);
      }
    } else {
      markReady();
    }

    // Limpeza em pagehide / beforeunload para evitar travamento do body
    function cleanup() {
      releaseLock();
      if (rafId) {
        cancelAnimationFrame(rafId);
        rafId = null;
      }
    }

    window.addEventListener('pagehide', cleanup);
    window.addEventListener('beforeunload', cleanup);

    // Suporte a bfcache (pageshow com persisted)
    window.addEventListener('pageshow', (event) => {
      if (event.persisted) {
        skipIntro = true;
        releaseLock();
        if (rafId) {
          cancelAnimationFrame(rafId);
          rafId = null;
        }
        applyStaticEndState();
      }
    });

    // Clique em "Ver cardápio" libera o lock antes de navegar
    if (skipLinkEl) {
      skipLinkEl.addEventListener('click', () => {
        releaseLock();
      });
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', inicializarVideoHero);
  } else {
    inicializarVideoHero();
  }
})();
