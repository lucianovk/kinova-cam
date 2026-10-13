#!/usr/bin/env bash
# Renderiza imagens da versão anel no FreeCAD e copia para out/images/.
#
# Como em make_fcstd.sh, o trabalho é feito em ~/snap/freecad/common/kinova-cam
# (o FreeCAD do snap só lê o $HOME). O FreeCAD roda numa tela virtual (Xvfb).
# Rode antes: build.py --variant ring --full
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
stage="$HOME/snap/freecad/common/kinova-cam"
mkdir -p "$stage"
rm -rf "$stage/images"
cp "$root/out/kinova_gen3_d435i_ring.step" "$root/out/wrist_ring_assembly.step" \
    "$root/out/wrist_ring_exploded.step" "$root/scripts/render_images.py" "$stage/"
# tela virtual (Xvfb): nenhuma janela aparece na sessão do usuário
nohup xvfb-run -a -s "-screen 0 1920x1440x24" freecad "$stage/render_images.py" \
    >"$stage/render.log" 2>&1 &
for _ in $(seq 1 600); do
    [ -e "$stage/images/done" ] && break
    sleep 1
done
[ -e "$stage/images/done" ] || { echo "FreeCAD não terminou (veja $stage/render.log)"; exit 1; }
rm "$stage/images/done"
mkdir -p "$root/out/images"
for f in "$stage"/images/*.png; do  # corta a margem branca
    convert "$f" -trim -bordercolor white -border 60 "$root/out/images/$(basename "$f")"
done
ls "$root/out/images"
