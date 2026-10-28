// Traduz o nome de um sabor/adicional nas coberturas desenhadas na prévia 3D.
// O cadastro não guarda ingredientes, então a prévia se guia por palavras-chave do nome.

const REGRAS = [
  { chaves: ['calabresa', 'pepperoni', 'linguica', 'salame'], itens: ['calabresa', 'cebola'], cor: '#a8322a' },
  { chaves: ['marguerita', 'margherita', 'margarita'], itens: ['tomate', 'manjericao'], cor: '#d8432c' },
  { chaves: ['portuguesa'], itens: ['presunto', 'ovo', 'azeitona', 'cebola'], cor: '#e59a96' },
  { chaves: ['frango', 'galinha'], itens: ['frango', 'milho'], cor: '#e9c99a' },
  { chaves: ['bacon'], itens: ['bacon'], cor: '#a5452f' },
  { chaves: ['charque', 'carne seca', 'carne de sol', 'carne'], itens: ['charque', 'cebola'], cor: '#7a3a24' },
  { chaves: ['jerimum', 'abobora'], itens: ['jerimum'], cor: '#e58a2c' },
  { chaves: ['coalho'], itens: ['coalho', 'mel'], cor: '#f0d49a' },
  { chaves: ['atum'], itens: ['atum', 'cebola'], cor: '#c79a7a' },
  { chaves: ['palmito'], itens: ['palmito', 'azeitona'], cor: '#efe6c8' },
  { chaves: ['cogumelo', 'champignon', 'champignom', 'shimeji'], itens: ['cogumelo'], cor: '#c9b49a' },
  { chaves: ['presunto'], itens: ['presunto'], cor: '#e59a96' },
  { chaves: ['catupiry', 'requeijao', 'cream cheese'], itens: ['catupiry'], cor: '#fbf4e2' },
  { chaves: ['vegetariana', 'legumes', 'pimentao', 'brocolis'], itens: ['pimentao', 'tomate', 'cebola'], cor: '#3c8a3a' },
  { chaves: ['milho'], itens: ['milho'], cor: '#f2c230' },
  { chaves: ['tomate'], itens: ['tomate'], cor: '#d8432c' },
  { chaves: ['azeitona'], itens: ['azeitona'], cor: '#2a2522' },
  { chaves: ['cebola'], itens: ['cebola'], cor: '#efe2ea' },
  { chaves: ['manjericao', 'rucula'], itens: ['manjericao'], cor: '#3f7d3a' },
  { chaves: ['ovo'], itens: ['ovo'], cor: '#f6c94a' },
  { chaves: ['chocolate', 'nutella', 'brigadeiro', 'prestigio'], itens: ['granulado'], base: 'chocolate', cor: '#5a3222' },
  { chaves: ['doce de leite', 'romeu', 'goiabada'], itens: ['goiabada'], base: 'doce', cor: '#c46a3a' },
  { chaves: ['banana'], itens: ['banana', 'canela'], base: 'doce', cor: '#f2dc8a' },
  { chaves: ['morango'], itens: ['morango'], base: 'chocolate', cor: '#d63a4a' },
  { chaves: ['queijo', 'mussarela', 'muçarela', 'parmesao', 'gorgonzola', 'provolone'], itens: ['oregano'], cor: '#f3d27a' },
];

const semAcento = (texto) => texto.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();

export function coberturaDoSabor(nome) {
  const texto = semAcento(nome);
  const itens = new Set();
  let base = 'queijo';
  let cor = null;
  for (const regra of REGRAS) {
    if (!regra.chaves.some((chave) => texto.includes(semAcento(chave)))) continue;
    regra.itens.forEach((item) => itens.add(item));
    if (regra.base) base = regra.base;
    cor ??= regra.cor;
  }
  if (!itens.size) itens.add('oregano');
  return { itens: [...itens].slice(0, 4), base, cor: cor ?? '#f3d27a' };
}
