# kinova-cam — memória do projeto

Suporte de punho para RealSense D435i ou D405 no Kinova Gen3 **6DOF sem
módulo de visão** + Robotiq 2F-85, em build123d (B-rep). Visão geral e uso no README.md;
parâmetros em `src/kinova_cam/params.py`. Textos, comentários e README em
português.

## Versões

- Só existe o **anel bipartido** (`clamp_ring.py`): abraça o pescoço do
  módulo de interface, dz 21–49,5 atrás da face do bracelete (entre os botões
  de admitância e a junta 6). Garra direto no punho, pogo ligados.
- O espaçador (`adapter.py`) foi **apagado a pedido do usuário** em
  2026-10-13: cortava a ligação elétrica da garra (24 V + RS-485 só pelos 10
  pinos pogo). Não recriar.
- Duas versões da metade da câmera em `params.PLACEMENTS` (`CamPlacement`);
  a **metade de baixo é idêntica nas duas** (o usuário perguntou: dá para
  reaproveitar a impressa). Ao mudar o anel, conferir que `ring` e
  `ring_lower_half` não mudaram (volume 76283,157 / 22497,62 mm³).
  - `ring`: original, câmera centrada, 15°, gap 3.
  - `ring_rgb` (2026-10-13): pedido de garra no centro horizontal do RGB e
    profundidade do objeto entre os dedos. Câmera deslocada 32,5 mm (RGB em
    x=0), 20°, gap 15, `tab_heel` 18 (costas a 45°), placa sobre a orelha
    até `plate_r` 30. Usuário escolheu **compacto + profundidade em baixa
    resolução** (424×240) em vez de mastro alto: Z do objeto 115–156 mm.
    94% da região entre os dedos vista pelos dois IR; folga j5 28,2 mm.
  - `ring_d405` (2026-10-13, pedido do usuário, "manter compatível com a
    metade de baixo"): D405, imageador esquerdo (cor = profundidade) em x=0,
    15°, gap 3, `pad_w` 46, `tab_heel` 18 (45,6°). Z do objeto 112–153 mm
    (min-Z ~100 mm em 1280x720). Folga j5 35,4 mm. M3 × 12 + arruela.
  - `ring_stereo` (2026-10-13, sugestão aceita pelo usuário): D435i como
    ring_rgb (20°, gap 15, tab_heel 18) com o meio da linha de base em x=0
    (`center="stereo"`): IR em ±25, pontas 91/97%, RGB 268 px fora do centro.
    Folga j5 32,8 mm. `CamPlacement.center`: None | "rgb" | "stereo".
- Câmeras em `params.CameraSpec` (D435I, D405); `CamPlacement.cam`. STEP da
  D405: o usuário converteu no Onshape → `vendor/D405_Solid.step` (corpo +
  vidro no mesmo arquivo; o CAD não tem lentes nem nada da óptica).
- Os 3 STEP das câmeras em vendor/ são versionados (pedido do usuário,
  2026-10-13; exceções no .gitignore); o resto de vendor/ não.
- Convenção conferida pelo USB-C: +X local = esquerda da câmera nos dois CAD
  (D435i: USB em -X = direita, como no URDF; D405: USB em +X = esquerda).
- Profundidade nos dedos (garra aberta, `scripts/depth_view.py`): pontas com
  profundidade D435i ring 94/63%, ring_rgb 98/28% (IR2 sobre o dedo -X não vê
  a face interna da ponta), D405 97/100%. Hastes perto da palma < Z mín.
- **Impressão em PLA** (decisão do usuário, 2026-10-13): não recomendar
  PETG/ASA como imposição; IMPRESSAO.md traz cuidados (reaperto dos M4,
  calor do punho, 5 perímetros, 50%).
- Câmera **de pé** (2026-10-13, pedido do usuário): 1/4-20 voltado para o
  punho, garra embaixo na imagem (`MOUNT.cam_upright`). Antes o topo ficava
  para o punho. O apoio é o mesmo (`_seat_pose_at_minus_y`); só a pose da
  câmera gira 180° no eixo óptico, e em ring_rgb o deslocamento troca de lado.
- Pedido do usuário: a base do apoio da câmera se une ao anel em **todo o
  comprimento e largura** (perfil do apoio começa em y=-15, dentro do furo).

## Ferragens (anel)

- Fechamento: 2x M4 × 16 ISO 4762 + 2x porca M4 ISO 4032, eixo Y nas orelhas
  em ±X. Cabeça embutida 4,2 mm na metade de baixo; porca em alojamento
  sextavado (3,4 mm) na metade da câmera; furos Ø4,5.
- **M4 × 16 confirmado pelo usuário** (sai ~2 mm além da orelha; M4 × 14
  ficaria rente, M4 × 12 pegaria só 1,6 mm de rosca).
- Câmera: 2x M3 × 10 por trás (8 mm de material + 2 mm na rosca da D435i).
  Em 2026-10-13 o usuário pediu: parafusos entravam demais → material sob a
  cabeça 5 → 8 mm (`m3_screw_engage`) e rebaixo Ø6,5 → Ø7,5 (`m3_cbore_d`).

## Impressão (IMPRESSAO.md)

- Orientação: face traseira (z_rear, voltada à junta 6) na mesa, eixo do anel
  vertical. Os STL já saem assim do build.py (min Z = -49,5). Escolhida por
  análise de balanço: furo sem suporte, cargas no plano das camadas.
- Único ponto crítico: costas do apoio da câmera a 43° (ring) / 45°
  (ring_rgb) da horizontal (suporte só a partir da mesa, se o fatiador pedir).
- Material: **PLA** (usuário); bore_clearance 0 → testar a metade de baixo
  primeiro e ajustar compensação de furo ou bore_clearance.
- Ao mudar geometria: atualizar IMPRESSAO.md (volumes, ângulos), README e
  regerar imagens (`scripts/render_images.sh [versão]`,
  `scripts/camera_view.py`, `scripts/depth_view.py`; as das versões não
  originais vão para out/images/<versão>/).

## Dados de geometria (do STEP oficial / User Guide R07)

- Pescoço: Ø75 de dz 0 a 23; afina por spline até Ø70 em dz 50,4; junta 6 em
  dz 51. Perfil amostrado em `WRIST_NECK`.
- Botões de admitância em ±X, ângulos ~3–25° e 155–177°, dz 5,9–19,3, até r 38,3.
- Limites 6DOF: j2 ±128,9°, j3 ±147,8°, j5 ±120,3°; j1/j4/j6 infinitos.
  Eixo j5 paralelo a Y em (x=0, z=1009,2); face da ferramenta em z=1179,5.
- Pino-guia assumido em +X (o STEP não tem os furos). O módulo de visão
  (STEP VISION_V01) fica em **-Y** do mundo do STEP, não em +Y; o modelo põe
  a câmera em +Y (lado para onde os botões de admitância são deslocados,
  y 3,2–16,8).
- ROS (ros2_kortex, gen3 6dof): `end_effector_link` na pose zero = Rz(180°)
  do referencial do modelo (X e Y invertidos, Z igual), origem 2,87 mm atrás
  da face Ø75 (fundo do rebaixo Ø71, z 1176,63). O mundo do STEP coincide
  com o `base_link` (centro do aro em y 1,35 nos dois). A visão do Kinova
  fica em +Y do `end_effector_link`.
- FOV D435i: profundidade 87×58° a partir do IR esquerdo (+17,5 mm em X local,
  que é a esquerda da câmera); RGB 69×42° em +32,5 mm; zero de profundidade
  4,2 mm atrás do vidro. Dedos a ~145–155 mm, abaixo do min-Z em 1280×720.

## ROS (ros/kinova_cam_description, gerado por scripts/ros_export.py)

- Pacote ROS 2 ament_cmake: config/camera_mounts.yaml, launch de TF estático,
  xacros `kinova_cam_mount` (camera_link; driver com publish_tf) e
  `kinova_cam_mount_realsense` (xacro oficial; driver com publish_tf:=false),
  URDFs isolados e malhas (STL mm, referencial do modelo). Regerar após mudar
  geometria. As malhas `*_camera.stl` (CAD da Intel) ficam fora do git, como
  vendor/; por isso `camera_mesh` é false por padrão. Transformações em `src/kinova_cam/ros_frames.py`.
- Validação sem ROS: venv com `xacro` 2.1.1 + `urdf-parser-py` do PyPI, um
  módulo falso `ament_index_python` e um prefixo falso com os xacros oficiais
  da RealSense baixados do GitHub; os 12 casos batem com o YAML (< 0,001 mm).
- camera_link a partir do 1/4-20 (`CameraSpec.link_from_screw`, do URDF
  oficial) confere com o CAD nas duas câmeras.

## Armadilhas

- **build123d/OCC:** filete global no anel falha — filetar a junção
  apoio/anel primeiro e depois o resto, excluindo as costuras tangentes
  (`_smooth`, por normais das faces) e as arestas do apoio ao longo de X.
  Não intersectar com cilindro coincidente com o anel (faces sobrepostas
  quebram o filete): cortar com caixa e canto 1 mm dentro do anel.
  `Plane.XZ` tem normal -Y (use `Plane(..., z_dir=...)` explícito). Filhos de
  `Compound` não carregam a Location do pai: use `(frame * ch).solids()`.
- Malha da 2F-85: `tessellate` do sólido falha (faces degeneradas);
  tesselar face a face com try/except (ver `scripts/camera_view.py`).
- **FreeCAD é snap e só lê $HOME:** tudo passa por
  `~/snap/freecad/common/kinova-cam/` (`scripts/make_fcstd.sh [ring_rgb]`).
  O usuário reabre o projeto de lá.
- **Lotes/renders no FreeCAD: sempre `xvfb-run`** (`scripts/render_images.sh`).
  Na sessão do usuário o import longo trava a GUI e o GNOME mostra "forçar
  saída / esperar". Não alterar preferências do FreeCAD por script.
- GUI do FreeCAD: `setCameraOrientation` anima — encadear etapas com
  `QTimer.singleShot`; orientar com matriz Z-para-cima (setViewDirection gira
  a imagem); só ocultar/restaurar objetos, nunca forçar Visibility=True.
- Não usar `pkill -f`/`pgrep -f` com o nome no mesmo comando (casa com o
  próprio shell e o mata); pegar o PID com `ps ... | grep "[x]"`.

## Colisão (scripts/collision_sweep.py [ring|ring_rgb], ~1 min)

- ring (2026-10-10): j6 vs Wrist2 folga 2,7 mm; j5 ±120,3° × j6 (30°): folga
  mín 40,9 mm do antebraço com a câmera de pé (40,6 antes; módulo sem
  anel: 41,5 mm); contato só a
  140–145°, fora do limite.
- ring_rgb (2026-10-13): j6 vs Wrist2 2,7 mm; folga mín 28,2 mm; contato a
  partir de 132,8°. ring_d405: 2,7 mm; 35,4 mm; contato a partir de 137,8°.
  Refazer após mudar geometria.
- O script só mede até 20 mm (`distance_upper_bound`): folga maior sai "inf".
- Usa nuvem de pontos + cKDTree. BRepExtrema (distância B-rep exata) contra o
  STEP do braço é lento demais (>20 min sem fechar uma linha).
