"""Montagem: braço Gen3 6DOF sem visão (STEP oficial Kinova) + anel + câmera + 2F-85.

Versões do anel em params.PLACEMENTS ("ring": original; "ring_rgb": RGB
centrado na garra). A garra vai direto no bracelete.
"""

import math
from pathlib import Path

from build123d import Compound, GeomType, Location, Pos, Vector, import_step

from . import clamp_ring
from .camera import camera_body, camera_fov
from .gripper import GRIPPER_STEP, robotiq_2f85
from .params import KINOVA, MOUNT, PLACEMENTS, CamPlacement

ORIGINAL = PLACEMENTS["ring"]


def ring_assembly(cp: CamPlacement = ORIGINAL) -> Compound:
    """Anel bipartido + parafusos + câmera + campo de visão (+ garra direto no bracelete)."""
    cam_half, low_half = clamp_ring.build_ring(cp)
    cam = camera_body(cp.cam)
    cam.locate(clamp_ring.camera_pose(cp))
    fov = camera_fov(cp.cam)
    fov.locate(clamp_ring.camera_pose(cp))
    children = [cam_half, low_half, clamp_ring.build_fasteners(), cam, fov]
    if GRIPPER_STEP.exists():
        children.append(robotiq_2f85())
    return Compound(label="Wrist_Clamp_Ring", children=children)


def ring_exploded(cp: CamPlacement = ORIGINAL, gap: float = 30.0) -> Compound:
    """Vista explodida do anel: metades afastadas, parafusos e câmera recuados."""
    cam_half, low_half = clamp_ring.build_ring(cp)
    a = math.radians(MOUNT.cam_side_deg)
    up = Vector(math.cos(a), math.sin(a), 0)  # direção radial da câmera
    cam = camera_body(cp.cam)
    cam.locate(Pos(*(up * gap)) * clamp_ring.camera_pose(cp) * Pos(0, 0, gap))
    fasteners = clamp_ring.build_fasteners()
    parts = [Pos(*(up * gap)) * cam_half, Pos(*(up * -gap)) * low_half, cam]
    for f in fasteners.children:
        shift = gap * (2.0 if f.label.startswith("M4x") else 1.6)
        sign = -1 if f.label.startswith("M4x") else 1
        moved = Pos(*(up * (sign * shift))) * f
        moved.label, moved.color = f.label, f.color
        parts.append(moved)
    for p, src in zip(parts[:2], (cam_half, low_half)):
        p.label, p.color = src.label, src.color
    return Compound(label="Wrist_Clamp_Ring_Exploded", children=parts)


def tool_frame(arm: Compound) -> Location:
    """Localiza a face do bracelete (aro Ø75 de maior Z) no STEP do braço."""
    rims = [
        e
        for e in arm.edges()
        if e.geom_type == GeomType.CIRCLE and abs(e.radius - KINOVA.bracelet_d / 2) < 0.05
    ]
    top = max(rims, key=lambda e: e.arc_center.Z)
    c = top.arc_center
    # STEP do Gen3 em posição zero: eixo da ferramenta paralelo a +Z. Atenção:
    # o lado do módulo de visão (+Y do end_effector_link) é -Y deste STEP; a
    # câmera do modelo fica em +Y, isto é, do lado oposto (equivalente para
    # colisão, já que a j6 gira livre).
    return Pos(c.X, c.Y, c.Z)


def full_assembly(arm_step: Path, cp: CamPlacement = ORIGINAL) -> Compound:
    arm = import_step(arm_step)
    arm.label = "Kinova_Gen3_6DOF"
    frame = tool_frame(arm)
    wrist = ring_assembly(cp)
    wrist.locate(frame)
    return Compound(label="Kinova_Gen3_D435i", children=[arm, wrist])
