"""Espaçador entre o punho do Gen3 e a Robotiq 2F-85, com apoio para a D435i.

Os dois lados têm a interface do punho (Figura 38): embaixo o piloto Ø71 que
entra no bracelete, em cima o alojamento Ø71 para o ressalto da garra. Os 4 M5
da garra atravessam o espaçador e rosqueiam no punho.

Sistema local: origem no centro da face de assento sobre o bracelete
(Datum B da Figura 38), +Z saindo do robô ao longo do eixo da ferramenta,
+X apontando para o pino-guia Ø4, +Y para o topo do punho (onde fica o
módulo de visão nas versões que o têm). A câmera fica no ângulo
MOUNT.cam_side_deg em torno do eixo da ferramenta, medido a partir de +X.
"""

import math

from build123d import (
    Align,
    Axis,
    Box,
    Color,
    Cylinder,
    GeomType,
    Location,
    Plane,
    Polygon,
    Vector,
    extrude,
    revolve,
    Part,
    Pos,
    Rot,
    chamfer,
    fillet,
)

from .camera import m3_positions
from .params import CAM, KINOVA, MOUNT, SEAT

MIN = (Align.CENTER, Align.CENTER, Align.MIN)
MAX = (Align.CENTER, Align.CENTER, Align.MAX)


def _side_rot() -> Location:
    """Rotação que leva a câmera de -Y (onde é modelada) para cam_side_deg."""
    return Rot(0, 0, MOUNT.cam_side_deg + 90)


def _camera_pose_at_minus_y() -> Location:
    t = math.radians(MOUNT.cam_tilt_deg)
    half_h = CAM.height / 2
    # o canto frontal-interno da câmera fica a cam_gap do Ø do bracelete
    y = -(KINOVA.bracelet_d / 2 + MOUNT.cam_gap) - (half_h * math.cos(t) + CAM.depth * math.sin(t))
    z = MOUNT.plate_t + MOUNT.riser + half_h * math.sin(t)
    return Pos(0, y, z) * Rot(-MOUNT.cam_tilt_deg, 0, 0)


def camera_pose() -> Location:
    """Pose da face traseira da D435i no referencial do adaptador."""
    return _side_rot() * _camera_pose_at_minus_y()


def _bracket(cam_loc: Location, r: float, t: float) -> Part:
    """Aba + apoio da câmera: perfil no plano YZ extrudado em X."""
    tan_t = math.tan(math.radians(MOUNT.cam_tilt_deg))
    inner = cam_loc * Pos(0, CAM.height / 2, 0)  # canto do apoio voltado ao eixo
    outer = cam_loc * Pos(0, -CAM.height / 2, 0)
    yi, zi = inner.position.Y, inner.position.Z
    yo, zo = outer.position.Y, outer.position.Z
    pts = [
        (-(r - MOUNT.tab_fillet - 2), 0),  # dentro do disco
        (yo - zo * tan_t, 0),  # pé da face externa
        (yo, zo),
        (yi, zi),
        (yi - (zi - t) * tan_t, t),  # pé da face interna sobre a aba
        (-(r - MOUNT.tab_fillet - 2), t),
    ]
    profile = Plane.YZ * Polygon(*pts, align=None)

    def corners(idx):
        return [profile.vertices().sort_by_distance(Vector(0, *pts[i]))[0] for i in idx]

    # a face interna do apoio é curta (≈ riser); limita o raio dos seus cantos
    inner_len = math.dist(pts[3], pts[4])
    profile = fillet(corners([1, 2]), MOUNT.profile_fillet)
    profile = fillet(corners([3, 4]), min(MOUNT.profile_fillet, 0.4 * inner_len))
    return extrude(profile, MOUNT.pad_w / 2, both=True)


def _rim_chamfer_cutter(rim, r: float, t: float, c: float) -> Part:
    """Sólido de revolução que remove um chanfro 45° de lado c ao longo do arco rim."""

    def ang(p) -> float:
        return math.degrees(math.atan2(p.Y, p.X)) % 360

    a0, a1, am = ang(rim @ 0), ang(rim @ 1), ang(rim @ 0.5)
    start, end = (a0, a1) if (am - a0) % 360 < (a1 - a0) % 360 else (a1, a0)
    span = (end - start) % 360
    e = 0.01  # só o suficiente para cortar a aresta de forma limpa
    tri = Plane.XZ * Polygon((r - c - 1, t + 1), (r + e, t + 1), (r + e, t - c - e), align=None)
    return Rot(0, 0, start) * revolve(tri, Axis.Z, span)


