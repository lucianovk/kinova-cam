"""Mostra o modelo no OCP CAD Viewer (VS Code).

Abra o viewer (ícone OCP na barra lateral ou Ctrl+K V) e rode este arquivo:

    .venv/bin/python view.py          # espaçador + câmera + garra
    .venv/bin/python view.py --ring   # anel bipartido + câmera + garra
    .venv/bin/python view.py --arm    # + punho do Gen3 6DOF (combina com --ring)
"""

import argparse
import sys
from pathlib import Path

from build123d import import_step
from ocp_vscode import Camera, set_defaults, show

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "src"))

from kinova_cam import clamp_ring  # noqa: E402
from kinova_cam.adapter import build_adapter, camera_pose  # noqa: E402
from kinova_cam.assembly import tool_frame  # noqa: E402
from kinova_cam.camera import camera_fov, d435i  # noqa: E402
from kinova_cam.gripper import GRIPPER_STEP, robotiq_2f85  # noqa: E402

ARM_STEP = ROOT / "vendor" / "GEN3_6DOF_NO-VISION_V01.STEP"
WRIST_LINKS = ("GEN3_SIMPLIFIED_Spherical_Wrist2", "GEN3_SIMPLIFIED_No-Vision")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", action="store_true", help="mostra o punho do Gen3")
    ap.add_argument("--ring", action="store_true", help="versão anel bipartido")
    args = ap.parse_args()

    if args.ring:
        cam_half, low_half = clamp_ring.build_ring()
        cam = clamp_ring.camera_pose() * d435i()
        objs = [cam_half, low_half, clamp_ring.build_fasteners(), cam]
        names = ["anel (câmera)", "anel (baixo)", "M4", "D435i"]
        colors = ["orange", "orange", "#202020", "#303035"]
        alphas = [1.0] * 4
    else:
        cam = camera_pose() * d435i()
        objs, names, colors, alphas = [build_adapter(), cam], ["adaptador", "D435i"], ["orange", "#303035"], [1.0, 1.0]
    pose = clamp_ring.camera_pose() if args.ring else camera_pose()
    for cone in camera_fov().children:
        objs.append(pose * cone)
        names.append(cone.label)
        colors.append("#3080ff" if "depth" in cone.label else "#30d050")
        alphas.append(0.2)
    if GRIPPER_STEP.exists():
        objs.append(robotiq_2f85(seat_z=0.0) if args.ring else robotiq_2f85())
        names.append("2F-85")
        colors.append("#6a6a70")
        alphas.append(1.0)

    if args.arm:
        arm = import_step(ARM_STEP)
        frame = tool_frame(arm)
        to_local = frame.inverse()  # punho no referencial do adaptador
        for link in arm.children:
            if link.label in WRIST_LINKS:
                objs.append(to_local * link)
                names.append(link.label)
                colors.append("#b0b4bc")
                alphas.append(0.35)

    set_defaults(reset_camera=Camera.KEEP)
    show(*objs, names=names, colors=colors, alphas=alphas)


if __name__ == "__main__":
    main()
