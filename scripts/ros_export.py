"""Gera o pacote ROS 2 ros/kinova_cam_description a partir do modelo.

Para cada versão do anel (params.PLACEMENTS): transformação
end_effector_link -> camera_link, malhas (metades do anel e câmera), xacro
com a montagem e URDF expandido. Rodar da raiz depois de mudar a geometria:

    .venv/bin/python scripts/ros_export.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from build123d import Compound, export_stl  # noqa: E402

from kinova_cam.camera import camera_body  # noqa: E402
from kinova_cam.clamp_ring import build_ring, camera_pose  # noqa: E402
from kinova_cam.params import KINOVA, PLACEMENTS  # noqa: E402
from kinova_cam.ros_frames import (  # noqa: E402
    bottom_screw_in_mount,
    camera_link_in_ee,
    camera_link_in_mount_tf,
)

PKG = "kinova_cam_description"
OUT = ROOT / "ros" / PKG
DESC = {
    "ring": "D435i centrada no punho, 15° (versão original)",
    "ring_rgb": "D435i com a lente RGB no eixo da garra, 20°",
    "ring_stereo": "D435i com o meio da linha de base no eixo da garra, 20°",
    "ring_d405": "D405 com o imageador esquerdo (cor e profundidade) no eixo da garra, 15°",
}
DEPTH = {"D435i": "424x240 (Z mín ~105 mm)", "D405": "1280x720 (Z mín ~100 mm)"}
RS_MACRO = {"D435i": ("_d435i.urdf.xacro", "sensor_d435i"), "D405": ("_d405.urdf.xacro", "sensor_d405")}
PLA_DENSITY = 1.24e-3  # g/mm³; peça impressa com ~50 % de preenchimento: fator 0,75
PRINT_FILL = 0.75


def f(v) -> str:
    return " ".join(f"{x:.6g}" for x in v)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    print(path.relative_to(ROOT))


def export_meshes() -> dict:
    """STL em mm, no referencial do modelo (centro da face do aro Ø75)."""
    (OUT / "meshes").mkdir(parents=True, exist_ok=True)
    info = {}
    lower = None
    for name, cp in PLACEMENTS.items():
        cam_half, low_half = build_ring(cp)
        lower = low_half
        export_stl(cam_half, OUT / "meshes" / f"{name}_camera_half.stl", tolerance=0.05, angular_tolerance=0.2)
        body = camera_pose(cp) * camera_body(cp.cam)
        solids = [s for c in body.children for s in (body.location * c).solids()]
        export_stl(Compound(solids), OUT / "meshes" / f"{name}_camera.stl", tolerance=0.2, angular_tolerance=0.5)
        parts = [cam_half, low_half]
        vol = sum(p.volume for p in parts)
        com = sum((p.center() * p.volume for p in parts[1:]), parts[0].center() * parts[0].volume) / vol
        info[name] = (vol * PLA_DENSITY * PRINT_FILL, com)
    export_stl(lower, OUT / "meshes" / "ring_lower_half.stl", tolerance=0.05, angular_tolerance=0.2)
    return info


def yaml_text(mass: dict) -> str:
    lines = [
        "# Gerado por scripts/ros_export.py (kinova-cam). Valores do CAD, sem calibração.",
        "# end_effector_link: ros2_kortex (Gen3 6DOF), no eixo da junta 6, "
        f"{KINOVA.ee_link_behind_face} mm atrás da face do aro Ø75.",
        "# camera_link: realsense-ros, imageador esquerdo no plano de profundidade zero",
        "# (x frente, y esquerda, z cima). rpy em rad (eixos fixos x, y, z); quat x y z w.",
        "# Montagem: câmera do lado +Y do end_effector_link (oposto ao deslocamento dos",
        "# botões de admitância), orelhas do anel alinhadas com os botões, câmera de pé.",
        "",
    ]
    for name, cp in PLACEMENTS.items():
        t = camera_link_in_ee(cp)
        m, com = mass[name]
        com_ee = (com.X / 1000, com.Y / 1000, (com.Z + KINOVA.ee_link_behind_face) / 1000)
        lines += [
            f"{name}:",
            f"  description: \"{DESC[name]}\"",
            f"  camera: {cp.cam.name}",
            f"  parent_frame: end_effector_link",
            f"  child_frame: camera_link",
            f"  xyz: [{', '.join(f'{x:.6g}' for x in t.xyz)}]",
            f"  rpy: [{', '.join(f'{x:.6g}' for x in t.rpy)}]",
            f"  quat_xyzw: [{', '.join(f'{x:.6g}' for x in t.quat)}]",
            f"  depth_profile: \"{DEPTH[cp.cam.name]}\"",
            f"  mount_mass_kg_pla: {m / 1000:.3f}  # anel impresso (estimativa, sem câmera nem parafusos)",
            f"  mount_com_in_ee_m: [{', '.join(f'{round(x, 4) + 0.0:.4f}' for x in com_ee)}]",
            "",
        ]
    return "\n".join(lines)


def xacro_text() -> str:
    m = (0, 0, KINOVA.ee_link_behind_face / 1000)
    blocks = []
    for name, cp in PLACEMENTS.items():
        link = camera_link_in_mount_tf(cp)
        blocks.append(f"""
    <!-- {name}: {DESC[name]} -->
    <xacro:if value="${{version == '{name}'}}">
      <link name="${{prefix}}camera_mount_link">
        <xacro:kinova_cam_mount_geometry part="{name}_camera_half"/>
        <xacro:kinova_cam_mount_geometry part="ring_lower_half"/>
        <xacro:if value="${{camera_mesh}}">
          <xacro:kinova_cam_mount_geometry part="{name}_camera" rgba="0.15 0.15 0.17 1"/>
        </xacro:if>
      </link>
      <xacro:if value="${{camera_link}}">
        <joint name="${{camera_name}}_joint" type="fixed">
          <parent link="${{prefix}}camera_mount_link"/>
          <child link="${{camera_name}}_link"/>
          <origin xyz="{f(link.xyz)}" rpy="{f(link.rpy)}"/>
        </joint>
        <link name="${{camera_name}}_link"/>
      </xacro:if>
    </xacro:if>""")
    return f"""<?xml version="1.0"?>