def build_adapter() -> Part:
    r = KINOVA.bracelet_d / 2
    t = MOUNT.plate_t
    cam_loc = _camera_pose_at_minus_y()

    # disco + aba radial com apoio inclinado (perfil lateral extrudado)
    part = Cylinder(r, t, align=MIN) + _bracket(cam_loc, r, t)

    # arredonda a junção aba/disco
    joints = part.edges().filter_by(Axis.Z).filter_by(
        lambda e: e.center().Y < 0 and abs(abs(e.center().X) - MOUNT.pad_w / 2) < 0.1
    )
    part = fillet(joints, MOUNT.tab_fillet)

    # arredonda as bordas visíveis; ficam vivas a face inferior (assento no
    # bracelete), as costuras tangentes do filete da junção e a borda do disco
    # na face da ferramenta (recebe chanfro abaixo)
    def is_tool_rim(e) -> bool:
        return (
            e.geom_type == GeomType.CIRCLE
            and abs(e.radius - r) < 1e-3
            and abs(e.arc_center.Z - t) < 1e-3
        )

    def keep_sharp(e) -> bool:
        c = e.center()
        seam = e.geom_type == GeomType.LINE and abs(e.length - t) < 1e-3
        return abs(c.Z) < 1e-3 or seam or is_tool_rim(e)

    part = fillet(part.edges().filter_by(lambda e: not keep_sharp(e)), MOUNT.edge_fillet)

    # chanfro na borda da face da ferramenta, para o perfil continuar rente à
    # base Ø75 da garra (Robotiq 2F-85). Feito por corte de revolução: o
    # OpenCascade não combina chanfro e filete no mesmo vértice.
    rim = part.edges().filter_by(is_tool_rim)[0]
    part -= _rim_chamfer_cutter(rim, r, t, MOUNT.tool_face_chamfer)

    # piloto Ø71 h8
    pilot = Pos(0, 0, -KINOVA.pilot_h) * Cylinder(KINOVA.pilot_d / 2, KINOVA.pilot_h, align=MIN)
    part += chamfer(pilot.edges().group_by(Axis.Z)[0], KINOVA.pilot_chamfer)
    part = _side_rot() * part
    cam_loc = camera_pose()

    # --- furação comum aos dois lados (Figura 38) ---
    zb = -KINOVA.pilot_h
    through = t - zb
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * KINOVA.m5_dx / 2, sy * KINOVA.m5_dy / 2
            part -= Pos(x, y, zb) * Cylinder(KINOVA.m5_clear_d / 2, through, align=MIN)
    part -= Pos(KINOVA.dowel_x, 0, zb) * Cylinder(KINOVA.dowel_d / 2, through, align=MIN)
    pogo_len = KINOVA.pogo_x1 - KINOVA.pogo_x0
    part -= Pos(KINOVA.pogo_x0 + pogo_len / 2, 0, zb) * Box(pogo_len, KINOVA.pogo_w, through, align=MIN)

    # --- lado do robô: folga para os conectores do punho ---
    part -= Pos(0, 0, zb) * Cylinder(KINOVA.center_pocket_d / 2, KINOVA.pocket_depth, align=MIN)

    # --- lado da garra: alojamento Ø71 para o ressalto da 2F-85 ---
    part -= Pos(0, 0, t) * Cylinder(SEAT.recess_d / 2, SEAT.recess_depth, align=MAX)

    # chanfro de entrada nos furos pequenos da face da garra
    entries = part.edges().filter_by(GeomType.CIRCLE).filter_by(
        lambda e: abs(e.center().Z - (t - SEAT.recess_depth)) < 1e-3 and e.radius < 3
    )
    part = chamfer(entries, MOUNT.hole_chamfer)

    # --- 2x M3 para a câmera (parafusos por baixo, cabeça embutida) ---
    for x, y in m3_positions():
        part -= cam_loc * Pos(x, y, 0) * Cylinder(MOUNT.m3_clear_d / 2, MOUNT.m3_screw_engage, align=MAX)
        part -= cam_loc * Pos(x, y, -MOUNT.m3_screw_engage) * Cylinder(MOUNT.m3_cbore_d / 2, 200, align=MAX)

    part.label = "Kinova_Gen3_D435i_Adapter"
    part.color = Color(0.85, 0.45, 0.1)
    return part
