# Impressão 3D — anel bipartido

Peças: `out/ring_camera_half.stl` (metade da câmera, 100 × 73 × 34 mm,
76 cm³) e `out/ring_lower_half.stl` (metade de baixo, 100 × 42 × 29 mm,
23 cm³). Regere com `.venv/bin/python build.py --variant ring` depois de
mudar `params.py`.

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
  horizontal, perto do limite usual de 45°. Na maioria das impressoras sai
  sem suporte. Se o fatiador marcar essa face, use suporte **só a partir da
  mesa**; não deve haver suporte dentro do furo nem nos alojamentos.
- Os rebaixos das cabeças M3 (Ø7,5) e os furos M4 horizontais são pontes
  curtas e saem sem suporte.

## Material e parâmetros

| item | recomendação |
|---|---|
| material | **PETG** ou **ASA**. PA-CF/PETG-CF se houver. Evite PLA: ele flui sob o aperto dos parafusos e amolece perto de 55 °C. |
| camada | 0,2 mm |
| paredes | 4 perímetros (≥ 1,6 mm) |
| topo/base | 5 camadas |
| preenchimento | 40 % giroide |
| velocidade nas paredes externas | reduzida, para o furo do pescoço sair liso |

O punho aquece em uso contínuo, mais um motivo para evitar o PLA.

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

Ferragens: 2x M4 × 16 ISO 4762 (allen), 2x porca M4 ISO 4032, 2x M3 × 10 para
a câmera (8 mm de material sob a cabeça + 2 mm na rosca). A ponta do M4 × 16
sai cerca de 2 mm além da porca.

1. **Porcas M4:** empurre cada porca no alojamento sextavado das orelhas da
   metade da câmera, pelo lado de fora. O alojamento tem 7,3 mm entre faces
   para porca de 7,0. Se ficar solta, uma gota de cola segura até a montagem.
2. **Câmera:** prenda a D435i no apoio com os 2x M3 × 10, por trás, **antes de
   pôr o anel no robô**. Com o anel no punho, o acesso aos M3 fica apertado.
3. **Anel:** encaixe as duas metades no pescoço do módulo de interface, atrás
   dos botões de admitância (o lado mais estreito do furo vai para a junta 6).
   Gire o anel até a câmera ficar no topo do punho.
4. **M4:** passe os parafusos pela metade de baixo e aperte alternando os
   dois lados, até o anel não girar com a mão. Não aperte demais: a carcaça
   do módulo tem cerca de 2 mm de parede.
5. **Garra:** monte a 2F-85 direto no punho, como de fábrica.
6. Na Web App, atualize a massa e o centro de massa da ferramenta
   (`SetToolConfiguration`), somando o anel, a câmera e o cabo USB.