<!-- Gerado por scripts/ros_export.py (kinova-cam). Não editar à mão.

  Anel bipartido da câmera no punho do Kinova Gen3 6DOF (ros2_kortex).

  Uso (no xacro do robô, depois do braço):
    <xacro:include filename="$(find {PKG})/urdf/kinova_cam_mount.urdf.xacro"/>
    <xacro:kinova_cam_mount parent="end_effector_link" version="ring_rgb"/>

  Parâmetros:
    parent       link do punho (end_effector_link do ros2_kortex)
    version      {' | '.join(PLACEMENTS)}
    prefix       prefixo do link da montagem (ex.: o do ros2_kortex)
    camera_name  prefixo dos frames da RealSense (padrão "camera" -> camera_link)
    camera_link  true: cria <camera_name>_link (o driver da RealSense publica o
                 resto da árvore com publish_tf:=true). Use false quando a
                 câmera vier do xacro oficial (kinova_cam_mount_realsense)
    camera_mesh  true: malha da câmera para visualização e colisão (MoveIt).
                 As malhas da câmera (CAD da Intel) não são versionadas: gere com
                 scripts/ros_export.py, com os STEP oficiais em vendor/
-->
<robot xmlns:xacro="http://www.ros.org/wiki/xacro">

  <xacro:macro name="kinova_cam_mount_geometry" params="part rgba:='0.85 0.45 0.1 1'">
    <visual>
      <geometry><mesh filename="package://{PKG}/meshes/${{part}}.stl" scale="0.001 0.001 0.001"/></geometry>
      <material name="kinova_cam_${{part}}"><color rgba="${{rgba}}"/></material>
    </visual>
    <collision>
      <geometry><mesh filename="package://{PKG}/meshes/${{part}}.stl" scale="0.001 0.001 0.001"/></geometry>
    </collision>
  </xacro:macro>

  <xacro:macro name="kinova_cam_mount"
      params="parent:=end_effector_link version:=ring_rgb prefix:='' camera_name:=camera camera_link:=true camera_mesh:=false">
    <!-- referencial da montagem: centro da face do aro Ø75 (mesmos eixos do end_effector_link) -->
    <joint name="${{prefix}}camera_mount_joint" type="fixed">
      <parent link="${{parent}}"/>
      <child link="${{prefix}}camera_mount_link"/>
      <origin xyz="{f(m)}" rpy="0 0 0"/>
    </joint>
{''.join(blocks)}
  </xacro:macro>
