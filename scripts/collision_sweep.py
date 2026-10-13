"""Varredura de colisão da versão anel: j6 (vs Wrist2) e j5 x j6 (vs antebraço
e Wrist1), por nuvem de pontos (~1 mm). Rodar da raiz: .venv/bin/python
scripts/collision_sweep.py (~1 min). Também mostra onde o contato começaria
além do limite da j5, como checagem de sensibilidade."""
import sys, time
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, "src")
from build123d import import_step, Rot, Location
from kinova_cam.assembly import ring_assembly, tool_frame
t0 = time.time()
rng = np.random.default_rng(0)
SP = 0.5  # espaçamento da amostragem (mm)
VOX = 1.0  # depois reduz para 1 ponto por voxel de 1 mm

def cloud(shapes):
    pts = []
    for s in shapes:
        v, t = s.tessellate(0.05, 0.1)
        V = np.array([[p.X, p.Y, p.Z] for p in v]); T = np.array(t)
        A, B, C = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
        area = np.linalg.norm(np.cross(B - A, C - A), axis=1) / 2
        n = np.ceil(area / SP**2 * 2).astype(int)
        idx = np.repeat(np.arange(len(T)), n)
        r1, r2 = rng.random(len(idx)), rng.random(len(idx))
        flip = r1 + r2 > 1; r1[flip], r2[flip] = 1 - r1[flip], 1 - r2[flip]
        pts.append(A[idx] + r1[:, None] * (B - A)[idx] + r2[:, None] * (C - A)[idx])
        pts.append(V)
    X = np.vstack(pts)
    _, keep = np.unique(np.floor(X / VOX).astype(np.int64), axis=0, return_index=True)
    return X[keep]

def mat(loc):
    tr = loc.wrapped.Transformation()
    M = np.array([[tr.Value(i, j) for j in range(1, 5)] for i in range(1, 4)])
    return M[:, :3], M[:, 3]

arm = import_step("vendor/GEN3_6DOF_NO-VISION_V01.STEP")
frame = tool_frame(arm)
wa = ring_assembly()
ours_s = [s for ch in wa.children if not ("Robotiq" in ch.label or "FOV" in ch.label) for s in ch.solids()]
P = cloud(ours_s)
L = {l.label: l for l in arm.children}
W2 = cloud(L["GEN3_SIMPLIFIED_Spherical_Wrist2"].solids())
MOD = cloud(L["GEN3_SIMPLIFIED_No-Vision"].solids())
j5c = np.array([0, 0, 1009.2])
# alcance do que gira na j5: pontos nossos (no braço) a até R do eixo da j5
R0, t0v = mat(frame)
Pw = P @ R0.T + t0v
R = np.max(np.linalg.norm((Pw - j5c)[:, [0, 2]], axis=1)) + 15
static = []
for l in arm.children:
    if l.label in ("GEN3_SIMPLIFIED_Spherical_Wrist2", "GEN3_SIMPLIFIED_No-Vision"): continue
    bb = l.bounding_box()
    if bb.max.Z < j5c[2] - R: continue
    c = cloud(l.solids())
    c = c[np.linalg.norm((c - j5c)[:, [0, 2]], axis=1) < R]
    if len(c): static.append((l.label, c))
names = np.concatenate([[n] * len(c) for n, c in static]); S = np.vstack([c for _, c in static])
tree = cKDTree(S); tw2 = cKDTree(W2)
print(f"pontos: nossos {len(P)}, braço {len(S)} ({sorted(set(names))}), R={R:.0f} mm [{time.time()-t0:.0f}s]", flush=True)

def pose(q5, q6):
    return Location(tuple(j5c)) * Rot(0, q5, 0) * Location(tuple(-j5c)) * frame * Rot(0, 0, q6)

def dist(cloudpts, loc, tr, nm=None):
    Rm, tv = mat(loc)
    d, i = tr.query(cloudpts @ Rm.T + tv, distance_upper_bound=20)
    k = int(np.argmin(d))
    return d[k], (nm[i[k]] if nm is not None and np.isfinite(d[k]) else None)

# sensibilidade: o próprio módulo de interface (sem o anel) também deve bater além do limite
w = min((dist(P, frame * Rot(0, 0, q6), tw2)[0], q6) for q6 in range(0, 360, 10))
print(f"j6 (passo 10°) vs Wrist2: folga mínima {w[0]:.1f} mm em q6={w[1]}", flush=True)
LIM = 120.3
angles = list(np.arange(0, LIM, 2.5)) + [LIM]
beyond = list(np.arange(LIM + 2.5, 181, 2.5))
def first_contact(cl, q6, sgn, nm=None):
    for a in beyond:
        d, who = dist(cl, pose(sgn * a, q6), tree, nm)
        if d < 1.0: return (round(sgn * a, 1), who)
    return None
Rf, tf = mat(frame); MODl = (MOD - tf) @ Rf
for sgn in (1, -1):
    print(f"sensibilidade: módulo sem anel, j5 {'+' if sgn>0 else '-'}: folga no limite {dist(MODl, pose(sgn*LIM, 0), tree, names)}, primeiro contato {first_contact(MODl, 0, sgn, names)}", flush=True)
glob = (1e9, None)
for q6 in range(0, 360, 30):
    row = []
    for sgn in (1, -1):
        best = min((dist(P, pose(sgn * a, q6), tree, names) + (sgn * a,) for a in angles), key=lambda x: x[0])
        if best[0] < glob[0]: glob = (best[0], (q6,) + best[1:])
        row.append(f"{best[0]:5.1f} mm em {best[2]:6.1f}° ({best[1]}); contato além: {first_contact(P, q6, sgn, names)}")
    print(f"q6={q6:3d} | + {row[0]} | - {row[1]} [{time.time()-t0:.0f}s]", flush=True)
print("folga mínima global dentro dos limites:", glob, flush=True)
