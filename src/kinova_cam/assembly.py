"""Montagem: braço Gen3 6DOF sem visão (STEP oficial Kinova) + suporte + D435i + 2F-85.

Duas versões de suporte:
- "spacer": espaçador entre o punho e a garra (adapter.py);
- "ring": anel bipartido em volta do punho, garra direto no bracelete (clamp_ring.py).
"""

import math
from pathlib import Path

from build123d import Compound, GeomType, Location, Pos, Vector, import_step

from . import clamp_ring
from .adapter import build_adapter, camera_pose
from .camera import camera_fov, d435i
from .gripper import GRIPPER_STEP, robotiq_2f85
from .params import KINOVA, MOUNT


def wrist_assembly() -> Compound:
    """Adaptador + câmera + campo de visão (+ garra, se o STEP estiver em vendor/)."""
    adapter = build_adapter()
    cam = d435i()
    cam.locate(camera_pose())
    fov = camera_fov()
    fov.locate(camera_pose())
    children = [adapter, cam, fov]
    if GRIPPER_STEP.exists():
        children.append(robotiq_2f85())
    return Compound(label="Wrist_Camera_Mount", children=children)


def ring_assembly() -> Compound:
    """Anel bipartido + parafusos + câmera + campo de visão (+ garra direto no bracelete)."""
    cam_half, low_half = clamp_ring.build_ring()
    cam = d435i()
    cam.locate(clamp_ring.camera_pose())
    fov = camera_fov()
    fov.locate(clamp_ring.camera_pose())
    children = [cam_half, low_half, clamp_ring.build_fasteners(), cam, fov]
    if GRIPPER_STEP.exists():
        children.append(robotiq_2f85(seat_z=0.0))
    return Compound(label="Wrist_Clamp_Ring", children=children)


def ring_exploded(gap: float = 30.0) -> Compound:
    """Vista explodida do anel: metades afastadas, parafusos e câmera recuados."""
    cam_half, low_half = clamp_ring.build_ring()
    a = math.radians(MOUNT.cam_side_deg)
    up = Vector(math.cos(a), math.sin(a), 0)  # direção radial da câmera
    cam = d435i()
    cam.locate(Pos(*(up * gap)) * clamp_ring.camera_pose() * Pos(0, 0, gap))
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
    # STEP do Gen3 em posição zero: eixo da ferramenta paralelo a +Z, topo do
    # punho (lado do módulo de visão, quando existe) em +Y, como no adaptador.
    return Pos(c.X, c.Y, c.Z)


def full_assembly(arm_step: Path, variant: str = "spacer") -> Compound:
    arm = import_step(arm_step)
    arm.label = "Kinova_Gen3_6DOF"
    frame = tool_frame(arm)
    wrist = ring_assembly() if variant == "ring" else wrist_assembly()
    wrist.locate(frame)
    return Compound(label="Kinova_Gen3_D435i", children=[arm, wrist])
