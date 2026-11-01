// Tela "Monte sua pizza": limita os sabores ao tamanho, resume a escolha e monta a pizza na tela.
// A pizza começa só com a massa. O tamanho a faz crescer; o primeiro sabor espalha o molho e
// derrete o queijo; cada sabor joga os próprios ingredientes na sua parte da pizza; a borda
// recheada é confeitada em volta. As fotos ficam em static/imagens/pizza/ e são recortadas por
// scripts/preparar_ingredientes.py. Sem JavaScript, o formulário funciona igual e a massa fica à vista.
document.addEventListener('DOMContentLoaded', () => {
  const montador = document.querySelector('.montador');
  if (!montador) return;

  const tamanhos = [...montador.querySelectorAll('input[name="tamanho_id"]')];
  const sabores = [...montador.querySelectorAll('input[name="sabores_ids"]')];
  const dica = montador.querySelector('[data-limite-sabores]');
  const palco = montador.querySelector('[data-palco]');
  const resumo = palco && palco.querySelector('[data-resumo]');
  const etiquetas = palco && palco.querySelector('[data-etiquetas]');
  const reduzirMovimento = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Limita os sabores ao máximo do tamanho escolhido; o servidor valida de novo.
  const atualizarLimite = () => {
    const tamanho = tamanhos.find((input) => input.checked);
    const maximo = tamanho ? Number(tamanho.dataset.maxSabores) : Infinity;
    const escolhidos = sabores.filter((input) => input.checked).length;
    sabores.forEach((input) => { input.disabled = !input.checked && escolhidos >= maximo; });

    if (!dica) return;
    if (!tamanho) {
      dica.textContent = 'Escolha o tamanho para ver quantos sabores cabem.';
    } else {
      const restam = Math.max(maximo - escolhidos, 0);
      dica.textContent = restam
        ? `Escolhidos ${escolhidos} de ${maximo}. Ainda cabe${restam > 1 ? 'm' : ''} ${restam}.`
        : `Escolhidos ${escolhidos} de ${maximo}. Para trocar, desmarque um sabor.`;
    }
  };

  // ---------- Estado da pizza, lido do formulário ----------

  const marcados = (nome) => [...montador.querySelectorAll(`input[name="${nome}"]:checked`)];

  const lerEstado = () => {
    const tamanho = tamanhos.find((input) => input.checked);
    const massa = marcados('massa_id')[0];
    const borda = marcados('borda_id')[0];
    return {
      tamanho: tamanho ? { nome: tamanho.dataset.nome, posicao: tamanhos.indexOf(tamanho) } : null,
      sabores: marcados('sabores_ids').map((i) => ({ id: i.value, nome: i.dataset.nome, detalhe: i.dataset.detalhe })),
      massa: massa && massa.value ? { nome: massa.dataset.nome } : null,
      borda: borda && borda.value ? { nome: borda.dataset.nome } : null,
      adicionais: marcados('adicionais_ids').map((i) => ({ id: i.value, nome: i.dataset.nome })),
    };
  };

  const descrever = (e) => {
    if (!e.tamanho) return 'Escolha o tamanho para começar.';
    const partes = [e.tamanho.nome];
    partes.push(e.sabores.length ? e.sabores.map((s) => s.nome).join(' e ') : 'sem sabor ainda');
    if (e.massa) partes.push(`massa ${e.massa.nome.toLowerCase()}`);
    if (e.borda) partes.push(`borda ${e.borda.nome.toLowerCase()}`);
    if (e.adicionais.length) partes.push(`+ ${e.adicionais.map((a) => a.nome.toLowerCase()).join(', ')}`);
    return partes.join(' · ');
  };

  // ---------- Etiquetas "+ ingrediente" sobre a pizza ----------

  const chaves = (e) => {
    const mapa = new Map();
    e.sabores.forEach((s) => mapa.set(`s${s.id}`, s.nome));
    if (e.massa) mapa.set('m', `Massa ${e.massa.nome.toLowerCase()}`);
    if (e.borda) mapa.set('b', `Borda ${e.borda.nome.toLowerCase()}`);
    e.adicionais.forEach((a) => mapa.set(`a${a.id}`, a.nome));
    return mapa;
  };

  const mostrarEtiqueta = (texto, tipo) => {
    if (!etiquetas || reduzirMovimento) return;
    while (etiquetas.children.length >= 3) etiquetas.firstElementChild.remove();
    const el = document.createElement('span');
    el.className = `palco__etiqueta palco__etiqueta--${tipo}`;
    el.textContent = `${tipo === 'entrou' ? '+' : '−'} ${texto}`;
    etiquetas.appendChild(el);
    el.addEventListener('animationend', () => el.remove());
  };

  // ---------- O que cada sabor leva ----------

  // tam: diâmetro da peça em fração da pizza. qtd: peças numa pizza inteira.
  // camada: 1 fica por baixo, 3 por cima (folhas e temperos).
  const INGREDIENTES = {
    calabresa: { tam: 0.1, qtd: 16, camada: 1 },
    pepperoni: { tam: 0.1, qtd: 15, camada: 1 },
    presunto: { tam: 0.11, qtd: 11, camada: 1 },
    mussarela: { tam: 0.11, qtd: 9, camada: 1 },
    tomate: { tam: 0.1, qtd: 9, camada: 1 },
    banana: { tam: 0.085, qtd: 12, camada: 1 },
    frango: { tam: 0.1, qtd: 13, camada: 1 },
    carnesol: { tam: 0.1, qtd: 13, camada: 1 },
    atum: { tam: 0.095, qtd: 12, camada: 1 },
    ovo: { tam: 0.09, qtd: 7, camada: 2 },
    bacon: { tam: 0.095, qtd: 12, camada: 2 },
    cogumelo: { tam: 0.09, qtd: 13, camada: 2 },
    cebola: { tam: 0.085, qtd: 10, camada: 2 },
    cebolaroxa: { tam: 0.085, qtd: 10, camada: 2 },
    cebolacar: { tam: 0.085, qtd: 11, camada: 2 },
    pimentao: { tam: 0.09, qtd: 10, camada: 2 },
    palmito: { tam: 0.07, qtd: 10, camada: 2 },
    coalho: { tam: 0.065, qtd: 12, camada: 2 },
    provolone: { tam: 0.06, qtd: 13, camada: 2 },
    gorgonzola: { tam: 0.07, qtd: 12, camada: 2 },
    parmesao: { tam: 0.08, qtd: 11, camada: 2 },
    catupiry: { tam: 0.085, qtd: 10, camada: 2 },
    pequi: { tam: 0.065, qtd: 13, camada: 2 },
    azeitona: { tam: 0.058, qtd: 12, camada: 2 },
    milho: { tam: 0.075, qtd: 12, camada: 2 },
    ervilha: { tam: 0.065, qtd: 12, camada: 2 },
    brocolis: { tam: 0.085, qtd: 10, camada: 2 },
    morango: { tam: 0.075, qtd: 12, camada: 2 },
    granulado: { tam: 0.08, qtd: 12, camada: 3 },
    manjericao: { tam: 0.075, qtd: 8, camada: 3 },
    rucula: { tam: 0.09, qtd: 10, camada: 3 },
    oregano: { tam: 0.07, qtd: 9, camada: 3 },
  };

  // O texto do cadastro (nome + descrição) é lido por palavras-chave: sabor novo criado no
  // painel também aparece na pizza. A ordem é a prioridade quando o texto cita muita coisa.
  const PALAVRAS = [
    ['pepperoni', /pepperoni/],
    ['calabresa', /calabresa|linguica|salame/],
    ['presunto', /presunto|peito de peru|apresuntado|lombo/],
    ['bacon', /bacon/],
    ['frango', /frango|galinha/],
    ['carnesol', /carne de sol|carne seca|charque|costela|\bcarne\b/],
    ['atum', /atum|sardinha/],
    ['pequi', /pequi/],
    ['cogumelo', /cogumelo|champignon|shiitake|shimeji/],
    ['tomate', /tomate/],
    ['cebolacar', /cebola carameliz/],
    ['cebolaroxa', /cebola roxa/],
    ['cebola', /cebola(?! roxa| carameliz)/],
    ['azeitona', /azeitona/],
    ['ovo', /\bovos?\b/],
    ['ervilha', /ervilha/],
    ['milho', /milho/],
    ['pimentao', /pimentao|pimenta/],
    ['brocolis', /brocolis/],
    ['palmito', /palmito/],
    ['banana', /banana/],
    ['morango', /morango/],
    ['granulado', /granulado|confeito|brigadeiro/],
    ['catupiry', /catupiry|requeijao|cream cheese/],
    ['coalho', /coalho/],
    ['gorgonzola', /gorgonzola/],
    ['parmesao', /parmesao/],
    ['provolone', /provolone/],
    ['mussarela', /mussarela|mucarela|queijo(?! coalho)/],
    ['manjericao', /manjericao|basilico/],
    ['rucula', /rucula/],
    ['oregano', /oregano/],
  ];
  const DOCE = /chocolate|brigadeiro|nutella|doce de leite|banana|morango|goiabada|romeu|prestigio|leite condensado|sensacao/;
  const CHOCOLATE = /chocolate|brigadeiro|nutella|prestigio|sensacao/;

  const semAcento = (t) => (t || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();

  const lerSabor = (nome, detalhe, limite) => {
    // "molho de tomate" é a base, não cobertura.
    const texto = semAcento(`${nome} ${detalhe || ''}`).replace(/molho (de|a) tomate|molho/g, ' ');
    const tipos = PALAVRAS.filter(([, regra]) => regra.test(texto)).map(([chave]) => chave).slice(0, limite);
    const doce = DOCE.test(texto);
    return {
      tipos: tipos.length ? tipos : [doce ? 'granulado' : 'oregano'],
      base: CHOCOLATE.test(texto) ? 'chocolate' : (doce ? 'queijo' : 'molho'),
    };
  };

  // ---------- Posições das peças ----------

  const VOLTA = Math.PI * 2;
  const RAIO = 0.35; // até onde vão as coberturas, em fração do diâmetro (fica dentro do queijo)

  const aleatorio = (semente) => {
    let a = semente >>> 0;
    return () => {
      a = (a + 0x6d2b79f5) >>> 0;
      let t = a;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  };
  const semente = (texto) => {
    let h = 2166136261;
    for (let i = 0; i < texto.length; i += 1) {
      h ^= texto.charCodeAt(i);
      h = Math.imul(h, 16777619);
    }
    return h >>> 0;
  };

  // Mesma escolha, mesma pizza: a semente vem do sabor. Peças da mesma camada não se encostam.
  const dispor = (setores, extras) => {
    const ocupados = { 1: [], 2: [], 3: [] };
    const pecas = [];
    const colocar = (chave, tipos, a0, a1, fator) => {
      const rnd = aleatorio(semente(chave));
      const inteira = a1 - a0 > VOLTA - 0.01;
      tipos.forEach((tipo) => {
        const def = INGREDIENTES[tipo];
        const total = Math.max(2, Math.round(def.qtd * ((a1 - a0) / VOLTA) * fator));
        const vizinhos = def.camada === 1 ? ocupados[1] : [...ocupados[1], ...ocupados[def.camada]];
        let feitos = 0;
        for (let tentativa = 0; tentativa < total * 14 && feitos < total; tentativa += 1) {
          const folga = tentativa > total * 7 ? 0.62 : 1;
          const r = Math.sqrt(0.004 + rnd() * 0.996) * RAIO;
          const ang = a0 + rnd() * (a1 - a0);
          if (!inteira) {
            const ate = Math.min(ang - a0, a1 - ang);
            if (r * Math.sin(Math.min(ate, Math.PI / 2)) < def.tam * 0.42) continue;
          }
          const x = 0.5 + Math.cos(ang) * r;
          const y = 0.5 + Math.sin(ang) * r;
          const dist = def.tam * (def.camada === 3 ? 0.55 : 0.82);
          if (vizinhos.some((o) => Math.hypot(o.x - x, o.y - y) < (dist + o.dist) * 0.5 * folga)) continue;
          const ponto = { x, y, dist };
          ocupados[def.camada].push(ponto);
          if (def.camada !== 1) vizinhos.push(ponto);
          pecas.push({
            id: `${chave}:${tipo}:${feitos}`, tipo, x, y, giro: rnd() * 360, escala: 0.88 + rnd() * 0.24, variacao: Math.floor(rnd() * 4),
          });
          feitos += 1;
        }
      });
    };
    const n = setores.length;
    setores.forEach((s, i) => colocar(`s${s.id}`, s.tipos, (i / n) * VOLTA - VOLTA / 4, ((i + 1) / n) * VOLTA - VOLTA / 4, 1));
    extras.forEach((e) => colocar(`a${e.id}`, e.tipos, 0, VOLTA, 0.55));
    return pecas;
  };

  // ---------- Palco ----------

  const pizza = palco && palco.querySelector('[data-pizza]');
  const massa = palco && palco.querySelector('[data-massa]');
  const pasta = palco ? palco.dataset.imagens : '';
  const animar = (el, quadros, opcoes) => (reduzirMovimento || !el.animate ? null : el.animate(quadros, opcoes));

  const criar = (tag, classe) => {
    const el = document.createElement(tag);
    el.className = classe;
    return el;
  };
  const camadaFoto = (nome, classe) => {
    const img = criar('img', `palco__camada ${classe}`);
    img.alt = '';
    img.decoding = 'async';
    img.src = `${pasta}${nome}.webp`;
    img.hidden = true;
    return img;
  };

  let bases = null;
  let coberturas = null;
  let borda = null;
  if (pizza) {
    bases = {
      molho: camadaFoto('molho', 'palco__molho'),
      chocolate: camadaFoto('chocolate', 'palco__chocolate'),
      queijo: camadaFoto('queijo', 'palco__queijo'),
    };
    pizza.append(bases.molho, bases.chocolate, bases.queijo);
    coberturas = [1, 2, 3].map(() => pizza.appendChild(criar('div', 'palco__coberturas')));
    borda = pizza.appendChild(criar('div', 'palco__coberturas palco__borda'));
  }

  // Cada foto de ingrediente é baixada uma vez, só quando algum sabor precisa dela.
  const carregadas = new Map();
  const carregar = (nome) => {
    if (!carregadas.has(nome)) {
      const img = new Image();
      img.src = `${pasta}${nome}.webp`;
      const pronta = img.decode ? img.decode().catch(() => {}) : new Promise((ok) => { img.onload = ok; img.onerror = ok; });
      carregadas.set(nome, pronta);
    }
    return carregadas.get(nome);
  };

  // Base por setor (molho, chocolate ou só queijo), com máscara cônica do tamanho de cada sabor.
  const mascara = (setores, quer) => {
    const n = setores.length;
    const com = setores.filter(quer).length;
    if (!com) return null;
    if (com === n) return 'none';
    const partes = setores.map((s, i) => `${quer(s) ? '#000' : 'transparent'} ${(i / n) * 360}deg ${((i + 1) / n) * 360}deg`);
    return `conic-gradient(${partes.join(', ')})`;
  };

  // Estado de cada base (aparecendo ou não), separado do atributo hidden, que só muda no fim da saída.
  const versoes = new WeakMap();
  const ligadas = new WeakMap();
  const mostrarBase = (el, valorMascara, entrada, atraso) => {
    const versao = (versoes.get(el) || 0) + 1;
    versoes.set(el, versao);
    if (valorMascara === null) {
      if (!ligadas.get(el)) return false;
      ligadas.set(el, false);
      const saida = animar(el, [{ opacity: 1 }, { opacity: 0 }], { duration: 260, easing: 'ease-in' });
      const esconder = () => { if (versoes.get(el) === versao) el.hidden = true; };
      if (saida) saida.finished.then(esconder, esconder);
      else esconder();
      return false;
    }
    el.style.webkitMaskImage = valorMascara;
    el.style.maskImage = valorMascara;
    if (ligadas.get(el)) return false;
    ligadas.set(el, true);
    if (el.getAnimations) el.getAnimations().forEach((animacao) => animacao.cancel());
    el.hidden = false;
    animar(el, entrada, { duration: 900, delay: atraso, easing: 'cubic-bezier(0.22, 0.8, 0.3, 1)', fill: 'backwards' });
    return true;
  };

  // O molho e o chocolate se espalham em espiral; o queijo derrete por cima.
  const ESPALHAR = [
    { clipPath: 'circle(0% at 50% 50%)', transform: 'rotate(-120deg) scale(0.9)' },
    { clipPath: 'circle(72% at 50% 50%)', transform: 'none' },
  ];
  const DERRETER = [
    { opacity: 0, transform: 'scale(0.9)', filter: 'blur(6px) brightness(1.25)' },
    { opacity: 1, transform: 'none', filter: 'none' },
  ];

  const transformDa = (p, extra = '') => `translate(-50%, -50%) ${extra} rotate(${p.giro}deg) scale(${p.escala})`;

  const posicionar = (el, p, tam) => {
    el.style.left = `${p.x * 100}%`;
    el.style.top = `${p.y * 100}%`;
    el.style.width = `${(tam / 0.84) * 100}%`;
    el.style.transform = transformDa(p);
  };

  const cair = (el, p, atraso) => animar(el, [
    { transform: `translate(-50%, -50%) translateY(-45%) rotate(${p.giro + 40}deg) scale(${p.escala * 1.55})`, opacity: 0 },
    { transform: `translate(-50%, -50%) rotate(${p.giro}deg) scale(${p.escala * 0.9})`, opacity: 1, offset: 0.7 },
    { transform: transformDa(p), opacity: 1 },
  ], { duration: 560, delay: atraso, easing: 'cubic-bezier(0.35, 0.6, 0.3, 1)', fill: 'backwards' });

  const tirar = (el, p) => {
    const saida = animar(el, [
      { transform: transformDa(p), opacity: 1 },
      { transform: `translate(-50%, -50%) translateY(-18%) rotate(${p.giro}deg) scale(${p.escala * 0.6})`, opacity: 0 },
    ], { duration: 220, easing: 'ease-in' });
    if (saida) saida.finished.then(() => el.remove(), () => el.remove());
    else el.remove();
  };

  const naPizza = new Map(); // id -> { el, p }

  const aplicarCoberturas = (pecas, atrasoBase) => {
    const ficam = new Set(pecas.map((p) => p.id));
    naPizza.forEach((item, id) => {
      if (ficam.has(id)) return;
      naPizza.delete(id);
      if (item.el.isConnected) tirar(item.el, item.p);
    });
    const inicio = performance.now();
    let ordem = 0;
    pecas.forEach((p) => {
      const def = INGREDIENTES[p.tipo];
      const atual = naPizza.get(p.id);
      if (atual) {
        // Mesmo ingrediente, lugar novo (a pizza foi dividida com outro sabor): desliza até lá.
        atual.p = p;
        posicionar(atual.el, p, def.tam);
        return;
      }
      const el = criar('span', 'peca');
      el.style.backgroundImage = `url("${pasta}${p.tipo}.webp")`;
      el.style.backgroundPosition = `${p.variacao * (100 / 3)}% 0`;
      posicionar(el, p, def.tam);
      const item = { el, p };
      naPizza.set(p.id, item);
      const atraso = atrasoBase + Math.min(ordem * 24, 900);
      ordem += 1;
      carregar(p.tipo).then(() => {
        if (naPizza.get(p.id) !== item) return;
        coberturas[def.camada - 1].appendChild(el);
        cair(el, item.p, Math.max(0, atraso - (performance.now() - inicio)));
      });
    });
  };

  // Borda recheada: montinhos confeitados em volta, um depois do outro.
  const BORDAS = [
    ['borda-chocolate', /chocolate|nutella|brigadeiro|doce/],
    ['borda-cheddar', /cheddar/],
    ['catupiry', /./],
  ];
  let bordaAtual = null;
  const aplicarBorda = (nome) => {
    const sprite = nome ? BORDAS.find(([, regra]) => regra.test(semAcento(nome)))[0] : null;
    if (sprite === bordaAtual) return;
    bordaAtual = sprite;
    [...borda.children].filter((el) => !el.dataset.saindo).forEach((el) => {
      el.dataset.saindo = '1';
      tirar(el, JSON.parse(el.dataset.p));
    });
    if (!sprite) return;
    carregar(sprite).then(() => {
      if (bordaAtual !== sprite) return;
      const rnd = aleatorio(semente(sprite));
      const n = 46;
      for (let i = 0; i < n; i += 1) {
        const a = (i / n) * VOLTA - VOLTA / 4;
        const p = {
          x: 0.5 + Math.cos(a) * 0.457, y: 0.5 + Math.sin(a) * 0.457, giro: rnd() * 360, escala: 0.9 + rnd() * 0.18, variacao: i % 4,
        };
        const el = criar('span', 'peca');
        el.dataset.p = JSON.stringify(p);
        el.style.backgroundImage = `url("${pasta}${sprite}.webp")`;
        el.style.backgroundPosition = `${p.variacao * (100 / 3)}% 0`;
        posicionar(el, p, 0.07);
        borda.appendChild(el);
        cair(el, p, i * 18);
      }
    });
  };

  const tomDaMassa = (nome) => {
    const t = semAcento(nome);
    if (/integral/.test(t)) return 'integral';
    if (/gluten/.test(t)) return 'semgluten';
    if (/fina|crocante/.test(t)) return 'fina';
    return '';
  };

  // Antes do tamanho a pizza é pequena; cada tamanho, do menor ao maior, a faz crescer.
  const escalaDo = (tamanho) => {
    if (!tamanho) return 0.6;
    const n = tamanhos.length;
    return n > 1 ? 0.7 + (0.3 * tamanho.posicao) / (n - 1) : 1;
  };

  let anterior = chaves(lerEstado());

  const desenhar = (estado) => {
    if (!pizza) return;
    pizza.style.scale = String(escalaDo(estado.tamanho));
    massa.dataset.tom = estado.massa ? tomDaMassa(estado.massa.nome) : '';

    const setores = estado.sabores.map((s) => ({ id: s.id, ...lerSabor(s.nome, s.detalhe, 5) }));
    const extras = estado.adicionais.map((a) => ({ id: a.id, ...lerSabor(a.nome, '', 1) }));

    const espalhouMolho = mostrarBase(bases.molho, mascara(setores, (s) => s.base === 'molho'), ESPALHAR, 0);
    const espalhouChocolate = mostrarBase(bases.chocolate, mascara(setores, (s) => s.base === 'chocolate'), ESPALHAR, 0);
    const espalhou = espalhouMolho || espalhouChocolate;
    const derreteu = mostrarBase(bases.queijo, mascara(setores, (s) => s.base !== 'chocolate'), DERRETER, espalhou ? 420 : 0);

    // As coberturas esperam a base ficar pronta para cair.
    aplicarCoberturas(dispor(setores, extras), espalhou || derreteu ? 900 : 0);
    aplicarBorda(estado.borda ? estado.borda.nome : null);
  };

  const aplicar = () => {
    const estado = lerEstado();
    if (resumo) resumo.textContent = descrever(estado);
    const agora = chaves(estado);
    agora.forEach((nome, chave) => { if (!anterior.has(chave)) mostrarEtiqueta(nome, 'entrou'); });
    anterior.forEach((nome, chave) => { if (!agora.has(chave)) mostrarEtiqueta(nome, 'saiu'); });
    anterior = agora;
    desenhar(estado);
  };

  // Inclinação leve seguindo o mouse: dá profundidade sem pesar (só CSS 3D).
  if (pizza && !reduzirMovimento && window.matchMedia('(hover: hover)').matches) {
    const area = palco.querySelector('.palco');
    let pedido = 0;
    let alvo = [0, 0];
    const inclinar = () => {
      pedido = 0;
      pizza.style.setProperty('--inclina-x', `${alvo[0]}deg`);
      pizza.style.setProperty('--inclina-y', `${alvo[1]}deg`);
    };
    area.addEventListener('pointermove', (e) => {
      const r = area.getBoundingClientRect();
      alvo = [((e.clientY - r.top) / r.height - 0.5) * -10, ((e.clientX - r.left) / r.width - 0.5) * 10];
      if (!pedido) pedido = requestAnimationFrame(inclinar);
    });
    area.addEventListener('pointerleave', () => {
      alvo = [0, 0];
      if (!pedido) pedido = requestAnimationFrame(inclinar);
    });
  }

  montador.addEventListener('change', aplicar);
  tamanhos.forEach((input) => input.addEventListener('change', atualizarLimite));
  sabores.forEach((input) => input.addEventListener('change', atualizarLimite));
  atualizarLimite();

  if (pizza) {
    // A massa pousa na tábua; o estado vem do formulário (o navegador pode lembrar escolhas ao voltar).
    animar(pizza, [{ opacity: 0, translate: '0 -6%' }, { opacity: 1, translate: '0 0' }], { duration: 700, easing: 'cubic-bezier(0.3, 0.7, 0.3, 1)' });
    const estado = lerEstado();
    if (resumo) resumo.textContent = descrever(estado);
    desenhar(estado);
    // Molho e queijo já ficam baixados para o primeiro sabor não esperar a rede.
    const adiantar = () => { carregar('molho'); carregar('queijo'); };
    if ('requestIdleCallback' in window) window.requestIdleCallback(adiantar, { timeout: 2000 });
    else window.setTimeout(adiantar, 800);
  }

  montador.addEventListener('submit', () => {
    const botao = montador.querySelector('button[type="submit"]');
    if (botao) botao.textContent = 'Botando na sacola...';
  });
});
