# kinova_cam_description

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
| `ring` | D435i centrada no punho, 15° (versão original) | 0.0175 0.053661 0.005196 | 0 -1.309 -1.5708 | 424x240 (Z mín ~105 mm) |
| `ring_rgb` | D435i com a lente RGB no eixo da garra, 20° | -0.015 0.065683 0.005691 | 0 -1.22173 -1.5708 | 424x240 (Z mín ~105 mm) |
| `ring_stereo` | D435i com o meio da linha de base no eixo da garra, 20° | 0.025 0.065683 0.005691 | 0 -1.22173 -1.5708 | 424x240 (Z mín ~105 mm) |
| `ring_d405` | D405 com o imageador esquerdo (cor e profundidade) no eixo da garra, 15° | 0 0.061768 0.005851 | 0 -1.309 -1.5708 | 1280x720 (Z mín ~100 mm) |

Os mesmos valores (e quatérnios) estão em `config/camera_mounts.yaml`.

## Três formas de usar

1. **Só o TF** (sem URDF):

   ```bash
   ros2 launch kinova_cam_description static_tf.launch.py version:=ring_rgb
   ros2 launch realsense2_camera rs_launch.py   # publish_tf:=true (padrão)
   ```

2. **Montagem no URDF do robô**, com o driver publicando a árvore da câmera
   (recomendado: usa a calibração de fábrica):

   ```xml
   <xacro:include filename="$(find kinova_cam_description)/urdf/kinova_cam_mount.urdf.xacro"/>
   <xacro:kinova_cam_mount parent="end_effector_link" version="ring_rgb"/>
   ```

   Cria `camera_mount_link` (malhas do anel, também como colisão para o
   MoveIt) e `camera_link`. Lance o driver com `publish_tf:=true`. Com
   `camera_mesh:="true"`, inclui a malha da câmera (ver abaixo).

3. **Câmera pelo xacro oficial** (`realsense2_description`), com todos os
   frames no URDF:

   ```xml
   <xacro:include filename="$(find kinova_cam_description)/urdf/kinova_cam_mount_realsense.urdf.xacro"/>
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
