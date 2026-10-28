// Montador de pizza: estado do formulário, preço estimado e ponte com a cena 3D.
// O preço mostrado aqui é só uma prévia; o valor gravado é recalculado no servidor.
import { coberturaDoSabor } from './pizza-coberturas.js';

const builder = document.querySelector('.pizza-builder');
const raiz = document.querySelector('.builder');

if (builder && raiz) iniciar();

function iniciar() {
  const moeda = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' });
  const regraMedia = raiz.dataset.regraPreco === 'media';
  const reduzirMovimento = window.matchMedia('(prefers-reduced-motion: reduce)');

  const todos = (nome) => [...builder.querySelectorAll(`input[name="${nome}"]`)];
  const marcado = (nome) => todos(nome).find((input) => input.checked);
  const marcados = (nome) => todos(nome).filter((input) => input.checked);
  const preco = (input) => Number(input?.dataset.preco || 0);

  const sizes = todos('tamanho_id');
  const flavors = todos('sabores_ids');
  const quantidade = builder.querySelector('#quantidade');
  const totalEl = raiz.querySelector('[data-pizza-total]');
  const resumoEl = raiz.querySelector('[data-pizza-resumo]');
  const limiteEl = builder.querySelector('[data-limite-sabores]');

  // "12:40.00,13:52.00" -> Map(tamanho_id -> preço)
  flavors.forEach((input) => {
    input.precos = new Map((input.dataset.precos || '').split(',').filter(Boolean).map((par) => {
      const [tamanho, valor] = par.split(':');
      return [tamanho, Number(valor)];
    }));
    const cobertura = coberturaDoSabor(input.dataset.nome || '');
    input.closest('label')?.style.setProperty('--cor-sabor', cobertura.cor);
  });

  builder.querySelectorAll('.choice-group').forEach((group, index) => {
    group.classList.add('js-reveal');
    group.style.transitionDelay = `${index * 70}ms`;
    requestAnimationFrame(() => group.classList.add('is-visible'));
  });

  // Ordem de escolha importa: a 1ª metade é o 1º sabor marcado.
  let ordemSabores = [];

  const estadoAtual = () => {
    const tamanho = marcado('tamanho_id');
    const massa = marcado('massa_id');
    const borda = marcado('borda_id');
    const sabores = ordemSabores.filter((input) => input.checked);
    return {
      tamanho: tamanho ? {
        nome: tamanho.dataset.nome,
        indice: Number(tamanho.dataset.indice),
        total: Number(tamanho.dataset.total),
        fatias: Number(tamanho.dataset.fatias) || 8,
      } : null,
      sabores: sabores.map((input) => ({ id: input.value, nome: input.dataset.nome })),
      massa: massa?.value ? massa.dataset.nome : null,
      borda: borda?.value ? borda.dataset.nome : null,
      adicionais: marcados('adicionais_ids').map((input) => input.dataset.nome),
    };
  };

  const calcularTotal = () => {
    const tamanho = marcado('tamanho_id');
    const sabores = ordemSabores.filter((input) => input.checked);
    if (!tamanho || !sabores.length) return null;
    const valores = sabores.map((input) => input.precos.get(tamanho.value)).filter((v) => v !== undefined);
    if (!valores.length) return null;
    const base = regraMedia ? valores.reduce((a, b) => a + b, 0) / valores.length : Math.max(...valores);
    const extras = preco(marcado('massa_id')) + preco(marcado('borda_id'))
      + marcados('adicionais_ids').reduce((soma, input) => soma + preco(input), 0);
    return (base + extras) * Math.max(1, Number(quantidade?.value) || 1);
  };

  const atualizarSabores = () => {
    const tamanho = marcado('tamanho_id');
    const maximo = tamanho ? Number(tamanho.dataset.max) || 1 : Infinity;
    // Ao trocar para um tamanho menor, desmarca os últimos sabores escolhidos.
    ordemSabores = ordemSabores.filter((input) => input.checked);
    while (ordemSabores.length > maximo) ordemSabores.pop().checked = false;

    flavors.forEach((input) => {
      const valor = tamanho ? input.precos.get(tamanho.value) : undefined;
      const semPreco = tamanho && valor === undefined;
      input.disabled = semPreco || (!input.checked && ordemSabores.length >= maximo);
      if (semPreco) input.checked = false;
      const precoEl = input.closest('label')?.querySelector('[data-preco-sabor]');
      if (precoEl) precoEl.textContent = valor !== undefined ? moeda.format(valor) : (semPreco ? 'indisponível' : '');
    });

    if (limiteEl) {
      limiteEl.textContent = tamanho
        ? `${ordemSabores.length} de ${maximo} · ${maximo > 1 ? 'cada sabor vira uma fatia da pizza' : 'um sabor'}`
        : 'escolha o tamanho primeiro';
    }
  };

  const atualizarResumo = (estado) => {
    if (!resumoEl) return;
    const itens = [];
    if (estado.tamanho) itens.push(`${estado.tamanho.nome} · ${estado.tamanho.fatias} fatias`);
    if (estado.sabores.length) itens.push(estado.sabores.map((s) => s.nome).join(' + '));
    if (estado.massa) itens.push(`Massa ${estado.massa}`);
    if (estado.borda) itens.push(`Borda ${estado.borda}`);
    if (estado.adicionais.length) itens.push(`+ ${estado.adicionais.join(', ')}`);
    resumoEl.replaceChildren(...(itens.length ? itens : ['Escolha um tamanho para começar']).map((texto) => {
      const li = document.createElement('li');
      li.textContent = texto;
      return li;
    }));
  };

  let cena = null;
  const atualizar = () => {
    atualizarSabores();
    const estado = estadoAtual();
    const total = calcularTotal();
    if (totalEl) totalEl.textContent = total === null ? '—' : moeda.format(total);
    atualizarResumo(estado);
    cena?.atualizar(estado);
  };

  builder.addEventListener('change', (evento) => {
    const alvo = evento.target;
    if (alvo.name === 'sabores_ids') {
      if (alvo.checked) ordemSabores.push(alvo);
      alvo.closest('label')?.classList.add('js-pulse');
    }
    atualizar();
  });
  builder.addEventListener('animationend', (evento) => evento.target.classList?.remove('js-pulse'));
  quantidade?.addEventListener('input', atualizar);

  builder.querySelectorAll('[data-passo]').forEach((botao) => botao.addEventListener('click', () => {
    if (!quantidade) return;
    const novo = Math.min(20, Math.max(1, (Number(quantidade.value) || 1) + Number(botao.dataset.passo)));
    quantidade.value = String(novo);
    atualizar();
  }));

  builder.addEventListener('submit', () => {
    builder.classList.add('js-loading');
    const submit = builder.querySelector('button[type="submit"]');
    if (submit) submit.textContent = 'Adicionando...';
  });

  // Sabores que já vierem marcados (voltar do navegador) entram na ordem do DOM.
  ordemSabores = flavors.filter((input) => input.checked);
  atualizar();
  carregarCena3d(reduzirMovimento.matches).then((instancia) => {
    if (!instancia) return;
    cena = instancia;
    cena.atualizar(estadoAtual());
  });
}

// A cena (Three.js, ~180 KB gzip) só carrega depois da página pronta e se houver WebGL.
async function carregarCena3d(reduzirMovimento) {
  const palco = document.querySelector('[data-pizza-stage]');
  const canvas = palco?.querySelector('[data-pizza-canvas]');
  const origem = document.querySelector('script[data-cena]')?.dataset.cena;
  if (!palco || !canvas || !origem || !suportaWebGL()) return null;
  if (navigator.connection?.saveData) return null;

  await new Promise((resolver) => {
    if (document.readyState === 'complete') resolver();
    else window.addEventListener('load', resolver, { once: true });
  });

  try {
    const { criarCenaPizza } = await import(origem);
    const cena = criarCenaPizza(canvas, { reduzirMovimento });
    palco.classList.add('is-3d');
    return cena;
  } catch (erro) {
    console.warn('Prévia 3D indisponível, mantendo a ilustração 2D.', erro);
    return null;
  }
}

function suportaWebGL() {
  try {
    const teste = document.createElement('canvas');
    return Boolean(teste.getContext('webgl2') || teste.getContext('webgl'));
  } catch {
    return false;
  }
}
