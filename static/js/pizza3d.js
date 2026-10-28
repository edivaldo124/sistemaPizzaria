// Prévia 3D da pizza (Three.js puro, sem modelos externos: tudo é gerado em código).
// Cada sabor ocupa uma fatia proporcional da pizza; as coberturas "caem" quando o sabor entra.
import * as THREE from '../vendor/three/three.module.min.js';
import { coberturaDoSabor } from './pizza-coberturas.js';

const RAIO_QUEIJO = 0.9;
const ALTURA_COBERTURA = 0.112;

// ---------------------------------------------------------------- utilidades
function aleatorio(semente) {
  let s = semente >>> 0;
  return () => {
    s = (s + 0x6d2b79f5) >>> 0;
    let t = s;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function hash(texto) {
  let h = 2166136261;
  for (const c of texto) h = Math.imul(h ^ c.codePointAt(0), 16777619);
  return h >>> 0;
}

// Ruído barato e determinístico para o relevo do queijo e da borda.
function ruido(x, y, semente = 0) {
  return (Math.sin(x * 7.3 + semente) * Math.cos(y * 6.1 - semente) + Math.sin((x + y) * 13.7 + semente * 2) * 0.5) / 1.5;
}

const amortecer = (atual, alvo, lambda, dt) => atual + (alvo - atual) * (1 - Math.exp(-lambda * dt));
const easeOutBack = (t) => 1 + 2.2 * (t - 1) ** 3 + 1.2 * (t - 1) ** 2;

function texturaCanvas(tamanho, desenhar) {
  const canvas = document.createElement('canvas');
  canvas.width = canvas.height = tamanho;
  desenhar(canvas.getContext('2d'), tamanho);
  const textura = new THREE.CanvasTexture(canvas);
  textura.colorSpace = THREE.SRGBColorSpace;
  return textura;
}

// ---------------------------------------------------------------- coberturas
const mat = (cor, extra = {}) => new THREE.MeshStandardMaterial({ color: cor, roughness: 0.6, ...extra });
const plano = (geo) => geo.rotateX(Math.PI / 2);

// geo: geometria compartilhada; qtd: peças por fatia inteira; alto: meia altura (para pousar no queijo)
function criarCatalogo() {
  const tipos = {
    calabresa: { geo: new THREE.CylinderGeometry(0.085, 0.085, 0.022, 20), mat: mat('#a8322a', { roughness: 0.45 }), qtd: 16, alto: 0.011 },
    tomate: { geo: new THREE.CylinderGeometry(0.095, 0.095, 0.018, 20), mat: mat('#d8432c', { roughness: 0.3 }), qtd: 10, alto: 0.009 },
    manjericao: { geo: new THREE.SphereGeometry(0.06, 10, 6).scale(1, 0.18, 0.6), mat: mat('#3f7d3a', { roughness: 0.5 }), qtd: 9, alto: 0.008 },
    azeitona: { geo: plano(new THREE.TorusGeometry(0.03, 0.016, 8, 16)), mat: mat('#26201d', { roughness: 0.25 }), qtd: 12, alto: 0.014 },
    cebola: { geo: plano(new THREE.TorusGeometry(0.06, 0.01, 6, 20)), mat: mat('#efe0ea', { roughness: 0.4, transparent: true, opacity: 0.9 }), qtd: 9, alto: 0.008 },
    frango: { geo: new THREE.DodecahedronGeometry(0.045), mat: mat('#e6c393'), qtd: 18, alto: 0.03 },
    bacon: { geo: new THREE.BoxGeometry(0.15, 0.02, 0.05), mat: mat('#a5452f', { roughness: 0.5 }), qtd: 12, alto: 0.01 },
    presunto: { geo: new THREE.BoxGeometry(0.12, 0.012, 0.09), mat: mat('#e59a96', { roughness: 0.5 }), qtd: 12, alto: 0.006 },
    ovo: { geo: new THREE.SphereGeometry(0.05, 14, 8).scale(1, 0.4, 1), mat: mat('#f6c94a', { roughness: 0.3 }), qtd: 6, alto: 0.01 },
    milho: { geo: new THREE.SphereGeometry(0.022, 8, 6), mat: mat('#f2c230', { roughness: 0.35 }), qtd: 30, alto: 0.015 },
    charque: { geo: new THREE.BoxGeometry(0.09, 0.03, 0.05), mat: mat('#7a3a24', { roughness: 0.75 }), qtd: 18, alto: 0.015 },
    jerimum: { geo: new THREE.BoxGeometry(0.06, 0.05, 0.06), mat: mat('#e58a2c', { roughness: 0.5 }), qtd: 14, alto: 0.025 },
    coalho: { geo: new THREE.BoxGeometry(0.08, 0.04, 0.08), mat: mat('#f3dfae', { roughness: 0.55 }), qtd: 12, alto: 0.02 },
    mel: { geo: new THREE.SphereGeometry(0.035, 12, 8).scale(1, 0.25, 1), mat: mat('#e0a422', { roughness: 0.1 }), qtd: 12, alto: 0.005 },
    atum: { geo: new THREE.DodecahedronGeometry(0.04), mat: mat('#c79a7a'), qtd: 18, alto: 0.025 },
    palmito: { geo: new THREE.CylinderGeometry(0.04, 0.04, 0.025, 14), mat: mat('#efe6c8'), qtd: 12, alto: 0.012 },
    cogumelo: { geo: new THREE.CylinderGeometry(0.06, 0.045, 0.025, 16), mat: mat('#c9b49a'), qtd: 12, alto: 0.012 },
    catupiry: { geo: new THREE.SphereGeometry(0.065, 14, 8).scale(1, 0.35, 1), mat: mat('#fbf4e2', { roughness: 0.3 }), qtd: 10, alto: 0.012 },
    pimentao: { geo: plano(new THREE.TorusGeometry(0.05, 0.012, 6, 16, Math.PI * 1.3)), mat: mat('#3c8a3a', { roughness: 0.35 }), qtd: 10, alto: 0.012 },
    granulado: { geo: new THREE.BoxGeometry(0.03, 0.01, 0.01), mat: mat('#3a1f14'), qtd: 80, alto: 0.005 },
    goiabada: { geo: new THREE.BoxGeometry(0.07, 0.03, 0.07), mat: mat('#a8323a', { roughness: 0.3 }), qtd: 12, alto: 0.015 },
    banana: { geo: new THREE.CylinderGeometry(0.06, 0.06, 0.02, 16), mat: mat('#f2dc8a', { roughness: 0.4 }), qtd: 12, alto: 0.01 },
    canela: { geo: new THREE.BoxGeometry(0.014, 0.004, 0.014), mat: mat('#7b4a2a'), qtd: 60, alto: 0.002 },
    morango: { geo: new THREE.SphereGeometry(0.04, 12, 8).scale(1, 0.6, 1.25), mat: mat('#d63a4a', { roughness: 0.3 }), qtd: 12, alto: 0.02 },
    oregano: { geo: new THREE.BoxGeometry(0.018, 0.004, 0.01), mat: mat('#4f6b2d', { roughness: 0.9 }), qtd: 70, alto: 0.002 },
  };
  const bases = {
    queijo: { claro: new THREE.Color('#f4cf6e'), tostado: new THREE.Color('#c98535'), roughness: 0.45 },
    chocolate: { claro: new THREE.Color('#5a3222'), tostado: new THREE.Color('#3b1e13'), roughness: 0.25 },
    doce: { claro: new THREE.Color('#e9c48a'), tostado: new THREE.Color('#c48a4a'), roughness: 0.35 },
  };
  return { tipos, bases };
}

// Queijo de uma fatia (setor) com relevo e manchas tostadas em cores por vértice.
function geometriaQueijo(inicio, abertura, semente, base) {
  const segmentos = Math.max(8, Math.round(64 * abertura / (Math.PI * 2)));
  const geo = new THREE.RingGeometry(0.001, RAIO_QUEIJO, segmentos, 14, inicio, abertura);
  const pos = geo.attributes.position;
  const cores = new Float32Array(pos.count * 3);
  const cor = new THREE.Color();
  for (let i = 0; i < pos.count; i++) {
    const x = pos.getX(i);
    const y = pos.getY(i);
    const r = Math.hypot(x, y);
    const borda = Math.min(1, (RAIO_QUEIJO - r) / 0.08);
    const n = ruido(x, y, semente);
    pos.setZ(i, (0.012 + 0.01 * n) * borda + 0.004);
    const tostado = THREE.MathUtils.smoothstep(n + ruido(y * 2, x * 2, semente + 3) * 0.4, 0.55, 0.95);
    cor.copy(base.claro).lerp(base.tostado, tostado * 0.85);
    cores.set([cor.r, cor.g, cor.b], i * 3);
  }
  geo.setAttribute('color', new THREE.BufferAttribute(cores, 3));
  geo.rotateX(-Math.PI / 2);
  geo.computeVertexNormals();
  return geo;
}

// Espalha peças dentro do setor sem amontoar (amostragem por rejeição).
function sortearPosicoes(qtd, inicio, abertura, rand, ocupados, distanciaMin) {
  const pontos = [];
  const margem = Math.min(0.08, abertura * 0.08);
  for (let tentativa = 0; pontos.length < qtd && tentativa < qtd * 30; tentativa++) {
    const r = Math.sqrt(0.02 + rand() * 0.98) * (RAIO_QUEIJO - 0.1);
    const a = inicio + margem + rand() * (abertura - margem * 2);
    // RingGeometry fica no plano XY e foi girada -90° em X: (x, y) vira (x, -z).
    const p = { x: Math.cos(a) * r, z: -Math.sin(a) * r };
    if (distanciaMin && ocupados.some((o) => (o.x - p.x) ** 2 + (o.z - p.z) ** 2 < distanciaMin ** 2)) continue;
    pontos.push(p);
    if (distanciaMin) ocupados.push(p);
  }
  return pontos;
}

// ---------------------------------------------------------------- cena
export function criarCenaPizza(canvas, { reduzirMovimento = false } = {}) {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true, powerPreference: 'low-power' });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.75));
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.05;

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(30, 1, 0.1, 50);

  scene.add(new THREE.HemisphereLight('#fff3e0', '#3a2418', 1.2));
  const sol = new THREE.DirectionalLight('#ffe2b8', 2.6);
  sol.position.set(2.5, 4, 2);
  scene.add(sol);
  const contraluz = new THREE.DirectionalLight('#ffb070', 1.1);
  contraluz.position.set(-3, 2, -2.5);
  scene.add(contraluz);

  // Tábua de madeira + sombra de contato (textura radial, sem shadow map).
  const madeira = texturaCanvas(512, (ctx, t) => {
    ctx.fillStyle = '#9a6a3f';
    ctx.fillRect(0, 0, t, t);
    const rand = aleatorio(7);
    for (let i = 0; i < 70; i++) {
      ctx.strokeStyle = `rgba(${rand() > 0.5 ? '70,40,20' : '190,140,90'},${0.08 + rand() * 0.12})`;
      ctx.lineWidth = 1 + rand() * 3;
      ctx.beginPath();
      const y = rand() * t;
      ctx.moveTo(0, y);
      ctx.bezierCurveTo(t * 0.3, y + (rand() - 0.5) * 30, t * 0.7, y + (rand() - 0.5) * 30, t, y + (rand() - 0.5) * 20);
      ctx.stroke();
    }
  });
  const tabua = new THREE.Mesh(
    new THREE.CylinderGeometry(1.2, 1.18, 0.07, 96),
    new THREE.MeshStandardMaterial({ map: madeira, roughness: 0.8 }),
  );
  tabua.position.y = -0.035;
  const sombra = new THREE.Mesh(
    new THREE.PlaneGeometry(3.8, 3.8).rotateX(-Math.PI / 2),
    new THREE.MeshBasicMaterial({
      transparent: true,
      depthWrite: false,
      map: texturaCanvas(256, (ctx, t) => {
        const g = ctx.createRadialGradient(t / 2, t / 2, t * 0.2, t / 2, t / 2, t / 2);
        g.addColorStop(0, 'rgba(40,20,10,0.55)');
        g.addColorStop(1, 'rgba(40,20,10,0)');
        ctx.fillStyle = g;
        ctx.fillRect(0, 0, t, t);
      }),
    }),
  );
  sombra.position.y = -0.075;

  const mesa = new THREE.Group();
  mesa.add(sombra, tabua);
  scene.add(mesa);

  // A pizza fica num grupo próprio para escalar por tamanho e girar com o arraste.
  const pizza = new THREE.Group();
  pizza.scale.setScalar(reduzirMovimento ? 0.9 : 0.001);
  mesa.add(pizza);

  const massaMat = new THREE.MeshStandardMaterial({ color: '#e8b673', roughness: 0.75 });
  const massa = new THREE.Mesh(new THREE.CylinderGeometry(1.0, 0.97, 0.08, 96), massaMat);
  massa.position.y = 0.04;
  const molho = new THREE.Mesh(
    new THREE.CylinderGeometry(0.95, 0.95, 0.012, 96),
    new THREE.MeshStandardMaterial({ color: '#b8321f', roughness: 0.35 }),
  );
  molho.position.y = 0.086;
  pizza.add(massa, molho);

  const catalogo = criarCatalogo();
  const queijoMats = Object.fromEntries(Object.entries(catalogo.bases).map(([nome, base]) => [
    nome, new THREE.MeshStandardMaterial({ vertexColors: true, roughness: base.roughness }),
  ]));

  let borda = null;
  let cortes = null;
  const setores = new Map(); // chave -> { grupo, animados }
  const extras = new Map();
  const animando = new Set();
  let tempo = 0;
  let ultimoQuadro = 0;

  // ---- borda (crosta) com recheio opcional
  function montarBorda(nomeBorda) {
    if (borda) {
      pizza.remove(borda);
      borda.traverse((o) => o.geometry?.dispose());
    }
    borda = new THREE.Group();
    const recheada = Boolean(nomeBorda);
    const tubo = recheada ? 0.125 : 0.09;
    const geo = new THREE.TorusGeometry(0.985, tubo, 24, 120);
    const pos = geo.attributes.position;
    const cores = new Float32Array(pos.count * 3);
    const claro = new THREE.Color('#e2ad6c');
    const tostado = new THREE.Color('#a8652f');
    const cor = new THREE.Color();
    const v = new THREE.Vector3();
    for (let i = 0; i < pos.count; i++) {
      v.fromBufferAttribute(pos, i);
      const n = ruido(v.x * 1.4, v.y * 1.4, 5);
      const fator = 1 + n * 0.035;
      pos.setXYZ(i, v.x * (1 + n * 0.006), v.y * (1 + n * 0.006), v.z * fator);
      // Mais tostado em cima (z > 0 antes de deitar o toro).
      const topo = THREE.MathUtils.smoothstep(v.z / tubo, -0.2, 1);
      cor.copy(claro).lerp(tostado, Math.min(1, topo * 0.55 + Math.max(0, n) * 0.5));
      cores.set([cor.r, cor.g, cor.b], i * 3);
    }
    geo.setAttribute('color', new THREE.BufferAttribute(cores, 3));
    geo.computeVertexNormals();
    geo.rotateX(-Math.PI / 2);
    const crosta = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.7 }));
    crosta.position.y = 0.085;
    crosta.scale.y = 0.85;
    borda.add(crosta);

    if (recheada) {
      // O recheio aparece como um filete na parte interna da borda.
      const nome = nomeBorda.toLowerCase();
      const corRecheio = nome.includes('cheddar') ? '#f0a030'
        : nome.includes('chocolate') ? '#4a2a1d'
          : nome.includes('goiab') ? '#a8323a' : '#fbf1dc';
      const recheio = new THREE.Mesh(
        new THREE.TorusGeometry(0.885, 0.035, 12, 120).rotateX(-Math.PI / 2),
        new THREE.MeshStandardMaterial({ color: corRecheio, roughness: 0.3 }),
      );
      recheio.position.y = 0.105;
      borda.add(recheio);
    }
    pizza.add(borda);
  }

  // ---- linhas de corte das fatias
  function montarCortes(fatias) {
    if (cortes) {
      pizza.remove(cortes);
      cortes.children[0]?.geometry.dispose();
    }
    const geo = new THREE.BoxGeometry(RAIO_QUEIJO, 0.004, 0.012).translate(RAIO_QUEIJO / 2, 0, 0);
    const material = new THREE.MeshBasicMaterial({ color: '#5a2c14', transparent: true, opacity: 0.35, depthWrite: false });
    cortes = new THREE.Group();
    for (let k = 0; k < fatias; k++) {
      const linha = new THREE.Mesh(geo, material);
      linha.rotation.y = (k / fatias) * Math.PI * 2 + Math.PI / fatias;
      cortes.add(linha);
    }
    cortes.position.y = ALTURA_COBERTURA + 0.016;
    pizza.add(cortes);
  }

  // ---- coberturas: InstancedMesh por tipo, com animação de queda
  function espalhar(grupo, itens, inicio, abertura, semente, densidade, animar) {
    const rand = aleatorio(semente);
    const ocupados = [];
    const proporcao = abertura / (Math.PI * 2);
    const animados = [];
    itens.forEach((nome, ordem) => {
      const tipo = catalogo.tipos[nome];
      if (!tipo) return;
      const salpico = tipo.qtd > 40;
      const qtd = Math.max(salpico ? 6 : 2, Math.round(tipo.qtd * proporcao * densidade / Math.max(1, itens.length * 0.6)));
      const pontos = sortearPosicoes(qtd, inicio, abertura, rand, ocupados, salpico ? 0 : 0.12);
      if (!pontos.length) return;
      const malha = new THREE.InstancedMesh(tipo.geo, tipo.mat, pontos.length);
      malha.frustumCulled = false; // a esfera de colisão seria calculada com as peças ainda no ar
      const alvos = pontos.map((p, i) => ({
        posicao: new THREE.Vector3(p.x, ALTURA_COBERTURA + tipo.alto + 0.006 + ordem * 0.004, p.z),
        rotacao: new THREE.Quaternion().setFromEuler(new THREE.Euler(0, rand() * Math.PI * 2, 0)),
        atraso: ordem * 0.12 + i * (salpico ? 0.004 : 0.03) + rand() * 0.08,
      }));
      malha.userData.alvos = alvos;
      grupo.add(malha);
      animados.push(malha);
    });
    animados.forEach((malha) => posicionar(malha, animar ? 0 : Infinity));
    if (animar) animados.forEach((malha) => { malha.userData.inicio = tempo; animando.add(malha); });
    return animados;
  }

  const m4 = new THREE.Matrix4();
  const p3 = new THREE.Vector3();
  const s3 = new THREE.Vector3();
  // decorrido = segundos desde o início da queda; Infinity = já pousado
  function posicionar(malha, decorrido) {
    let terminou = true;
    malha.userData.alvos.forEach((alvo, i) => {
      const t = THREE.MathUtils.clamp((decorrido - alvo.atraso) / 0.55, 0, 1);
      if (t < 1) terminou = false;
      const queda = 1 - t;
      p3.copy(alvo.posicao);
      p3.y += queda * queda * 1.4;
      s3.setScalar(t === 0 ? 0.0001 : 0.5 + 0.5 * easeOutBack(t));
      malha.setMatrixAt(i, m4.compose(p3, alvo.rotacao, s3));
    });
    malha.instanceMatrix.needsUpdate = true;
    return terminou;
  }

  function descartar(grupo) {
    pizza.remove(grupo);
    grupo.traverse((o) => {
      animando.delete(o);
      if (o.isInstancedMesh) o.dispose();
      else if (o.isMesh) o.geometry.dispose(); // queijo: geometria própria; coberturas usam geometria compartilhada
    });
  }

  function montarSabores(sabores, idsAntes) {
    const n = Math.max(1, sabores.length);
    const abertura = (Math.PI * 2) / n;
    const lista = sabores.length ? sabores : [{ id: 'vazio', nome: '' }];
    const novos = new Map();
    lista.forEach((sabor, i) => {
      const chave = `${sabor.id}|${i}|${n}`;
      if (setores.has(chave)) {
        novos.set(chave, setores.get(chave));
        setores.delete(chave);
        return;
      }
      const inicio = Math.PI / 2 + i * abertura; // 1º sabor começa voltado para a câmera
      const cobertura = sabor.id === 'vazio' ? { itens: [], base: 'queijo' } : coberturaDoSabor(sabor.nome);
      const semente = hash(String(sabor.id));
      const grupo = new THREE.Group();
      const queijo = new THREE.Mesh(
        geometriaQueijo(inicio, abertura, semente % 97, catalogo.bases[cobertura.base]),
        queijoMats[cobertura.base],
      );
      queijo.position.y = ALTURA_COBERTURA - 0.02;
      grupo.add(queijo);
      const animar = !reduzirMovimento && !idsAntes.has(String(sabor.id));
      espalhar(grupo, cobertura.itens, inicio, abertura, semente + i, 1, animar);
      pizza.add(grupo);
      novos.set(chave, grupo);
    });
    setores.forEach(descartar);
    setores.clear();
    novos.forEach((grupo, chave) => setores.set(chave, grupo));
  }

  function montarAdicionais(nomes) {
    const novos = new Map();
    nomes.forEach((nome) => {
      if (extras.has(nome)) {
        novos.set(nome, extras.get(nome));
        extras.delete(nome);
        return;
      }
      const grupo = new THREE.Group();
      grupo.position.y = 0.01; // por cima das coberturas dos sabores
      espalhar(grupo, coberturaDoSabor(nome).itens, 0, Math.PI * 2, hash(nome), 0.45, !reduzirMovimento);
      pizza.add(grupo);
      novos.set(nome, grupo);
    });
    extras.forEach(descartar);
    extras.clear();
    novos.forEach((grupo, nome) => extras.set(nome, grupo));
  }

  // ---- estado vindo do formulário
  let escalaAlvo = 0.9;
  let anterior = { sabores: [], borda: undefined, massa: undefined, fatias: 0, adicionais: '' };

  function atualizar(estado) {
    const fatias = estado.tamanho?.fatias || 8;
    escalaAlvo = estado.tamanho
      ? 0.72 + 0.28 * (estado.tamanho.total > 1 ? estado.tamanho.indice / (estado.tamanho.total - 1) : 1)
      : 0.9;

    if (estado.borda !== anterior.borda) montarBorda(estado.borda);
    if (fatias !== anterior.fatias) montarCortes(fatias);
    if (estado.massa !== anterior.massa) {
      const nome = (estado.massa || '').toLowerCase();
      massaMat.color.set(nome.includes('integral') ? '#b98552' : nome.includes('australiana') ? '#6e3f26' : '#e8b673');
      massa.scale.y = nome.includes('fina') ? 0.6 : /grossa|pan|pao/.test(nome) ? 1.5 : 1;
    }
    const idsAntes = new Set(anterior.sabores.map((s) => String(s.id)));
    if (estado.sabores.map((s) => s.id).join() !== anterior.sabores.map((s) => s.id).join()) {
      montarSabores(estado.sabores, idsAntes);
    }
    if (estado.adicionais.join('|') !== anterior.adicionais) montarAdicionais(estado.adicionais);

    anterior = { ...estado, fatias, adicionais: estado.adicionais.join('|') };
    pedirQuadro();
  }

  // ---- interação: arrastar gira a pizza (com inércia); o ponteiro inclina de leve
  let giro = 0;
  let velocidade = 0;
  let arrastando = false;
  let ultimoX = 0;
  let ultimoArraste = -10;
  const inclinacao = { x: 0, y: 0, alvoX: 0, alvoY: 0 };

  canvas.addEventListener('pointerdown', (e) => {
    arrastando = true;
    ultimoX = e.clientX;
    velocidade = 0;
    canvas.setPointerCapture(e.pointerId);
    canvas.parentElement?.classList.add('is-arrastando');
    pedirQuadro();
  });
  canvas.addEventListener('pointermove', (e) => {
    const caixa = canvas.getBoundingClientRect();
    inclinacao.alvoX = ((e.clientY - caixa.top) / caixa.height - 0.5) * 0.18;
    inclinacao.alvoY = ((e.clientX - caixa.left) / caixa.width - 0.5) * 0.18;
    if (arrastando) {
      const dx = e.clientX - ultimoX;
      ultimoX = e.clientX;
      giro += dx * 0.012;
      velocidade = dx * 0.7;
      ultimoArraste = tempo;
    }
    pedirQuadro();
  });
  const soltar = () => {
    arrastando = false;
    canvas.parentElement?.classList.remove('is-arrastando');
  };
  canvas.addEventListener('pointerup', soltar);
  canvas.addEventListener('pointercancel', soltar);
  canvas.addEventListener('pointerleave', () => { inclinacao.alvoX = 0; inclinacao.alvoY = 0; pedirQuadro(); });

  // ---- tamanho do canvas e enquadramento (folga para a pizza não encostar na borda)
  function redimensionar() {
    const { clientWidth: w, clientHeight: h } = canvas;
    if (!w || !h) return;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    const distancia = 4.4 * Math.max(1, 1.1 / camera.aspect);
    camera.position.set(0, distancia * 0.62, distancia * 0.78);
    camera.lookAt(0, -0.08, 0);
    camera.updateProjectionMatrix();
    pedirQuadro();
  }
  new ResizeObserver(redimensionar).observe(canvas);

  // ---- laço: só roda enquanto visível e com algo a animar
  let visivel = true;
  let pedido = 0;
  new IntersectionObserver(([entrada]) => {
    visivel = entrada.isIntersecting;
    if (visivel) pedirQuadro();
  }).observe(canvas);
  document.addEventListener('visibilitychange', () => { if (!document.hidden) pedirQuadro(); });

  function pedirQuadro() {
    if (!pedido && visivel && !document.hidden) pedido = requestAnimationFrame(quadro);
  }

  function quadro(agora) {
    pedido = 0;
    const dt = ultimoQuadro ? Math.min((agora - ultimoQuadro) / 1000, 0.05) : 0;
    ultimoQuadro = agora;
    tempo += dt;

    let ativo = arrastando || animando.size > 0;

    // Giro automático lento, pausado logo após o arraste.
    if (!reduzirMovimento && !arrastando && tempo - ultimoArraste > 2.5) giro += dt * 0.22;
    if (!arrastando && Math.abs(velocidade) > 0.001) {
      giro += velocidade * dt;
      velocidade = amortecer(velocidade, 0, 4, dt);
      ativo = true;
    }
    pizza.rotation.y = giro;

    const alvoX = reduzirMovimento ? 0 : inclinacao.alvoX;
    const alvoY = reduzirMovimento ? 0 : inclinacao.alvoY;
    inclinacao.x = amortecer(inclinacao.x, alvoX, 6, dt);
    inclinacao.y = amortecer(inclinacao.y, alvoY, 6, dt);
    mesa.rotation.set(inclinacao.x, 0, -inclinacao.y * 0.5);

    const escala = reduzirMovimento ? escalaAlvo : amortecer(pizza.scale.x, escalaAlvo, 7, dt);
    pizza.scale.setScalar(escala);

    animando.forEach((malha) => {
      if (posicionar(malha, tempo - malha.userData.inicio)) animando.delete(malha);
    });

    renderer.render(scene, camera);

    const assentando = Math.abs(escala - escalaAlvo) > 0.001
      || Math.abs(inclinacao.x - alvoX) > 0.001 || Math.abs(inclinacao.y - alvoY) > 0.001;
    if (ativo || assentando || !reduzirMovimento) pedirQuadro();
    else ultimoQuadro = 0; // o próximo quadro não deve ver o tempo parado como um salto
  }

  redimensionar();
  montarBorda(null);
  montarCortes(8);
  montarSabores([], new Set());
  anterior = { sabores: [], borda: null, massa: null, fatias: 8, adicionais: '' };
  pedirQuadro();

  return { atualizar };
}
