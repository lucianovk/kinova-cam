#!/usr/bin/env bash
# Gera o projeto FreeCAD da montagem completa e o deixa aberto no FreeCAD.
#
#   scripts/make_fcstd.sh              # anel original
#   scripts/make_fcstd.sh ring_rgb     # anel com o RGB centrado na garra
#
# Rode antes: build.py --full
#
# O FreeCAD do snap só lê arquivos dentro do $HOME, então o trabalho é feito
# em ~/snap/freecad/common/kinova-cam e o .FCStd é copiado de volta para out/.
# Para reabrir depois, use a cópia de lá (o snap não consegue abrir out/).
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
stage="$HOME/snap/freecad/common/kinova-cam"
name="kinova_gen3_d435i_${1:-ring}"
fcstd="$stage/$name.FCStd"
mkdir -p "$stage"
cp "$root/out/$name.step" "$root/scripts/make_fcstd.py" "$stage/"
echo "$name" >"$stage/job.txt"  # o script lê daqui qual montagem converter
rm -f "$fcstd"
# interface gráfica: preserva as cores do STEP
nohup freecad "$stage/make_fcstd.py" >"$stage/freecad.log" 2>&1 &
for _ in $(seq 1 300); do
    [ -s "$fcstd" ] && sleep 2 && break
    sleep 1
done
[ -s "$fcstd" ] || { echo "FreeCAD não gerou $fcstd (veja $stage/freecad.log)"; exit 1; }
cp "$fcstd" "$root/out/"
echo "projeto aberto no FreeCAD: $fcstd"
