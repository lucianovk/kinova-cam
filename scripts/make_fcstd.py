"""Gera <nome>.FCStd a partir de <nome>.step no mesmo diretório (nome em job.txt).

Chamado por scripts/make_fcstd.sh, que copia este script e o STEP para uma
pasta que o FreeCAD do snap consegue ler. Com a interface gráfica as cores do
STEP vão para o projeto; no freecad.cmd as peças ficam sem cor.
"""

import os

import FreeCAD

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, "job.txt")) as f:
    NAME = f.read().strip()
STEP = os.path.join(HERE, NAME + ".step")
FCSTD = os.path.join(HERE, NAME + ".FCStd")

doc = FreeCAD.newDocument("Kinova_Gen3_D435i")
if FreeCAD.GuiUp:
    import FreeCADGui
    import ImportGui

    ImportGui.insert(STEP, doc.Name)
else:
    import Import

    Import.insert(STEP, doc.Name)
doc.recompute()

if FreeCAD.GuiUp:
    # destaca a peça: braço semitransparente, vista no punho pelo lado da câmera
    def by_label(prefix):
        return next(o for o in doc.Objects if o.Label.startswith(prefix))

    arm, mount = by_label("Kinova_Gen3_6DOF"), by_label("Wrist_")
    for o in arm.OutListRecursive:
        if hasattr(o.ViewObject, "Transparency"):
            o.ViewObject.Transparency = 75
    for o in doc.Objects:  # cones de visão da câmera
        if o.Label.startswith("FOV_") and hasattr(o.ViewObject, "Transparency"):
            o.ViewObject.Transparency = 80
    view = FreeCADGui.activeDocument().activeView()
    view.setViewDirection((-0.8, -1.0, -0.45))  # de +X/+Y, um pouco de cima
    FreeCADGui.Selection.clearSelection()
    FreeCADGui.Selection.addSelection(mount)
    FreeCADGui.SendMsgToActiveView("ViewSelection")
    FreeCADGui.Selection.clearSelection()

doc.saveAs(FCSTD)
print(f"salvo: {FCSTD} ({len(doc.Objects)} objetos)")
