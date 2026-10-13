"""Robotiq 2F-85 (STEP oficial, aberta, com dedos).

No STEP da Robotiq o eixo da garra é +Y e a base fica em y≈0. A pose é
calculada a partir da geometria: eixo = centro do Ø75 da base, assento =
ombro do Ø75 (onde termina o ressalto Ø71).
"""

from pathlib import Path

from build123d import Color, Compound, GeomType, Location, Pos, Rot, import_step

from .params import KINOVA, MOUNT

VENDOR = Path(__file__).resolve().parents[2] / "vendor"
GRIPPER_STEP = VENDOR / "Robotiq_2F85_Open.step"


def _seat_frame(gripper: Compound) -> Location:
    """Localização do centro do ombro de assento, no referencial do STEP."""
    rims = [
        e
        for e in gripper.edges()
        if e.geom_type == GeomType.CIRCLE and abs(e.radius - KINOVA.bracelet_d / 2) < 0.05
    ]
    seat = min(rims, key=lambda e: e.arc_center.Y)
    c = seat.arc_center
    return Pos(c.X, c.Y, c.Z)


def robotiq_2f85(seat_z: float = MOUNT.plate_t) -> Compound:
    """Garra no referencial do punho, com o assento em z = seat_z.

    seat_z = MOUNT.plate_t: sobre o espaçador; 0: direto no bracelete.

    Rot X +90° leva o eixo +Y da garra para +Z; o pino-guia da garra (em +X
    no STEP) cai sobre o furo do pino em +X.
    """
    g = import_step(GRIPPER_STEP)
    seat = _seat_frame(g)
    g = Pos(0, 0, seat_z) * Rot(90, 0, 0) * seat.inverse() * g
    g.label = "Robotiq_2F-85"
    for c in g.children:
        c.color = Color(0.25, 0.25, 0.27) if "base" in c.label else Color(0.6, 0.6, 0.62)
    return g