</robot>
"""


def xacro_rs_text() -> str:
    blocks = []
    for name, cp in PLACEMENTS.items():
        screw = bottom_screw_in_mount(cp)
        _, macro = RS_MACRO[cp.cam.name]
        blocks.append(f"""
    <xacro:if value="${{version == '{name}'}}">
      <xacro:{macro} parent="${{prefix}}camera_mount_link" name="${{camera_name}}"
          use_nominal_extrinsics="${{use_nominal_extrinsics}}">
        <origin xyz="{f(screw.xyz)}" rpy="{f(screw.rpy)}"/>
      </xacro:{macro}>
    </xacro:if>""")
    includes = "\n".join(
        f'  <xacro:include filename="$(find realsense2_description)/urdf/{fn}"/>' for fn, _ in RS_MACRO.values()
    )
    return f"""<?xml version="1.0"?>
<!-- Gerado por scripts/ros_export.py (kinova-cam). Não editar à mão.

  Como kinova_cam_mount, mas com a câmera do xacro oficial
  (realsense2_description): todos os frames da câmera vêm do URDF. Lance o
  driver com publish_tf:=false para não haver dois publicadores dos mesmos
  frames, ou use use_nominal_extrinsics:=true só em simulação.

    <xacro:include filename="$(find {PKG})/urdf/kinova_cam_mount_realsense.urdf.xacro"/>
    <xacro:kinova_cam_mount_realsense parent="end_effector_link" version="ring_rgb"/>
-->
<robot xmlns:xacro="http://www.ros.org/wiki/xacro">
  <xacro:include filename="$(find {PKG})/urdf/kinova_cam_mount.urdf.xacro"/>
{includes}

  <xacro:macro name="kinova_cam_mount_realsense"
      params="parent:=end_effector_link version:=ring_rgb prefix:='' camera_name:=camera use_nominal_extrinsics:=false">
    <xacro:kinova_cam_mount parent="${{parent}}" version="${{version}}" prefix="${{prefix}}"
        camera_name="${{camera_name}}" camera_link="false" camera_mesh="false"/>
    <!-- origem: <camera_name>_bottom_screw_frame (rosca 1/4-20) no referencial da montagem -->
{''.join(blocks)}
  </xacro:macro>
</robot>
"""


def urdf_text(name: str) -> str:
    cp = PLACEMENTS[name]
    link = camera_link_in_mount_tf(cp)
    m = (0, 0, KINOVA.ee_link_behind_face / 1000)
    geo = lambda part, rgba: f"""
    <visual>
      <geometry><mesh filename="package://{PKG}/meshes/{part}.stl" scale="0.001 0.001 0.001"/></geometry>
      <material name="{part}"><color rgba="{rgba}"/></material>
    </visual>
    <collision>
      <geometry><mesh filename="package://{PKG}/meshes/{part}.stl" scale="0.001 0.001 0.001"/></geometry>
    </collision>"""  # noqa: E731
    return f"""<?xml version="1.0"?>
