"""Simula a imagem de profundidade com a garra 2F-85 totalmente aberta.

Mesmo enquadramento de camera_view.py, mas no imageador esquerdo (origem da
profundidade da RealSense), com o campo de visão e a resolução de
profundidade de cada câmera. Os dedos são coloridos conforme haja ou não
profundidade. Um ponto tem profundidade se:

1. aparece na imagem do imageador esquerdo (campo de visão, sem obstrução);
2. também é visto pelo imageador direito (campo de visão, sem obstrução). Isso
   inclui a faixa sem profundidade da borda esquerda da imagem: um ponto a Z
   tem disparidade fx·B/Z px e precisa caber na imagem do imageador direito;
3. está além da distância mínima (Z_min) da resolução usada.

Rodar da raiz (~1 min por versão):

    .venv/bin/python scripts/depth_view.py [versão ...]
    # -> out/images/[<versão>/]11_vista_profundidade.png
"""

import math
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.collections import PolyCollection  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from build123d import Pos  # noqa: E402

from kinova_cam.clamp_ring import camera_pose  # noqa: E402
from kinova_cam.gripper import robotiq_2f85  # noqa: E402
from kinova_cam.params import PLACEMENTS  # noqa: E402

# resolução de profundidade recomendada e Z mínimo publicado pela Intel (mais
# conservador que o teórico fx·B/126) para cada câmera
DEPTH_MODE = {"D435i": ((424, 240), 105.0), "D405": ((1280, 720), 100.0)}
OK_CMAP = plt.cm.viridis
NO_MATCH = (0.85, 0.25, 0.25, 1.0)  # sem par no imageador direito
TOO_CLOSE = (0.95, 0.6, 0.2, 1.0)  # mais perto que Z mín


def gripper_mesh():
    """Triângulos da garra, o lado (+X/-X) e o tipo de peça de cada um."""
    g = robotiq_2f85()
    tris, side, kind = [], [], []
    for ch in g.children:
        k = "base" if "base" in ch.label else "ponta" if "fingertips" in ch.label else "haste"
        for s in (g.location * ch).solids():
            for f in s.faces():
                try:
                    v, t = f.tessellate(0.3, 0.5)
                except AttributeError:  # faces degeneradas do STEP da Robotiq
                    continue
                if not t:
                    continue
                tri = np.array([tuple(p) for p in v])[np.array(t)]
                tris.append(tri)
                side += ["+X" if tri[:, :, 0].mean() > 0 else "-X"] * len(tri)
                kind += [k] * len(tri)
    return np.concatenate(tris), np.array(side), np.array(kind)


def blocked(o, P, T, skip):
    """Para cada ponto P, se o segmento o->P cruza algum triângulo de T
    (Möller–Trumbore), ignorando o próprio triângulo (índice skip)."""
    A, E1, E2 = T[:, 0], T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]
    out = np.zeros(len(P), bool)
    for k, p in enumerate(P):
        d = p - o
        L = np.linalg.norm(d)
        d /= L
        h = np.cross(d, E2)
        a = np.einsum("ij,ij->i", E1, h)
        ok = np.abs(a) > 1e-12
        f = np.where(ok, 1 / np.where(ok, a, 1), 0)
        s = o - A
        u = f * np.einsum("ij,ij->i", s, h)
        q = np.cross(s, E1)
        v = f * (q @ d)
        t = f * np.einsum("ij,ij->i", E2, q)
        hit = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 0.3) & (t < L - 0.3)
        hit[skip[k]] = False
        out[k] = hit.any()
    return out


