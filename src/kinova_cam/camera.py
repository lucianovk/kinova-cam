"""Câmeras Intel RealSense (D435i, D405).

Usa o CAD oficial (vendor/, convertido do .SLDPRT para STEP) quando presente;
senão, um envelope simplificado feito a partir do datasheet.

Sistema local: origem no centro da face traseira, +Z = eixo óptico,
X ao longo da largura (+X = esquerda da câmera), +Y = topo (1/4-20 em -Y).
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

from .params import CAM, CameraSpec

VENDOR = Path(__file__).resolve().parents[2] / "vendor"
BODY_COLOR = Color(0.15, 0.15, 0.17)


def m3_positions(cam: CameraSpec = CAM) -> list[tuple[float, float]]:
    s = cam.m3_spacing / 2
    return [(-s, 0.0), (s, 0.0)]


def camera_body(cam: CameraSpec = CAM) -> Part | Compound:
    """Câmera oficial se o STEP estiver em vendor/, senão o envelope do datasheet."""
    if (VENDOR / cam.step).exists():
        return load_official(cam)
    return build_envelope(cam)


def load_official(cam: CameraSpec = CAM) -> Compound:
    """STEP oficial no referencial da câmera.

    Os STEP oficiais têm a frente em z=0 e o eixo óptico em +Z; basta trazer a
    face traseira para z=0. O vidro vem num arquivo à parte (D435i) ou como
    segundo sólido do mesmo arquivo (D405).
    """
    solids = list(import_step(VENDOR / cam.step).solids())
    if cam.cover_step and (VENDOR / cam.cover_step).exists():
        solids += import_step(VENDOR / cam.cover_step).solids()
    body = max(solids, key=lambda x: x.volume)
    to_local = Pos(0, 0, -body.bounding_box().min.Z)
    children = []
    for x in solids:
        is_body = x is body
        x = to_local * x
        x.label = f"{cam.name}_{'body' if is_body else 'cover'}"
        x.color = BODY_COLOR if is_body else Color(0.05, 0.05, 0.08)
        children.append(x)
    return Compound(label=f"RealSense_{cam.name}", children=children)


def build_envelope(cam: CameraSpec = CAM) -> Part:
    body = Box(cam.width, cam.height, cam.depth, align=(Align.CENTER, Align.CENTER, Align.MIN))
    body = fillet(body.edges().filter_by(Axis.Y), cam.edge_r)

    # 2x M3 traseiros
    for x, y in m3_positions(cam):
        body -= Pos(x, y, 0) * Cylinder(1.25, cam.m3_depth, align=(Align.CENTER, Align.CENTER, Align.MIN))
    # 1/4-20 inferior
    body -= Pos(0, -cam.height / 2, cam.depth / 2) * Rot(-90, 0, 0) * Cylinder(
        3.2, 6.0, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    # imageadores (ilustrativo, para indicar a frente)
    for x in {cam.depth_origin_x, cam.depth_origin_x - cam.baseline, cam.rgb_origin_x}:
        body -= Pos(x, 0, cam.depth - 1.0) * Cylinder(3.5, 1.0, align=(Align.CENTER, Align.CENTER, Align.MIN))

    body.label = f"RealSense_{cam.name}"
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


def camera_fov(cam: CameraSpec = CAM) -> Compound:
    """Cones de visão (profundidade e RGB) no referencial da câmera."""
    z0 = cam.depth - cam.zero_depth_to_front
    depth = Pos(cam.depth_origin_x, 0, z0) * _frustum(*cam.depth_fov, cam.fov_range)
    rgb = Pos(cam.rgb_origin_x, 0, z0) * _frustum(*cam.rgb_fov, cam.fov_range)
    depth.label, depth.color = "FOV_depth_{:.0f}x{:.0f}".format(*cam.depth_fov), Color(0.2, 0.5, 1.0)
    rgb.label, rgb.color = "FOV_rgb_{:.0f}x{:.0f}".format(*cam.rgb_fov), Color(0.2, 0.85, 0.3)
    return Compound(label=f"FOV_{cam.name}", children=[depth, rgb])
