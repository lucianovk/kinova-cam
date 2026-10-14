"""Simula o que a câmera RGB vê da garra, em cada versão do anel.

Projeta a malha da 2F-85 (aberta) no RGB da câmera (1280 x 720) com o modelo
pinhole, desenhando os triângulos do mais longe para o mais perto. Marca o
centro da imagem e a região entre os dedos. Rodar da raiz:

    .venv/bin/python scripts/camera_view.py   # -> out/images/[ring_rgb/]10_vista_rgb.png
"""

import math
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.collections import PolyCollection  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from build123d import Pos  # noqa: E402

from kinova_cam.clamp_ring import camera_pose  # noqa: E402
from kinova_cam.gripper import robotiq_2f85  # noqa: E402
from kinova_cam.params import PLACEMENTS  # noqa: E402

W, H = 1280, 720


def gripper_triangles() -> np.ndarray:
    g = robotiq_2f85()
    tris = []
    for ch in g.children:
        for s in (g.location * ch).solids():
            for f in s.faces():
                try:
                    v, t = f.tessellate(0.1, 0.2)
                except AttributeError:  # faces degeneradas do STEP da Robotiq
                    continue
                if t:
                    v = np.array([tuple(p) for p in v])
                    tris.append(v[np.array(t)])
    return np.concatenate(tris)


def rgb_frame(cp):
    """Origem e eixos ópticos (x direita, y baixo, z frente) do RGB no punho."""
    pose = camera_pose(cp)
    cam = cp.cam
    z0 = cam.depth - cam.zero_depth_to_front
    o = np.array(tuple((pose * Pos(cam.rgb_origin_x, 0, z0)).position))

    def axis(v):
        return np.array(tuple((pose * Pos(*v)).position)) - np.array(tuple(pose.position))

    # câmera: +X local = esquerda dela, +Y local = topo
    return o, -axis((1, 0, 0)), -axis((0, 1, 0)), axis((0, 0, 1))


def render(cp, tris, out: Path) -> None:
    o, ex, ey, ez = rgb_frame(cp)
    fx = (W / 2) / math.tan(math.radians(cp.cam.rgb_fov[0] / 2))
    fy = (H / 2) / math.tan(math.radians(cp.cam.rgb_fov[1] / 2))
    P = tris - o
    x, y, z = P @ ex, P @ ey, P @ ez
    ok = (z > 1).all(axis=1)
    u = fx * x[ok] / z[ok] + W / 2
    v = fy * y[ok] / z[ok] + H / 2
    zm = z[ok].mean(axis=1)
    # sombreamento simples pela normal em relação à direção de visada
    T = tris[ok]
    n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
    n /= np.linalg.norm(n, axis=1)[:, None] + 1e-12
    view = T.mean(axis=1) - o
    view /= np.linalg.norm(view, axis=1)[:, None]
    shade = 0.35 + 0.6 * np.abs(np.einsum("ij,ij->i", n, view))
    order = np.argsort(-zm)
    polys = np.stack([u, v], axis=2)[order]

    fig, ax = plt.subplots(figsize=(12.8, 7.2), dpi=100)
    ax.add_collection(PolyCollection(polys, facecolors=plt.cm.gray(shade[order] * 0.85), edgecolors="none"))
    ax.axvline(W / 2, color="#d62728", lw=1.5, ls="--")
    ax.axhline(H / 2, color="#d62728", lw=0.8, ls=":")
    # região entre os dedos (pontas a z 108–146, abertura ±42,5)
    box = np.array([(x0, 0, z0) for x0 in (-42.5, 42.5) for z0 in (108, 146)]) - o
    bu = fx * (box @ ex) / (box @ ez) + W / 2
    bv = fy * (box @ ey) / (box @ ez) + H / 2
    ax.plot(bu[[0, 1, 3, 2, 0]], bv[[0, 1, 3, 2, 0]], color="#1f77b4", lw=1.5)
    # eixo da ferramenta projetado (de 100 mm a 2 m à frente da flange)
    pts = np.array([(0, 0, d) for d in np.linspace(100, 2000, 50)]) - o
    ax.plot(fx * (pts @ ex) / (pts @ ez) + W / 2, fy * (pts @ ey) / (pts @ ez) + H / 2,
            color="#2ca02c", lw=1.2)
    centro = np.array([0, 0, 127.0]) - o
    du = fx * (centro @ ex) / (centro @ ez)
    zd = centro @ ez
    ax.set_title(f"{cp.name}: vista simulada do RGB da {cp.cam.name} ({cp.cam.rgb_fov[0]:.0f}° x {cp.cam.rgb_fov[1]:.0f}°)   centro entre os dedos a {du:+.0f} px do "
                 f"centro horizontal, {zd:.0f} mm à frente", fontsize=12)
    ax.text(10, 25, "tracejado vermelho: centro da imagem · azul: região entre os dedos · "
            "verde: eixo da ferramenta (0,1–2 m)", fontsize=9, color="#333")
    ax.set_xlim(0, W)
    ax.set_ylim(H, 0)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    fig.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out)
    plt.close(fig)
    print(f"{out.relative_to(ROOT)}: centro entre os dedos {du:+.1f} px, Z {zd:.0f} mm")


def main() -> None:
    tris = gripper_triangles()
    for name, cp in PLACEMENTS.items():
        sub = "" if name == "ring" else name
        render(cp, tris, ROOT / "out" / "images" / sub / "10_vista_rgb.png")


if __name__ == "__main__":
    main()
