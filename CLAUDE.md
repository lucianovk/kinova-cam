# kinova-cam — memória do projeto

Suporte de punho para RealSense D435i no Kinova Gen3 **6DOF sem módulo de
visão** + Robotiq 2F-85, em build123d (B-rep). Visão geral e uso no README.md;
parâmetros em `src/kinova_cam/params.py`. Textos, comentários e README em
português.

## Versões

- **Anel bipartido** (`clamp_ring.py`, versão principal): abraça o pescoço do
  módulo de interface, dz 21–49,5 atrás da face do bracelete (entre os botões
  de admitância e a junta 6). Garra direto no punho, pogo ligados.
- **Espaçador** (`adapter.py`): 12 mm entre punho e garra. **Corta a ligação
  elétrica** da garra (24 V + RS-485 só pelos 10 pinos pogo; a porta de
  expansão de 20 vias não tem RS-485). Foi por isso que o anel foi criado.
- Pedido do usuário: a base do apoio da câmera se une ao anel em **todo o
  comprimento e largura** (perfil do apoio começa em y=-15, dentro do furo).

## Ferragens (anel)

- Fechamento: 2x M4 × 16 ISO 4762 + 2x porca M4 ISO 4032, eixo Y nas orelhas
  em ±X. Cabeça embutida 4,2 mm na metade de baixo; porca em alojamento
  sextavado (3,4 mm) na metade da câmera; furos Ø4,5.
- **M4 × 16 confirmado pelo usuário** (sai ~2 mm além da orelha; M4 × 14
  ficaria rente, M4 × 12 pegaria só 1,6 mm de rosca).
- Câmera: 2x M3 × 8 por trás (5 mm de material + 3 mm na rosca da D435i).

## Impressão (IMPRESSAO.md)

- Orientação: face traseira (z_rear, voltada à junta 6) na mesa, eixo do anel
  vertical. Os STL já saem assim do build.py (min Z = -49,5). Escolhida por
  análise de balanço: furo sem suporte, cargas no plano das camadas.
- Único ponto crítico: costas do apoio da câmera a 43° da horizontal
  (suporte só a partir da mesa, se o fatiador pedir).
- Material PETG/ASA (sem PLA); bore_clearance 0 → testar a metade de baixo
  primeiro e ajustar compensação de furo ou bore_clearance.
- Ao mudar geometria: atualizar IMPRESSAO.md (volumes, ângulos), README e
  regerar imagens (`scripts/render_images.sh`).

## Dados de geometria (do STEP oficial / User Guide R07)

- Pescoço: Ø75 de dz 0 a 23; afina por spline até Ø70 em dz 50,4; junta 6 em
  dz 51. Perfil amostrado em `WRIST_NECK`.
- Botões de admitância em ±X, ângulos ~3–25° e 155–177°, dz 5,9–19,3, até r 38,3.
- Limites 6DOF: j2 ±128,9°, j3 ±147,8°, j5 ±120,3°; j1/j4/j6 infinitos.
  Eixo j5 paralelo a Y em (x=0, z=1009,2); face da ferramenta em z=1179,5.
- Pino-guia assumido em +X e topo do punho em +Y (o STEP não tem os furos).
- FOV D435i: profundidade 87×58° a partir do IR esquerdo (+17,5 mm em X local,
  que é a esquerda da câmera); RGB 69×42° em +32,5 mm; zero de profundidade
  4,2 mm atrás do vidro. Dedos a ~145–155 mm, abaixo do min-Z em 1280×720.

## Armadilhas

- **build123d/OCC:** filete global no anel falha — filetar a junção
  apoio/anel primeiro e depois o resto, excluindo as costuras tangentes.
  `Plane.XZ` tem normal -Y (use `Plane(..., z_dir=...)` explícito). Filhos de
  `Compound` não carregam a Location do pai: use `(frame * ch).solids()`.
- **FreeCAD é snap e só lê $HOME:** tudo passa por
  `~/snap/freecad/common/kinova-cam/` (`scripts/make_fcstd.sh [ring]`).
  O usuário reabre o projeto de lá.
- **Lotes/renders no FreeCAD: sempre `xvfb-run`** (`scripts/render_images.sh`).
  Na sessão do usuário o import longo trava a GUI e o GNOME mostra "forçar
  saída / esperar". Não alterar preferências do FreeCAD por script.
- GUI do FreeCAD: `setCameraOrientation` anima — encadear etapas com
  `QTimer.singleShot`; orientar com matriz Z-para-cima (setViewDirection gira
  a imagem); só ocultar/restaurar objetos, nunca forçar Visibility=True.
- Não usar `pkill -f`/`pgrep -f` com o nome no mesmo comando (casa com o
  próprio shell e o mata); pegar o PID com `ps ... | grep "[x]"`.

## Colisão (scripts/collision_sweep.py, ~1 min)

- Feita em 2026-10-10 com o apoio de comprimento total: j6 vs Wrist2 folga
  2,7 mm; j5 ±120,3° × j6 (30°): folga mín 40,6 mm do antebraço (módulo sem
  anel: 41,5 mm); contato só a 140–145°, fora do limite. Refazer após mudar
  geometria.
- Usa nuvem de pontos + cKDTree. BRepExtrema (distância B-rep exata) contra o
  STEP do braço é lento demais (>20 min sem fechar uma linha).