<!-- Gerado por scripts/ros_export.py (kinova-cam): {name} — {DESC[name]}.
     URDF isolado (raiz end_effector_link), para conferir com check_urdf / RViz. -->
<robot name="kinova_cam_{name}">
  <link name="end_effector_link"/>
  <joint name="camera_mount_joint" type="fixed">
    <parent link="end_effector_link"/>
    <child link="camera_mount_link"/>
    <origin xyz="{f(m)}" rpy="0 0 0"/>
  </joint>
  <link name="camera_mount_link">{geo(f"{name}_camera_half", "0.85 0.45 0.1 1")}{geo("ring_lower_half", "0.85 0.45 0.1 1")}
  </link>
  <joint name="camera_joint" type="fixed">
    <parent link="camera_mount_link"/>
    <child link="camera_link"/>
    <origin xyz="{f(link.xyz)}" rpy="{f(link.rpy)}"/>
  </joint>
  <link name="camera_link"/>
</robot>
"""


LAUNCH = f'''"""TF estático end_effector_link -> camera_link para uma versão do anel.

    ros2 launch {PKG} static_tf.launch.py version:=ring_rgb

Gerado por scripts/ros_export.py (kinova-cam); valores em config/camera_mounts.yaml.
"""

import os

import yaml
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def _publisher(context):
    share = get_package_share_directory("{PKG}")
    with open(os.path.join(share, "config", "camera_mounts.yaml")) as f:
        mounts = yaml.safe_load(f)
    version = LaunchConfiguration("version").perform(context)
    m = mounts[version]
    x, y, z = (str(v) for v in m["xyz"])
    qx, qy, qz, qw = (str(v) for v in m["quat_xyzw"])
    return [
        Node(
            package="tf2_ros",
            executable="static_transform_publisher",
            name="kinova_cam_static_tf",
            arguments=["--x", x, "--y", y, "--z", z, "--qx", qx, "--qy", qy, "--qz", qz, "--qw", qw,
                       "--frame-id", LaunchConfiguration("parent").perform(context),
                       "--child-frame-id", LaunchConfiguration("child").perform(context)],
        )
    ]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument("version", default_value="ring_rgb", description="{' | '.join(PLACEMENTS)}"),
        DeclareLaunchArgument("parent", default_value="end_effector_link"),
        DeclareLaunchArgument("child", default_value="camera_link"),
        OpaqueFunction(function=_publisher),
    ])
'''

PACKAGE_XML = f"""<?xml version="1.0"?>
<?xml-model href="http://download.ros.org/schema/package_format3.xsd" schematypens="http://www.w3.org/2001/XMLSchema"?>
<package format="3">
  <name>{PKG}</name>
  <version>0.1.0</version>
  <description>Anel da câmera RealSense (D435i/D405) no punho do Kinova Gen3 6DOF: URDF/xacro, malhas e TF.</description>
  <maintainer email="luciano.vieira@embrapa.br">Luciano Vieira Koenigkan</maintainer>
  <license>TODO</license>

  <buildtool_depend>ament_cmake</buildtool_depend>
  <exec_depend>xacro</exec_depend>
  <exec_depend>tf2_ros</exec_depend>
  <exec_depend>launch_ros</exec_depend>
  <exec_depend>python3-yaml</exec_depend>
  <!-- kinova_cam_mount_realsense.urdf.xacro também precisa de realsense2_description -->

  <export>
    <build_type>ament_cmake</build_type>
  </export>
</package>
"""

CMAKE = f"""cmake_minimum_required(VERSION 3.8)
project({PKG})
find_package(ament_cmake REQUIRED)
install(DIRECTORY config launch meshes urdf DESTINATION share/${{PROJECT_NAME}})
ament_package()
"""


def readme_text() -> str:
    rows = []
    for name, cp in PLACEMENTS.items():
        t = camera_link_in_ee(cp)
        rows.append(f"| `{name}` | {DESC[name]} | {f(t.xyz)} | {f(t.rpy)} | {DEPTH[cp.cam.name]} |")
    return f"""# {PKG}

