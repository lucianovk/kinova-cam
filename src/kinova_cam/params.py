"""Parâmetros do suporte (mm, graus).

Fontes:
- Kinova Gen3 6DOF: STEP oficial (GEN3_6DOF_NO-VISION_V01) e User Guide R07.
- Robotiq 2F-85: STEP oficial (2F85_Opened_20190924).
- RealSense D435i: datasheet Intel RealSense D400 Series (90 x 25 x 25 mm,
  2x M3 traseiros a 45 mm, 1x 1/4-20 inferior).
- RealSense D405: CAD oficial (D405_Solid.SLDPRT -> STEP) e URDF oficial
  (realsense-ros, _d405.urdf.xacro).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class KinovaInterface:
    bracelet_d: float = 75.0  # diâmetro externo do bracelete (medido: 75)
    # end_effector_link do ros2_kortex (gen3 6dof): no eixo, 2,87 mm atrás da
    # face do aro Ø75 (fundo do rebaixo Ø71); cinemática direta do URDF na pose
    # zero (z 1176,63) contra o STEP (face em z 1179,5)
    ee_link_behind_face: float = 2.87


@dataclass(frozen=True)
class CameraSpec:
    """Câmera RealSense: corpo, furação traseira e óptica.

    Referencial da câmera: origem no centro da face traseira, +Z = eixo
    óptico, +Y = topo (o 1/4-20 fica em -Y), +X = esquerda dela (olhando para
    fora; nos dois CAD oficiais o USB-C fica do lado indicado pelo URDF).
    Posições das lentes como no URDF oficial (realsense-ros): origem da
    profundidade no imageador esquerdo.
    """

    name: str
    width: float  # X
    height: float  # Y
    depth: float  # Z (eixo óptico)
    m3_spacing: float  # 2x M3 na face traseira, em y = 0
    m3_depth: float  # profundidade da rosca (CAD oficial)
    depth_fov: tuple[float, float]
    rgb_fov: tuple[float, float]
    depth_origin_x: float  # imageador esquerdo (origem da profundidade)
    rgb_origin_x: float
    baseline: float  # imageador direito em depth_origin_x - baseline
    zero_depth_to_front: float  # plano de profundidade zero atrás da frente
    # camera_link em relação ao <name>_bottom_screw_frame (1/4-20), no URDF
    # oficial (realsense2_description): x frente, y esquerda, z cima
    link_from_screw: tuple[float, float, float]
    step: str  # STEP oficial em vendor/ (corpo; o vidro pode vir junto)
    cover_step: str | None = None
    edge_r: float = 3.0
    fov_range: float = 300.0  # comprimento desenhado dos cones


# D435i: profundidade 87° x 58°, RGB 69° x 42° (datasheet D400); IR esquerdo a
# 17,5 mm do centro, RGB 15 mm além; zero de profundidade 4,2 mm atrás do vidro.
D435I = CameraSpec(
    "D435i", width=90.0, height=25.0, depth=25.0, m3_spacing=45.0, m3_depth=3.5,
    depth_fov=(87.0, 58.0), rgb_fov=(69.0, 42.0), depth_origin_x=17.5, rgb_origin_x=32.5,
    baseline=50.0, zero_depth_to_front=4.2, link_from_screw=(0.0106, 0.0175, 0.0125),
    step="D435i_Solid - D435i Solid.step", cover_step="D435i_Solid - D435i cvr.step",
)
# D405: a cor sai do próprio imageador esquerdo (9 mm do centro), já alinhada
# com a profundidade; linha de base 18 mm; zero 3,7 mm atrás do vidro + 0,1.
# Min-Z ~70 mm em 848x480, ~100 mm em 1280x720. M3 traseiros com 5,5 mm de rosca.
D405 = CameraSpec(
    "D405", width=42.0, height=42.0, depth=23.0, m3_spacing=20.0, m3_depth=5.5,
    depth_fov=(87.0, 58.0), rgb_fov=(87.0, 58.0), depth_origin_x=9.0, rgb_origin_x=9.0,
    baseline=18.0, zero_depth_to_front=3.8, link_from_screw=(0.01085, 0.009, 0.021),
    step="D405_Solid.step",
)


@dataclass(frozen=True)
class Mount:
    """Apoio da câmera no anel (comum às versões)."""

    cam_side_deg: float = 90.0  # posição angular da câmera (90 = +Y, topo do punho)
    # True: câmera de pé, com o 1/4-20 voltado para o punho (imagem com a garra
    # embaixo). False: topo da câmera voltado para o punho (até 2026-10-13).
    # O apoio é o mesmo; muda a pose da câmera (e o lado do deslocamento RGB).
    cam_upright: bool = True
    m3_clear_d: float = 3.4
    m3_cbore_d: float = 7.5  # cabeça M3 (5,5) + folga; era 6,5
    m3_screw_engage: float = 8.0  # material entre cabeça M3 e câmera; era 5 (parafusos entravam demais)
    profile_fillet: float = 3.0  # cantos do perfil lateral do apoio


@dataclass(frozen=True)
class CamPlacement:
    """Câmera e posição dela em cada versão do anel (a metade de baixo é a mesma)."""

    name: str
    tilt_deg: float  # inclinação do eixo óptico em direção ao eixo da ferramenta
    gap: float  # folga radial entre o Ø75 e o canto frontal-interno da câmera
    # o que fica no plano do eixo da ferramenta (desloca a câmera ao longo da
    # largura): None = centro do corpo; "rgb" = lente RGB (garra no centro
    # horizontal da imagem RGB); "stereo" = meio da linha de base (os dois
    # imageadores entre os dedos)
    center: str | None = None
    # parte do apoio fora do Ø do anel (câmera deslocada): base da placa,
    # medida do eixo; dentro do Ø do anel o apoio desce até o anel
    plate_r: float = 30.0
    # base do apoio além do Ø do anel, na face traseira (mesa de impressão):
    # define a inclinação das costas do apoio
    tab_heel: float = 4.0
    cam: CameraSpec = D435I
    pad_w: float = 70.0  # largura do apoio da câmera (X)


@dataclass(frozen=True)
class ClampRing:
    """Anel bipartido no pescoço do módulo de interface, atrás da faixa Ø75.

    z medido a partir da face do bracelete (assento da garra), negativo para
    dentro do robô. Os botões de admitância terminam em z -19.3 e a junta 6
    fica em z -51.0.
    """

    z_front: float = -21.0
    z_rear: float = -49.5
    outer_d: float = 85.0
    bore_clearance: float = 0.0  # folga radial (ex.: 0.5 para fita de borracha)
    split_gap: float = 1.0  # entre as metades, para o aperto
    bore_chamfer: float = 0.5
    edge_fillet: float = 1.5
    # orelhas de aperto em ±X, só na parte traseira (deixa espaço para o dedo
    # nos botões, que ficam logo à frente, em ±X)
    ear_len: float = 16.0
    ear_h: float = 9.0  # altura de cada metade da orelha a partir do plano de corte
    ear_x: float = 50.0  # extremidade da orelha
    # 2x M4 ISO 4762 (allen) + porca ISO 4032 embutida na metade da câmera
    screw_x: float = 44.0
    screw_clear_d: float = 4.5
    head_cbore_d: float = 7.5
    head_cbore_depth: float = 4.2
    nut_af: float = 7.3  # porca M4 (7.0) + folga
    nut_depth: float = 3.4
    # câmera: aresta traseira interna da D435i, encostada na face do anel
    cam_z: float = -21.0
    tab_t: float = 10.0  # espessura do apoio atrás da câmera
    tab_fillet: float = 6.0  # junção apoio/anel


# Perfil externo do pescoço do módulo de interface (Gen3 6DOF sem visão):
# (distância atrás da face do bracelete, raio). Amostrado do STEP oficial
# (GEN3_6DOF_NO-VISION_V01); a superfície é de revolução e tangente nas pontas.
WRIST_NECK = (
    (21.0, 37.500),
    (23.0, 37.500),
    (25.0, 37.483),
    (27.5, 37.405),
    (30.0, 37.245),
    (32.5, 36.995),
    (35.0, 36.662),
    (37.5, 36.285),
    (40.0, 35.904),
    (42.5, 35.556),
    (45.0, 35.280),
    (47.5, 35.094),
    (49.5, 35.019),
)


KINOVA = KinovaInterface()
CAM = D435I
MOUNT = Mount()
RING = ClampRing()

# Versões do anel:
# - ring: câmera centrada no punho, 15°, rente ao Ø75 (versão original);
# - ring_rgb: RGB no plano do eixo da ferramenta (garra no centro horizontal da
#   imagem), 20° e 12 mm mais alta, para o objeto entre os dedos ficar visível
#   pelos dois IR (Z de profundidade 115–156 mm: usar 424x240);
# - ring_stereo: como ring_rgb, mas com o meio da linha de base no eixo: os
#   dois IR ficam entre os dedos e as duas pontas têm profundidade (o RGB fica
#   40 mm fora do eixo);
# - ring_d405: RealSense D405, cor/profundidade centradas na garra.
PLACEMENTS = {
    "ring": CamPlacement("ring", tilt_deg=15.0, gap=3.0),
    # tab_heel 18: costas do apoio a 45° (impressão sem suporte)
    "ring_rgb": CamPlacement("ring_rgb", tilt_deg=20.0, gap=15.0, center="rgb", tab_heel=18.0),
    "ring_stereo": CamPlacement("ring_stereo", tilt_deg=20.0, gap=15.0, center="stereo", tab_heel=18.0),
    # D405: imageador esquerdo (cor + profundidade) no plano do eixo da garra;
    # objeto entre os dedos a Z 112–153 mm (min-Z ~100 mm em 1280x720)
    "ring_d405": CamPlacement(
        "ring_d405", tilt_deg=15.0, gap=3.0, center="rgb", tab_heel=18.0, cam=D405, pad_w=46.0
    ),
}
