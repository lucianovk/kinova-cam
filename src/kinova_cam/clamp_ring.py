"""Anel bipartido em volta do punho do Gen3, com apoio para a D435i.

Alternativa ao espaçador: a 2F-85 continua montada direto no punho, então os
pinos pogo (24 V + RS-485) ligam a garra normalmente. O anel abraça o pescoço
do módulo de interface, entre os botões de admitância e a junta 6; esse trecho
gira junto com a ferramenta. O furo copia o perfil do pescoço (WRIST_NECK),
que afina de Ø75 para Ø70: o anel não escorrega em direção à garra.

As duas metades se fecham com 2x M4 ISO 4762 (allen) nas orelhas em ±X. Os
parafusos entram pela metade de baixo e rosqueiam em porcas embutidas na
metade da câmera.

Sistema local: o mesmo do adaptador, com origem no centro da face do bracelete
(assento da garra), +Z ao longo da ferramenta (o anel fica em z < 0), +X para
o pino-guia e +Y para o topo do punho. A câmera fica em MOUNT.cam_side_deg.
"""

import math

from build123d import (
    Align,
    Axis,
    Box,
    Color,
    Compound,
    Cylinder,
    Face,
    GeomType,
    Line,
    Location,
    Part,
    Plane,
    Polygon,
    Pos,
    RegularPolygon,
    Rot,
    Spline,
    Vector,
    Wire,
    chamfer,
    extrude,
    fillet,
    revolve,
)

from .camera import m3_positions
from .params import CAM, KINOVA, MOUNT, RING, WRIST_NECK

MIN = (Align.CENTER, Align.CENTER, Align.MIN)
MAX = (Align.CENTER, Align.CENTER, Align.MAX)
BIG = 400.0


def _side_rot() -> Location:
    """Rotação que leva a câmera de -Y (onde é modelada) para cam_side_deg."""
    return Rot(0, 0, MOUNT.cam_side_deg + 90)


def _camera_pose_at_minus_y() -> Location:
    t = math.radians(MOUNT.cam_tilt_deg)
    half_h = CAM.height / 2
    # canto frontal-interno a cam_gap do Ø75; aresta traseira interna em cam_z
    y = -(KINOVA.bracelet_d / 2 + MOUNT.cam_gap) - (half_h * math.cos(t) + CAM.depth * math.sin(t))
    z = RING.cam_z + half_h * math.sin(t)
    return Pos(0, y, z) * Rot(-MOUNT.cam_tilt_deg, 0, 0)


def camera_pose() -> Location:
    """Pose da face traseira da D435i no referencial do punho."""
    return _side_rot() * _camera_pose_at_minus_y()


def _neck() -> Part:
    """Sólido de revolução com o perfil do pescoço (+ folga), para o furo."""
    c = RING.bore_clearance
    zf, zr = RING.z_front, RING.z_rear
    pts = [Vector(r + c, 0, -dz) for dz, r in WRIST_NECK if dz >= 23.0]
    r0 = WRIST_NECK[0][1] + c
    e = 1.0  # passa das faces do anel para o corte ficar limpo
    edges = [
        Line((0, 0, zf + e), (r0, 0, zf + e)),
        Line((r0, 0, zf + e), pts[0]),
        Spline(*pts, tangents=((0, 0, -1), (0, 0, -1))),
        Line(pts[-1], (pts[-1].X, 0, zr - e)),
        Line((pts[-1].X, 0, zr - e), (0, 0, zr - e)),
        Line((0, 0, zr - e), (0, 0, zf + e)),
    ]
    return revolve(Face(Wire(edges)), Axis.Z, 360)


def _tab(cam_loc: Location, ro: float) -> Part:
    """Apoio da câmera em -Y: perfil no plano YZ extrudado em X."""
    t = math.radians(MOUNT.cam_tilt_deg)
    inner = cam_loc * Pos(0, CAM.height / 2, 0)  # aresta traseira voltada ao eixo
    outer = cam_loc * Pos(0, -CAM.height / 2, 0)
    yi, zi = inner.position.Y, inner.position.Z
    yo, zo = outer.position.Y, outer.position.Z
    # costas do apoio: paralelas à face da câmera, tab_t atrás dela
    yb, zb = yo - RING.tab_t * math.sin(t), zo - RING.tab_t * math.cos(t)
    # a base desce até dentro do furo (cortado depois), para o apoio se unir
    # ao anel em toda a largura e todo o comprimento
    y_in = -15.0
    pts = [
        (y_in, RING.z_front),
        (yi, zi),
        (yo, zo),
        (yb, zb),
        (-(ro + RING.tab_heel), RING.z_rear),  # base cobre o anel até a face traseira
        (y_in, RING.z_rear),
    ]
    profile = Plane.YZ * Polygon(*pts, align=None)

    def corners(idx):
        return [profile.vertices().sort_by_distance(Vector(0, *pts[i]))[0] for i in idx]

    profile = fillet(corners([2, 3]), MOUNT.profile_fillet)
    return extrude(profile, MOUNT.pad_w / 2, both=True)


def _ears(ro: float) -> Part:
    z0 = RING.z_rear
    x0 = ro - 4
    ears = None
    for sx in (-1, 1):
        ear = Pos(sx * (x0 + RING.ear_x) / 2, 0, z0) * Box(
            RING.ear_x - x0, 2 * RING.ear_h, RING.ear_len, align=MIN
        )
        outer = ear.edges().filter_by(lambda e: abs(abs(e.center().X) - RING.ear_x) < 1e-3)
        ear = fillet(outer, 3.0)
        ears = ear if ears is None else ears + ear
    return ears