Gerado por `scripts/ros_export.py` (projeto kinova-cam). Não edite à mão:
mude o modelo e rode o script de novo.

Anel bipartido da câmera RealSense no punho do Kinova Gen3 6DOF, para usar com
o `ros2_kortex` (`end_effector_link`) e o `realsense-ros` (`camera_link`).

## Montagem física (vale para os números abaixo)

- Câmera do lado **+Y do `end_effector_link`**: o lado oposto ao deslocamento
  dos botões de admitância (onde ficaria o módulo de visão da Kinova).
- Orelhas do anel alinhadas com os botões; câmera de pé (1/4" voltado para o
  punho).

## Transformação `end_effector_link → camera_link`

Valores do CAD, sem calibração (rpy em rad, eixos fixos x, y, z):

| versão | câmera / posição | xyz (m) | rpy (rad) | profundidade |
|---|---|---|---|---|
{chr(10).join(rows)}

Os mesmos valores (e quatérnios) estão em `config/camera_mounts.yaml`.

## Três formas de usar

1. **Só o TF** (sem URDF):

   ```bash
   ros2 launch {PKG} static_tf.launch.py version:=ring_rgb
   ros2 launch realsense2_camera rs_launch.py   # publish_tf:=true (padrão)
   ```

2. **Montagem no URDF do robô**, com o driver publicando a árvore da câmera
   (recomendado: usa a calibração de fábrica):

   ```xml
   <xacro:include filename="$(find {PKG})/urdf/kinova_cam_mount.urdf.xacro"/>
   <xacro:kinova_cam_mount parent="end_effector_link" version="ring_rgb"/>
   ```

   Cria `camera_mount_link` (malhas do anel, também como colisão para o
   MoveIt) e `camera_link`. Lance o driver com `publish_tf:=true`. Com
   `camera_mesh:="true"`, inclui a malha da câmera (ver abaixo).

3. **Câmera pelo xacro oficial** (`realsense2_description`), com todos os
   frames no URDF:

   ```xml
   <xacro:include filename="$(find {PKG})/urdf/kinova_cam_mount_realsense.urdf.xacro"/>
   <xacro:kinova_cam_mount_realsense parent="end_effector_link" version="ring_rgb"/>
   ```

   Lance o driver com `publish_tf:=false` (senão dois nós publicam os mesmos
   frames). Em simulação, `use_nominal_extrinsics:=true`.

`urdf/<versão>.urdf` são URDFs isolados (raiz `end_effector_link`) para conferir
com `check_urdf` ou no RViz.

As malhas das câmeras (`meshes/<versão>_camera.stl`) vêm do CAD oficial da
Intel e não são versionadas, como o resto do CAD de terceiros do projeto. Para
gerá-las, converta os `.SLDPRT` para STEP em `vendor/` (ver README do projeto)
e rode `scripts/ros_export.py`.

## Conferir no robô

Publique o TF, abra a nuvem de pontos no RViz e gire a junta 6: a nuvem deve
acompanhar a garra. Para precisão abaixo de ~2 mm, faça calibração mão-olho
(ex.: `easy_handeye2`) partindo destes valores.
"""


def main() -> None:
    mass = export_meshes()
    write(OUT / "config" / "camera_mounts.yaml", yaml_text(mass))
    write(OUT / "urdf" / "kinova_cam_mount.urdf.xacro", xacro_text())
    write(OUT / "urdf" / "kinova_cam_mount_realsense.urdf.xacro", xacro_rs_text())
    for name in PLACEMENTS:
        write(OUT / "urdf" / f"{name}.urdf", urdf_text(name))
    write(OUT / "launch" / "static_tf.launch.py", LAUNCH)
    write(OUT / "package.xml", PACKAGE_XML)
    write(OUT / "CMakeLists.txt", CMAKE)
    write(OUT / "README.md", readme_text())


if __name__ == "__main__":
    main()
