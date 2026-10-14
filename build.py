"""Gera os arquivos em out/.

    .venv/bin/python build.py                      # as duas versões do anel
    .venv/bin/python build.py --variant ring_rgb   # só uma (ring | ring_rgb)
    .venv/bin/python build.py --full               # + montagem com o braço Gen3 completo

A metade de baixo é a mesma nas duas versões e sai só como ring_lower_half.
"""

import argparse
import sys
from pathlib import Path

from build123d import export_step, export_stl

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "src"))

from kinova_cam.assembly import full_assembly, ring_assembly, ring_exploded  # noqa: E402
from kinova_cam.camera import camera_body  # noqa: E402
from kinova_cam.clamp_ring import build_ring  # noqa: E402
from kinova_cam.params import PLACEMENTS  # noqa: E402

ARM_STEP = ROOT / "vendor" / "GEN3_6DOF_NO-VISION_V01.STEP"
OUT = ROOT / "out"


def export_part(part, name: str) -> None:
    export_step(part, OUT / f"{name}.step")
    export_stl(part, OUT / f"{name}.stl", tolerance=0.01, angular_tolerance=0.1)
    print(f"{name}: volume {part.volume / 1000:.1f} cm³, válido={part.is_valid}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true", help="inclui o braço Gen3 (vendor/)")
    ap.add_argument("--variant", choices=(*PLACEMENTS, "all"), default="all")
    args = ap.parse_args()
    variants = list(PLACEMENTS) if args.variant == "all" else [args.variant]
    if args.full and not ARM_STEP.exists():
        sys.exit(f"faltando {ARM_STEP}: rode scripts/fetch_vendor.sh")
    OUT.mkdir(exist_ok=True)
    for cam in {PLACEMENTS[n].cam for n in variants}:
        export_step(camera_body(cam), OUT / f"{cam.name.lower()}.step")

    for name in variants:
        cp = PLACEMENTS[name]
        cam_half, low_half = build_ring(cp)
        export_part(cam_half, f"{name}_camera_half")
        if name == variants[0]:  # igual nas duas versões
            export_part(low_half, "ring_lower_half")
        export_step(ring_assembly(cp), OUT / f"wrist_{name}_assembly.step")
        export_step(ring_exploded(cp), OUT / f"wrist_{name}_exploded.step")
        if args.full:
            export_step(full_assembly(ARM_STEP, cp), OUT / f"kinova_gen3_d435i_{name}.step")
    print(f"arquivos em {OUT}")


if __name__ == "__main__":
    main()