def screw_positions() -> list[tuple[float, float]]:
    """(x, z) dos 2 parafusos M4; o eixo deles é Y."""
    z = RING.z_rear + RING.ear_len / 2
    return [(-RING.screw_x, z), (RING.screw_x, z)]


def _blank() -> Part:
    """Anel inteiro (antes do corte em duas metades), com a câmera em -Y."""
    ro = RING.outer_d / 2
    length = RING.z_front - RING.z_rear
    cam_loc = _camera_pose_at_minus_y()

    ring = Pos(0, 0, RING.z_rear) * Cylinder(ro, length, align=MIN)
    part = (ring + _tab(cam_loc, ro)).clean()

    # o apoio se une ao anel em todo o comprimento; arredonda a junção
    joints = part.edges().filter_by(Axis.Z).filter_by(
        lambda e: e.center().Y < 0 and abs(abs(e.center().X) - MOUNT.pad_w / 2) < 0.1
    )
    part = fillet(joints, RING.tab_fillet)

    # arredonda as bordas; ficam de fora as costuras tangentes (dos filetes da
    # junção e do perfil do apoio), onde não há aresta viva
    def seam(e) -> bool:
        if e.geom_type != GeomType.LINE:
            return False
        along_ring = abs(e.length - length) < 1e-3 and abs(e.center().X) > MOUNT.pad_w / 2 - 1
        along_tab = abs(e.length - MOUNT.pad_w) < 1e-3
        return along_ring or along_tab

    part = fillet(part.edges().filter_by(lambda e: not seam(e)), RING.edge_fillet)
    part += _ears(ro)

    part -= _neck()
    entries = part.edges().filter_by(GeomType.CIRCLE).filter_by(
        lambda e: e.radius < ro - 3
        and min(abs(e.arc_center.Z - RING.z_front), abs(e.arc_center.Z - RING.z_rear)) < 1e-3
    )
    part = chamfer(entries, RING.bore_chamfer)

    # 2x M3 para a câmera (parafusos por trás, cabeça embutida)
    for x, y in m3_positions():
        part -= cam_loc * Pos(x, y, 0) * Cylinder(MOUNT.m3_clear_d / 2, MOUNT.m3_screw_engage, align=MAX)
        part -= cam_loc * Pos(x, y, -MOUNT.m3_screw_engage) * Cylinder(MOUNT.m3_cbore_d / 2, 200, align=MAX)

    # M4 passantes nas orelhas (eixo Y)
    for x, z in screw_positions():
        part -= Pos(x, 0, z) * Rot(90, 0, 0) * Cylinder(RING.screw_clear_d / 2, BIG)
    return part


def build_ring() -> tuple[Part, Part]:
    """(metade da câmera, metade de baixo), já na posição de montagem."""
    blank = _blank()
    g = RING.split_gap / 2
    cam_half = blank & Pos(0, -g, 0) * Box(BIG, BIG, BIG, align=(Align.CENTER, Align.MAX, Align.CENTER))
    low_half = blank & Pos(0, g, 0) * Box(BIG, BIG, BIG, align=(Align.CENTER, Align.MIN, Align.CENTER))

    # porcas M4 embutidas na metade da câmera; cabeças na metade de baixo
    nut_r = RING.nut_af / 2 / math.cos(math.radians(30))
    for x, z in screw_positions():
        pocket = Plane((x, -RING.ear_h, z), z_dir=(0, 1, 0)) * RegularPolygon(nut_r, 6)
        cam_half -= extrude(pocket, RING.nut_depth)
        low_half -= Pos(x, RING.ear_h, z) * Rot(90, 0, 0) * Cylinder(
            RING.head_cbore_d / 2, RING.head_cbore_depth, align=MIN
        )

    cam_half = _side_rot() * cam_half
    low_half = _side_rot() * low_half
    cam_half.label = "Clamp_Ring_Camera_Half"
    low_half.label = "Clamp_Ring_Lower_Half"
    cam_half.color = low_half.color = Color(0.85, 0.45, 0.1)
    return cam_half, low_half


def build_fasteners() -> Compound:
    """2x M4x16 ISO 4762 + 2x porca M4, simplificados, na posição de montagem."""
    parts = []
    head_top = RING.ear_h - RING.head_cbore_depth  # face de apoio da cabeça (lado +Y no modelo)
    for i, (x, z) in enumerate(screw_positions()):
        screw = Pos(x, head_top, z) * Rot(-90, 0, 0) * (
            Cylinder(3.5, 4.0, align=MIN) + Pos(0, 0, -16) * Cylinder(2.0, 16, align=MIN)
        )
        screw = screw - Pos(x, head_top + 4.0, z) * Rot(90, 0, 0) * Cylinder(1.5, 2.5, align=MIN)
        nut_r = 7.0 / 2 / math.cos(math.radians(30))
        seat = -(RING.ear_h - RING.nut_depth)  # fundo do alojamento da porca
        nut = extrude(Plane((x, seat, z), z_dir=(0, -1, 0)) * RegularPolygon(nut_r, 6), 3.2)
        nut -= Pos(x, 0, z) * Rot(90, 0, 0) * Cylinder(2.0, BIG)
        screw, nut = _side_rot() * screw, _side_rot() * nut
        screw.label, nut.label = f"M4x16_ISO4762_{i + 1}", f"M4_ISO4032_{i + 1}"
        screw.color = nut.color = Color(0.1, 0.1, 0.1)
        parts += [screw, nut]
    return Compound(label="Fasteners", children=parts)