def analyse(cp, T, side, kind, out: Path) -> list[str]:
    cam = cp.cam
    (W, H), zmin = DEPTH_MODE[cam.name]
    pose = camera_pose(cp)
    z0 = cam.depth - cam.zero_depth_to_front

    def at(x, y=0.0, z=z0):
        return np.array(tuple((pose * Pos(x, y, z)).position))

    left, right = at(cam.depth_origin_x), at(cam.depth_origin_x - cam.baseline)
    o = np.array(tuple(pose.position))
    ex = -(at(1, 0, 0) - o)  # x da imagem: direita da câmera
    ey = -(at(0, 1, 0) - o)  # y da imagem: para baixo
    ez = at(0, 0, 1) - o
    fx = (W / 2) / math.tan(math.radians(cam.depth_fov[0] / 2))
    fy = (H / 2) / math.tan(math.radians(cam.depth_fov[1] / 2))

    def project(org, P):
        d = P - org
        z = d @ ez
        return fx * (d @ ex) / z + W / 2, fy * (d @ ey) / z + H / 2, z

    C = T.mean(axis=1)
    n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
    area = np.linalg.norm(n, axis=1) / 2
    uL, vL, zL = project(left, C)
    uR, vR, zR = project(right, C)
    inL = (zL > 1) & (uL >= 0) & (uL < W) & (vL >= 0) & (vL < H)
    inR = (zR > 1) & (uR >= 0) & (uR < W) & (vR >= 0) & (vR < H)
    finger = kind != "base"
    facing = np.einsum("ij,ij->i", n, left - C) > 0
    cand = np.where(inL & facing & finger)[0]
    seenL = np.zeros(len(T), bool)
    seenL[cand] = ~blocked(left, C[cand], T, cand)
    cand_r = np.where(seenL & inR)[0]
    seenR = np.zeros(len(T), bool)
    seenR[cand_r] = ~blocked(right, C[cand_r], T, cand_r)
    far = zL >= zmin
    valid = seenL & seenR & far

    # estatística: fração da área visível (no esquerdo) com profundidade
    lines = []
    for s in ("+X", "-X"):
        parts = []
        for k, label in (("ponta", "ponta"), (None, "dedo inteiro")):
            m = finger & (side == s) & seenL & ((kind == k) if k else True)
            a = area[m].sum()
            if a == 0:
                parts.append(f"{label}: fora da imagem")
                continue
            parts.append(f"{label} {area[m & valid].sum() / a:.0%}")
            if k:
                zv = zL[m & valid]
                parts[-1] += f" (Z {zv.min():.0f}–{zv.max():.0f} mm)" if len(zv) else ""
        lines.append(f"dedo {s}: " + ", ".join(parts))

    # desenho no imageador esquerdo, do mais longe para o mais perto
    P = T - left
    Z = P @ ez
    ok = (Z > 1).all(axis=1)
    u = fx * (P @ ex)[ok] / Z[ok] + W / 2
    v = fy * (P @ ey)[ok] / Z[ok] + H / 2
    order = np.argsort(-Z[ok].mean(axis=1))
    view = C[ok] - left
    view /= np.linalg.norm(view, axis=1)[:, None]
    nn = n[ok] / (np.linalg.norm(n[ok], axis=1)[:, None] + 1e-12)
    shade = 0.35 + 0.6 * np.abs(np.einsum("ij,ij->i", nn, view))
    colors = plt.cm.gray(shade * 0.85)
    f_ok = finger[ok]
    colors[f_ok & valid[ok]] = OK_CMAP(np.clip((zL[ok][f_ok & valid[ok]] - zmin) / 60, 0, 1))
    colors[f_ok & ~valid[ok] & ~far[ok]] = TOO_CLOSE
    colors[f_ok & ~valid[ok] & far[ok]] = NO_MATCH

    fig, ax = plt.subplots(figsize=(12.8, 7.2), dpi=100)
    ax.add_collection(PolyCollection(np.stack([u, v], axis=2)[order], facecolors=colors[order], edgecolors="none"))
    # faixa sem profundidade na borda esquerda, para o Z do centro entre os dedos
    zc = (np.array([0, 0, 127.0]) - left) @ ez
    band = fx * cam.baseline / zc
    ax.add_patch(Rectangle((0, 0), band, H, fc="none", ec="#d62728", hatch="//", lw=0, alpha=0.5))
    ax.text(band + 3, H * 0.97, f"faixa sem profundidade a Z {zc:.0f} mm ({band:.0f} px)",
            color="#d62728", fontsize=9, va="bottom")
    ax.axvline(W / 2, color="#d62728", lw=1.5, ls="--")
    ax.axhline(H / 2, color="#d62728", lw=0.8, ls=":")
    box = np.array([(x0, 0, z) for x0 in (-42.5, 42.5) for z in (108, 146)], float)
    bu, bv, _ = project(left, box)
    ax.plot(bu[[0, 1, 3, 2, 0]], bv[[0, 1, 3, 2, 0]], color="#1f77b4", lw=1.5)
    axis_pts = np.array([(0, 0, d) for d in np.linspace(100, 2000, 50)])
    au, av, _ = project(left, axis_pts)
    ax.plot(au, av, color="#2ca02c", lw=1.2)
    ax.set_xlim(0, W)
    ax.set_ylim(H, 0)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title(f"{cp.name}: vista simulada da profundidade da {cam.name} ({cam.depth_fov[0]:.0f}° x "
                 f"{cam.depth_fov[1]:.0f}°, {W}x{H}, Z mín {zmin:.0f} mm), garra aberta", fontsize=12)
    ax.text(W * 0.01, H * 0.03, "\n".join(lines) + "\n(fração da área de cada dedo visível na imagem)", fontsize=9,
            va="top", bbox=dict(fc="white", ec="#999", alpha=0.85))
    ax.text(W * 0.99, H * 0.03, "dedos: cor = Z (amarelo = mais longe)\nvermelho: sem par no imageador direito\n"
            "laranja: mais perto que Z mín\ntracejado: centro · azul: entre os dedos\nverde: eixo da ferramenta",
            fontsize=8, va="top", ha="right", bbox=dict(fc="white", ec="#999", alpha=0.85))
    fig.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out)
    plt.close(fig)
    print(f"{out.relative_to(ROOT)}: " + " | ".join(lines), flush=True)
    return lines


def main() -> None:
    T, side, kind = gripper_mesh()
    for name in sys.argv[1:] or list(PLACEMENTS):
        sub = "" if name == "ring" else name
        analyse(PLACEMENTS[name], T, side, kind, ROOT / "out" / "images" / sub / "11_vista_profundidade.png")


if __name__ == "__main__":
    main()
