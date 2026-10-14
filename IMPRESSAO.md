# Impressão 3D — anel bipartido

Peças:

| peça | arquivo | tamanho | volume |
|---|---|---|---|
| metade da câmera, versão original | `out/ring_camera_half.stl` | 100 × 73 × 34 mm | 76 cm³ |
| metade da câmera, versão RGB centrado | `out/ring_rgb_camera_half.stl` | 118 × 87 × 36 mm | 111 cm³ |
| metade da câmera, versão estéreo centrado | `out/ring_stereo_camera_half.stl` | 100 × 87 × 36 mm | 105 cm³ |
| metade da câmera, versão D405 | `out/ring_d405_camera_half.stl` | 100 × 89 × 39 mm | 78 cm³ |
| metade de baixo (**a mesma nas quatro**) | `out/ring_lower_half.stl` | 100 × 42 × 29 mm | 23 cm³ |

Para trocar de versão, basta imprimir a outra metade da câmera: a metade de
baixo, as porcas e os M4 servem em todas. Os M3 da câmera mudam: M3 × 10 na
D435i, **M3 × 12** na D405 (rosca de 5,5 mm). Regere com
`.venv/bin/python build.py` depois de mudar `params.py`.

## Orientação

As duas peças **já saem do `build.py` na orientação de impressão**: a face
traseira do anel (a que fica voltada para a junta 6) apoiada na mesa e o eixo
do anel na vertical. Basta importar no fatiador e colocar na mesa, sem girar.

Por que essa orientação:

- As camadas ficam perpendiculares ao eixo do anel. O aperto dos M4 e o
  abraço no pescoço trabalham no plano das camadas, e não tentam descolar uma
  camada da outra.
- O furo do pescoço sai na vertical, redondo e liso, sem suporte. Com a face
  de corte na mesa, o furo viraria um arco de Ø70 em balanço.
- Tem pouca área em balanço e a maior área apoiada na mesa entre as
  orientações testadas.

## Suportes

- **Metade de baixo:** não precisa.
- **Metade da câmera:** as costas do apoio da câmera ficam a 43° da
  horizontal na versão original e a 45° nas demais versões,
  perto do limite usual de 45°. Na maioria das impressoras sai sem suporte. Se o
  fatiador marcar essa face, use suporte **só a partir da mesa**; não deve
  haver suporte dentro do furo nem nos alojamentos.
- **Versões RGB e estéreo centrado:** a placa que passa por cima da orelha fica em pé
  sobre a mesa (face de baixo vertical), sem balanço. Deixe um vão livre
  embaixo dela para empurrar a porca M4 no alojamento.
- Os rebaixos das cabeças M3 (Ø7,5) e os furos M4 horizontais são pontes
  curtas e saem sem suporte.

## Material e parâmetros

| item | recomendação |
|---|---|
| material | **PLA** (escolhido pelo usuário). PETG/ASA seriam mais tolerantes a calor e aperto; ver abaixo. |
| camada | 0,2 mm |
| paredes | 5 perímetros (≥ 2 mm) |
| topo/base | 5 camadas |
| preenchimento | 50 % giroide |
| velocidade nas paredes externas | reduzida, para o furo do pescoço sair liso |

### Cuidados com o PLA

O PLA é rígido e preciso, mas tem dois pontos fracos neste uso:

- **Fluência sob aperto:** sob carga constante (abraço dos M4 no pescoço,
  cabeças dos M3), o PLA cede devagar e o anel afrouxa. Aperte só até o anel
  não girar com a mão, **reaperte os M4 depois das primeiras horas de uso** e
  confira de tempos em tempos. Na D405, ponha arruela M3 (DIN 433, 0,5 mm)
  sob as cabeças dos M3 × 12 (o rebaixo Ø7,5 comporta); na D435i não, porque o
  M3 × 10 pegaria só 1,5 mm de rosca.
- **Calor:** o PLA começa a amolecer perto de 55–60 °C. O punho aquece em uso
  contínuo; se a carcaça ficar quente ao toque (acima de ~45 °C), o anel pode
  deformar. Nesse caso, reimprima em PETG ou ASA (mesmos STL).
- Não deixe a peça no carro ou ao sol: o PLA empena.

## Ajuste no pescoço

O furo copia o pescoço sem folga (`bore_clearance = 0`). Furos impressos
costumam sair um pouco menores, e a primeira camada pode espalhar (pé de
elefante). A entrada do furo tem chanfro de 0,5 mm para isso.

- Imprima primeiro a **metade de baixo** (é a menor) e teste no punho.
- As metades devem fechar sobre o pescoço deixando uma fresta entre elas (o
  projeto prevê 1 mm). Se encostarem antes de apertar o pescoço, o furo está
  grande; se não fecharem com a mão, está pequeno.
- Ajuste com a compensação de furos do fatiador (*XY hole compensation* /
  *horizontal expansion*) ou mude `bore_clearance` em `params.py`. Para usar
  fita de borracha no furo, use cerca de 0,5.

## Montagem

Ferragens: 2x M4 × 16 ISO 4762 (allen), 2x porca M4 ISO 4032 e, para a
câmera (8 mm de material sob a cabeça), 2x M3 × 10 na D435i (2 mm na rosca de
3,5) ou 2x M3 × 12 + arruela na D405 (3,5 mm na rosca de 5,5). A ponta do
M4 × 16 sai cerca de 2 mm além da porca.

1. **Porcas M4:** empurre cada porca no alojamento sextavado das orelhas da
   metade da câmera, pelo lado de fora. O alojamento tem 7,3 mm entre faces
   para porca de 7,0. Se ficar solta, uma gota de cola segura até a montagem.
2. **Câmera:** prenda a câmera no apoio com os 2x M3 por trás (M3 × 10 na
   D435i, M3 × 12 na D405), **antes de pôr o anel no robô**, de pé: o furo de
   1/4" voltado para o anel. Com o anel no punho, o acesso aos M3 fica apertado.
   Na versão RGB centrado, encoste a câmera no apoio antes de apertar: uma
   guinada de 1° tira a garra ~16 px do centro da imagem.
3. **Anel:** encaixe as duas metades no pescoço do módulo de interface, atrás
   dos botões de admitância (o lado mais estreito do furo vai para a junta 6).
   Gire o anel até as orelhas ficarem alinhadas com os botões e a câmera do
   lado oposto ao deslocamento dos botões (ver "ROS" no README).
4. **M4:** passe os parafusos pela metade de baixo e aperte alternando os
   dois lados, até o anel não girar com a mão. Não aperte demais: a carcaça
   do módulo tem cerca de 2 mm de parede.
5. **Garra:** monte a 2F-85 direto no punho, como de fábrica.
6. Na Web App, atualize a massa e o centro de massa da ferramenta
   (`SetToolConfiguration`), somando o anel, a câmera e o cabo USB.
