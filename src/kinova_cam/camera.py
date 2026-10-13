"""Intel RealSense D435i.

Usa o CAD oficial (vendor/, convertido de D435i_Solid.SLDPRT para STEP) quando
presente; senão, um envelope simplificado feito a partir do datasheet.

Sistema local: origem no centro da face traseira, +Z = eixo óptico,
X ao longo da largura, +Y = topo da câmera (1/4-20 fica em -Y).
"""

import math
from pathlib import Path

from build123d import (
    Align,
    Axis,
    Box,
    Color,
    Compound,
    Cylinder,
    Part,
    Plane,
    Pos,
    Rectangle,
    Rot,
    fillet,
    import_step,
    loft,
)

from .params import CAM, D435i

VENDOR = Path(__file__).resolve().parents[2] / "vendor"
OFFICIAL_BODY = VENDOR / "D435i_Solid - D435i Solid.step"
OFFICIAL_COVER = VENDOR / "D435i_Solid - D435i cvr.step"
BODY_COLOR = Color(0.15, 0.15, 0.17)


def m3_positions(cam: D435i = CAM) -> list[tuple[float, float]]:
    s = cam.m3_spacing / 2
    return [(-s, 0.0), (s, 0.0)]


def d435i() -> Part | Compound:
    """D435i oficial se disponível, senão o envelope do datasheet."""
    if OFFICIAL_BODY.exists():
        return load_official_d435i()
    return build_d435i()


def load_official_d435i() -> Compound:
    # o STEP oficial tem a frente em z=0 e o eixo óptico em +Z; basta trazer
    # a face traseira para z=0
    body = import_step(OFFICIAL_BODY)
    to_local = Pos(0, 0, -body.bounding_box().min.Z)
    body = to_local * body
    body.label = "D435i_body"
    body.color = BODY_COLOR
    children = [body]
    if OFFICIAL_COVER.exists():
        cover = to_local * import_step(OFFICIAL_COVER)
        cover.label = "D435i_cover"
        cover.color = Color(0.05, 0.05, 0.08)
        children.append(cover)
    return Compound(label="RealSense_D435i", children=children)


def build_d435i(cam: D435i = CAM) -> Part:
    body = Box(cam.width, cam.height, cam.depth, align=(Align.CENTER, Align.CENTER, Align.MIN))
    body = fillet(body.edges().filter_by(Axis.Y), cam.edge_r)

    # 2x M3 traseiros
    for x, y in m3_positions(cam):
        body -= Pos(x, y, 0) * Cylinder(1.25, cam.m3_depth, align=(Align.CENTER, Align.CENTER, Align.MIN))
    # 1/4-20 inferior
    body -= Pos(0, -cam.height / 2, cam.depth / 2) * Rot(-90, 0, 0) * Cylinder(
        3.2, 6.0, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    # lentes/emissor (ilustrativo, para indicar a frente)
    for x, d in ((-25.0, 9.0), (-10.0, 7.0), (10.0, 8.0), (25.0, 9.0)):
        body -= Pos(x, 0, cam.depth - 1.0) * Cylinder(d / 2, 1.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    # USB-C na lateral +X
    body -= Pos(cam.width / 2, 0, cam.depth / 2) * Box(6.0, 3.5, 9.5)

    body.label = "RealSense_D435i"
    body.color = BODY_COLOR
    return body



def _frustum(h_deg: float, v_deg: float, length: float) -> Part:
    """Pirâmide de visão com o vértice na origem, ao longo de +Z."""
    w = 2 * length * math.tan(math.radians(h_deg / 2))
    h = 2 * length * math.tan(math.radians(v_deg / 2))
    tip = 0.01
    return loft(
        [
            Plane.XY.offset(tip) * Rectangle(w * tip / length, h * tip / length),
            Plane.XY.offset(length) * Rectangle(w, h),
        ]
    )


def camera_fov(cam: D435i = CAM) -> Compound:
    """Cones de visão (profundidade e RGB) no referencial da câmera."""
    z0 = cam.depth - cam.zero_depth_to_front
    depth = Pos(cam.depth_origin_x, 0, z0) * _frustum(*cam.depth_fov, cam.fov_range)
    rgb = Pos(cam.rgb_origin_x, 0, z0) * _frustum(*cam.rgb_fov, cam.fov_range)
    depth.label, depth.color = "FOV_depth_87x58", Color(0.2, 0.5, 1.0)
    rgb.label, rgb.color = "FOV_rgb_69x42", Color(0.2, 0.85, 0.3)
    return Compound(label="FOV_D435i", children=[depth, rgb])
