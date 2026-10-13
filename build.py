"""Gera os arquivos em out/.

    .venv/bin/python build.py                  # as duas versões: espaçador e anel
    .venv/bin/python build.py --variant ring   # só o anel bipartido
    .venv/bin/python build.py --full           # + montagem com o braço Gen3 completo
"""

import argparse
import sys
from pathlib import Path

from build123d import export_step, export_stl

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "src"))

from kinova_cam.adapter import build_adapter  # noqa: E402
from kinova_cam.assembly import full_assembly, ring_assembly, ring_exploded, wrist_assembly  # noqa: E402
from kinova_cam.clamp_ring import build_ring  # noqa: E402
from kinova_cam.camera import d435i  # noqa: E402

ARM_STEP = ROOT / "vendor" / "GEN3_6DOF_NO-VISION_V01.STEP"
OUT = ROOT / "out"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true", help="inclui o braço Gen3 (vendor/)")
    ap.add_argument("--variant", choices=("spacer", "ring", "all"), default="all")
    args = ap.parse_args()
    variants = ("spacer", "ring") if args.variant == "all" else (args.variant,)
    if args.full and not ARM_STEP.exists():
        sys.exit(f"faltando {ARM_STEP}: rode scripts/fetch_vendor.sh")
    OUT.mkdir(exist_ok=True)
    export_step(d435i(), OUT / "d435i.step")

    if "spacer" in variants:
        adapter = build_adapter()
        export_step(adapter, OUT / "adapter.step")
        export_stl(adapter, OUT / "adapter.stl", tolerance=0.01, angular_tolerance=0.1)
        export_step(wrist_assembly(), OUT / "wrist_assembly.step")
        print(f"espaçador: volume {adapter.volume / 1000:.1f} cm³, válido={adapter.is_valid}")
        if args.full:
            export_step(full_assembly(ARM_STEP), OUT / "kinova_gen3_d435i.step")

    if "ring" in variants:
        for half in build_ring():
            name = "ring_camera_half" if "Camera" in half.label else "ring_lower_half"
            export_step(half, OUT / f"{name}.step")
            export_stl(half, OUT / f"{name}.stl", tolerance=0.01, angular_tolerance=0.1)
            print(f"{name}: volume {half.volume / 1000:.1f} cm³, válido={half.is_valid}")
        export_step(ring_assembly(), OUT / "wrist_ring_assembly.step")
        export_step(ring_exploded(), OUT / "wrist_ring_exploded.step")
        if args.full:
            export_step(full_assembly(ARM_STEP, "ring"), OUT / "kinova_gen3_d435i_ring.step")
    print(f"arquivos em {OUT}")


if __name__ == "__main__":
    main()
