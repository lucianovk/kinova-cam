#!/usr/bin/env bash
# Renderiza imagens de uma versão do anel no FreeCAD.
#
#   scripts/render_images.sh             # anel original  -> out/images/
#   scripts/render_images.sh ring_rgb    # RGB centrado   -> out/images/ring_rgb/
#
# Como em make_fcstd.sh, o trabalho é feito em ~/snap/freecad/common/kinova-cam
# (o FreeCAD do snap só lê o $HOME). O FreeCAD roda numa tela virtual (Xvfb).
# Rode antes: build.py --full
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
variant="${1:-ring}"
dest="$root/out/images"
if [ "$variant" != ring ]; then dest="$dest/$variant"; fi
stage="$HOME/snap/freecad/common/kinova-cam"
mkdir -p "$stage"
rm -rf "$stage/images"
cp "$root/out/kinova_gen3_d435i_$variant.step" "$root/out/wrist_${variant}_assembly.step" \
    "$root/out/wrist_${variant}_exploded.step" "$root/scripts/render_images.py" "$stage/"
echo "$variant" >"$stage/render_job.txt"  # o script lê daqui qual versão renderizar
# tela virtual (Xvfb): nenhuma janela aparece na sessão do usuário
nohup xvfb-run -a -s "-screen 0 1920x1440x24" freecad "$stage/render_images.py" \
    >"$stage/render.log" 2>&1 &
for _ in $(seq 1 600); do
    [ -e "$stage/images/done" ] && break
    sleep 1
done
[ -e "$stage/images/done" ] || { echo "FreeCAD não terminou (veja $stage/render.log)"; exit 1; }
rm "$stage/images/done"
mkdir -p "$dest"
for f in "$stage"/images/*.png; do  # corta a margem branca
    convert "$f" -trim -bordercolor white -border 60 "$dest/$(basename "$f")"
done
ls "$dest"
