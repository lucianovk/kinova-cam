"""Parâmetros do suporte (mm, graus).

Fontes:
- Interface do Kinova Gen3: User Guide Gen3 R07, Figura 38 (padrão de furação)
  e flange de referência KR13890 (End_Effector_Reference_Design.zip).
- Robotiq 2F-85: STEP oficial (2F85_Opened_20190924). A base da garra tem a
  mesma interface do punho do Gen3 (Ø71, 4x M5 54 x 32, pino Ø4, pogo).
- RealSense D435i: datasheet Intel RealSense D400 Series (90 x 25 x 25 mm,
  2x M3 traseiros a 45 mm, 1x 1/4-20 inferior).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class KinovaInterface:
    bracelet_d: float = 75.0  # diâmetro externo do bracelete (medido: 75)
    pilot_d: float = 71.0  # piloto h8 que entra no furo do bracelete
    pilot_h: float = 2.8  # alojamento no bracelete tem 3.00 ±0.10; assenta no aro Ø75
    pilot_chamfer: float = 0.5
    m5_dx: float = 54.0  # 4x M5, retângulo 54 x 32
    m5_dy: float = 32.0
    m5_clear_d: float = 5.3  # passantes: os M5 da garra rosqueiam no punho
    dowel_d: float = 4.0  # pino-guia Ø4 em (30.5, 0), passante
    dowel_x: float = 30.5
    # janela passante para os pogo (pinos no punho, contatos na garra em
    # x 4..21.4, y ±4.9): espaço para uma placa de passagem
    pogo_x0: float = 3.0
    pogo_x1: float = 27.0
    pogo_w: float = 11.0
    center_pocket_d: float = 40.0
    pocket_depth: float = 4.0  # medido a partir da face do piloto


@dataclass(frozen=True)
class GripperSeat:
    """Lado da ferramenta: réplica do alojamento do bracelete para a 2F-85."""

    recess_d: float = 71.0  # H8 para o ressalto Ø71 da garra (folgar se impresso)
    recess_depth: float = 3.3  # ressalto da garra tem 3.1


@dataclass(frozen=True)
class D435i:
    width: float = 90.0  # X
    height: float = 25.0  # Y
    depth: float = 25.0  # Z (eixo óptico)
    edge_r: float = 3.0
    m3_spacing: float = 45.0
    m3_depth: float = 3.5  # medido no CAD oficial
    # campo de visão (datasheet D400): profundidade 87° x 58°, RGB 69° x 42°.
    # Posições das lentes como no URDF oficial (realsense-ros, _d435.urdf.xacro):
    # origem da profundidade no imageador IR esquerdo, 17.5 mm do centro;
    # RGB 15 mm além dele; profundidade zero 4.2 mm atrás do vidro frontal.
    # No referencial da câmera, +X é a esquerda dela (olhando para fora).
    depth_fov: tuple[float, float] = (87.0, 58.0)
    rgb_fov: tuple[float, float] = (69.0, 42.0)
    depth_origin_x: float = 17.5
    rgb_origin_x: float = 32.5
    zero_depth_to_front: float = 4.2
    fov_range: float = 300.0  # comprimento desenhado dos cones


@dataclass(frozen=True)
class Mount:
    plate_t: float = 12.0  # espessura do flange adaptador
    cam_gap: float = 3.0  # folga radial entre Ø75 e o corpo da câmera
    cam_side_deg: float = 90.0  # posição angular da câmera (90 = +Y, topo do punho)
    cam_tilt_deg: float = 15.0  # inclinação do eixo óptico em direção ao eixo da ferramenta
    riser: float = 6.0  # altura mínima do apoio acima do flange
    pad_w: float = 70.0  # largura do apoio da câmera (X)
    m3_clear_d: float = 3.4
    m3_cbore_d: float = 6.5
    m3_screw_engage: float = 5.0  # material entre cabeça M3 e câmera
    tab_fillet: float = 6.0  # junção aba/disco
    edge_fillet: float = 2.0  # bordas externas
    tool_face_chamfer: float = 0.5  # borda da face onde assenta a garra
    profile_fillet: float = 3.0  # cantos do perfil lateral do apoio
    hole_chamfer: float = 0.5  # entrada dos furos na face da ferramenta


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
    tab_heel: float = 4.0  # altura do apoio acima do anel na face traseira
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
SEAT = GripperSeat()
CAM = D435i()
MOUNT = Mount()
RING = ClampRing()
