"""Renderiza imagens de uma versão do anel no FreeCAD (chamado por render_images.sh).

Lê os STEP do mesmo diretório e grava PNGs em images/. Roda dentro da
interface gráfica, que preserva as cores do STEP, e fecha o FreeCAD no fim.
"""

import os

import FreeCAD
import FreeCADGui
import ImportGui
from PySide import QtCore

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "images")
W, H = 1920, 1440
with open(os.path.join(HERE, "render_job.txt")) as f:
    VARIANT = f.read().strip()  # ring | ring_rgb
FULL = f"kinova_gen3_d435i_{VARIANT}.step"
WRIST = f"wrist_{VARIANT}_assembly.step"
EXPLODED = f"wrist_{VARIANT}_exploded.step"

# (arquivo, nome da imagem, direção de visada, foco, ocultar)
# "FOV" são os cones de visão da câmera, mostrados só nas imagens 08 e 09.
# direção: do olho para a cena. Montagem completa: braço em +Z, câmera em +Y;
# montagens do punho: ferramenta em +Z, câmera em +Y.
SHOTS = [
    (FULL, "01_robo_completo", (-0.9, -1.0, -0.35), None, ("FOV",)),
    (FULL, "02_punho_lado_camera", (-0.8, -1.0, -0.45), "Clamp_Ring", ("FOV",)),
    (FULL, "03_punho_parafusos", (-0.7, 1.0, -0.25), "Clamp_Ring", ("FOV",)),
    (FULL, "04_punho_lateral", (-1.0, 0.0, 0.0), "Robotiq", ("FOV",)),
    (WRIST, "05_anel_camera", (-0.9, -1.0, -0.6), None, ("Robotiq", "FOV")),
    (WRIST, "06_anel_traseira", (-0.6, -0.8, 0.9), None, ("Robotiq", "FOV")),
    (EXPLODED, "07_explodida", (-1.0, -0.55, -0.6), None, ()),
    (FULL, "08_campo_de_visao_lateral", (-1.0, 0.0, 0.0), "FOV_D", ()),
    (FULL, "09_campo_de_visao", (-0.8, -1.0, -0.45), "FOV_D", ()),
]


def by_prefix(doc, prefix):
    return [o for o in doc.Objects if o.Label.startswith(prefix)]


def orient(view, d):
    """Câmera olhando na direção d, com +Z da cena para cima na imagem."""
    z = FreeCAD.Vector(*d).normalize() * -1  # eixo da câmera aponta para o olho
    up = FreeCAD.Vector(0, 0, 1)
    y = (up - z * up.dot(z)).normalize()
    x = y.cross(z)
    m = FreeCAD.Matrix(x.x, y.x, z.x, 0, x.y, y.y, z.y, 0, x.z, y.z, z.z, 0, 0, 0, 0, 1)
    view.setCameraOrientation(FreeCAD.Rotation(m))


def shoot():
    """Monta a lista de etapas; cada uma roda com o laço de eventos livre entre
    elas, para as animações de câmera do FreeCAD terminarem."""
    os.makedirs(OUT, exist_ok=True)
    docs = {}
    state = {}

    def load(step):
        if step not in docs:
            doc = FreeCAD.newDocument(os.path.splitext(step)[0])
            ImportGui.insert(os.path.join(HERE, step), doc.Name)
            doc.recompute()
            docs[step] = doc
        doc = docs[step]
        FreeCADGui.setActiveDocument(doc.Name)
        state["doc"], state["view"] = doc, FreeCADGui.getDocument(doc.Name).activeView()
        state["view"].setCameraType("Perspective")

    def setup(d, focus, hide):
        doc, view = state["doc"], state["view"]
        hidden = state.setdefault(doc.Name, [])
        for o in hidden:  # reexibe o que a imagem anterior deste documento ocultou
            o.ViewObject.Visibility = True
        hidden[:] = [o for o in doc.Objects if any(o.Label.startswith(h) for h in hide)]
        for o in doc.Objects:
            if o.Label.startswith("FOV_") and hasattr(o.ViewObject, "Transparency"):
                o.ViewObject.Transparency = 80
        for o in hidden:
            o.ViewObject.Visibility = False
        orient(view, d)

    def frame(focus):
        doc, view = state["doc"], state["view"]
        FreeCADGui.Selection.clearSelection()
        if focus:
            for o in by_prefix(doc, focus):
                FreeCADGui.Selection.addSelection(o)
            FreeCADGui.SendMsgToActiveView("ViewSelection")
            FreeCADGui.Selection.clearSelection()
        else:
            view.fitAll()

    def save(name, d):
        view = state["view"]
        view.saveImage(os.path.join(OUT, name + ".png"), W, H, "White")
        print("imagem:", name, "pedido", d, "obtido", view.getViewDirection(), flush=True)

    def finish():
        for doc in docs.values():
            FreeCAD.closeDocument(doc.Name)
        open(os.path.join(OUT, "done"), "w").close()
        FreeCADGui.getMainWindow().close()

    plan = []
    for step, name, d, focus, hide in SHOTS:
        plan += [
            (lambda step=step: load(step), 500),
            (lambda d=d, focus=focus, hide=hide: setup(d, focus, hide), 1500),
            (lambda focus=focus: frame(focus), 1500),
            (lambda name=name, d=d: save(name, d), 300),
        ]
    plan.append((finish, 0))
    steps = iter(plan)

    def tick():
        try:
            action, delay = next(steps)
        except StopIteration:
            return
        action()
        QtCore.QTimer.singleShot(delay, tick)

    tick()


QtCore.QTimer.singleShot(1500, shoot)
