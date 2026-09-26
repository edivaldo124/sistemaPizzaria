# Vídeo do hero (página inicial)

`forno.mp4` e `forno-poster.jpg` são usados pelo hero de `/` (`templates/cardapio/inicio.html`).

## Vídeo atual

Animação gerada por código: a pizza é montada (massa, molho, queijo, coberturas) e
assada no forno conforme a rolagem. Para regerar ou ajustar, veja
`scripts/gerar_video_hero.py`.

## Trocando por filmagem própria

Basta substituir os dois arquivos mantendo os nomes.

- Horizontal (16:9), 6 a 10 segundos, até ~4 MB (ele carrega antes de tudo).
- Keyframes frequentes (`-g 6`) para o scrub não travar, sem áudio e com `faststart`:
  ```bash
  ffmpeg -i entrada.mp4 -c:v libx264 -crf 26 -g 6 -pix_fmt yuv420p -movflags +faststart -an forno.mp4
  ```
- Pôster obrigatório com o primeiro quadro (o iOS demora a exibir o vídeo):
  ```bash
  ffmpeg -i forno.mp4 -frames:v 1 -q:v 3 forno-poster.jpg
  ```
- Mantenha o assunto centralizado: no celular o vídeo é cortado nas laterais (`object-fit: cover`).
