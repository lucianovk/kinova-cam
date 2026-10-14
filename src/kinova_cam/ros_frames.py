"""Referenciais para o ROS (ros2_kortex + realsense-ros), em metros.

- end_effector_link (ros2_kortex): no eixo da junta 6, KINOVA.ee_link_behind_face
  atrás da face do aro Ø75; Z sai da ferramenta, +Y no lado do módulo de
  visão da Kinova (oposto ao deslocamento dos botões de admitância).
- mount: o referencial do modelo (centro da face do aro Ø75), com os mesmos
  eixos do end_effector_link quando a câmera é montada em +Y_ee.
- camera_link (realsense-ros): imageador esquerdo, no plano de profundidade
  zero; x frente, y esquerda, z cima.
"""

from dataclasses import dataclass

import numpy as np
from build123d import Location, Pos
from scipy.spatial.transform import Rotation

from .clamp_ring import camera_pose
from .params import KINOVA, CamPlacement

# eixos do camera_link (x frente, y esquerda, z cima) no referencial da câmera
# do modelo (+Z eixo óptico, +X esquerda, +Y topo)
_LINK_AXES = np.column_stack([[0, 0, 1], [1, 0, 0], [0, 1, 0]])


@dataclass(frozen=True)
class Transform:
    xyz: tuple[float, float, float]  # m
    rpy: tuple[float, float, float]  # rad (ROS: x, y, z fixos)
    quat: tuple[float, float, float, float]  # x, y, z, w


def _to_transform(R: np.ndarray, t_mm: np.ndarray) -> Transform:
    r = Rotation.from_matrix(R)
    clean = lambda v, n: tuple(float(round(x, n)) + 0.0 for x in v)  # noqa: E731
    return Transform(clean(t_mm / 1000, 6), clean(r.as_euler("xyz"), 6), clean(r.as_quat(), 6))


def _matrix(loc: Location) -> np.ndarray:
    tr = loc.wrapped.Transformation()
    return np.array([[tr.Value(i, j) for j in range(1, 5)] for i in range(1, 4)])


def mount_in_ee() -> Transform:
    """Referencial do modelo (face do aro Ø75) no end_effector_link."""
    return _to_transform(np.eye(3), np.array([0.0, 0.0, KINOVA.ee_link_behind_face]))


def camera_link_in_mount(cp: CamPlacement) -> tuple[np.ndarray, np.ndarray]:
    """(rotação, posição em mm) do camera_link no referencial do modelo."""
    cam = cp.cam
    pose = camera_pose(cp)
    M = _matrix(pose)
    p = np.array(tuple((pose * Pos(cam.depth_origin_x, 0, cam.depth - cam.zero_depth_to_front)).position))
    return M[:, :3] @ _LINK_AXES, p


def camera_link_in_ee(cp: CamPlacement) -> Transform:
    R, p = camera_link_in_mount(cp)
    return _to_transform(R, p + np.array([0.0, 0.0, KINOVA.ee_link_behind_face]))


def camera_link_in_mount_tf(cp: CamPlacement) -> Transform:
    R, p = camera_link_in_mount(cp)
    return _to_transform(R, p)


def bottom_screw_in_mount(cp: CamPlacement) -> Transform:
    """<name>_bottom_screw_frame (origem do xacro da realsense2_description)."""
    R, p = camera_link_in_mount(cp)
    offset = np.array(cp.cam.link_from_screw) * 1000
    return _to_transform(R, p - R @ offset)
