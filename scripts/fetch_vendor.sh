#!/usr/bin/env bash
# Baixa os CAD oficiais (Kinova Gen3 6DOF, Robotiq e RealSense) para vendor/ (não versionados).
set -euo pipefail
cd "$(dirname "$0")/../vendor"
base="https://artifactory.kinovaapps.com/artifactory/generic-documentation-public/Documentation/Gen3/CADS%20%26%20Drawings"
curl -fL -o GEN3_6DOF_CAD_MODELS.zip "$base/GEN3_6DOF_CAD_MODELS.zip"
curl -fL -o End_Effector_Reference_Design.zip "$base/End_Effector_Reference_Design.zip"
unzip -o GEN3_6DOF_CAD_MODELS.zip GEN3_6DOF_NO-VISION_V01.STEP

# CAD oficial das câmeras RealSense D400 (SolidWorks .SLDPRT)
curl -fL -o RealSense_Depth-Cameras.zip "https://dev.realsenseai.com/download/41950"
unzip -o RealSense_Depth-Cameras.zip D435i_Solid.SLDPRT D405_Solid.SLDPRT

# Robotiq 2F-85 aberta, com dedos (mesmo arquivo do site da Robotiq)
unzip -p GEN3_6DOF_CAD_MODELS.zip 2F85-OPENED_20190924.STEP > Robotiq_2F85_Open.step
