from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtWidgets


def vector(value):
    return [float(value.x), float(value.y), float(value.z)]


def shape_record(obj):
    result = {"name": obj.Name, "label": obj.Label, "type": obj.TypeId, "status": list(obj.State)}
    if hasattr(obj, "Shape") and not obj.Shape.isNull():
        shape = obj.Shape
        solids = shape.Solids
        volume = sum(float(solid.Volume) for solid in solids)
        center = [sum(float(solid.Volume) * vector(solid.CenterOfMass)[axis] for solid in solids) / volume for axis in range(3)] if volume else None
        result.update(solids=len(solids), volume_mm3=volume, area_mm2=float(shape.Area), center_mm=center, valid=bool(shape.isValid()), visible=bool(obj.ViewObject.Visibility))
    if "sourceFile" in obj.PropertiesList:
        result["source_file"] = str(obj.sourceFile)
    return result


def main():
    job = json.loads(Path(os.environ["KIT_PUBLIC_SOURCE_JOB"]).read_text())
    output = Path(job["output"])
    output.mkdir(parents=True, exist_ok=True)
    source = Path(job["source"])
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    sys.path.insert(0, job["assembly_module_path"])
    import a2p_importedPart_class
    import a2p_viewProviderProxies
    document = App.openDocument(str(source))
    Gui.activateWorkbench("PartWorkbench")
    window = Gui.getMainWindow()
    window.resize(1600, 1000)
    Gui.activeDocument().activeView().viewAxonometric()
    Gui.activeDocument().activeView().fitAll()
    Gui.updateGui()
    record = {"authority": "native-freecad-source-observation", "version": list(App.Version()), "source": str(source), "source_sha256": before, "recomputed": False, "saved": False, "objects": [shape_record(obj) for obj in document.Objects]}
    (output / "FreecadSource.json").write_text(json.dumps(record, indent=2) + "\n")

    def capture():
        area = window.findChild(QtWidgets.QMdiArea)
        candidates = [item for item in area.subWindowList() if item.windowTitle().startswith(document.Label + " :")]
        record["view_windows"] = [item.windowTitle() for item in area.subWindowList()]
        if len(candidates) != 1:
            record["capture_exception"] = f"expected one native source view, found {len(candidates)}"
            (output / "FreecadSource.json").write_text(json.dumps(record, indent=2) + "\n")
            App.closeDocument(document.Name)
            QtWidgets.QApplication.instance().quit()
            return
        area.setActiveSubWindow(candidates[0])
        window.show()
        window.raise_()
        window.activateWindow()
        record["active_view_title"] = candidates[0].windowTitle()
        Gui.activeDocument().activeView().viewAxonometric()
        Gui.activeDocument().activeView().fitAll()
        Gui.updateGui()
        QtCore.QTimer.singleShot(1000, save_capture)

    def save_capture():
        try:
            Gui.updateGui()
            path = output / "FreecadSource.png"
            record["capture_api"] = "QScreen.grabWindow(native-window-id)"
            record["native_window_id"] = int(window.winId())
            Gui.activeDocument().activeView().saveImage(str(output / "FreecadViewport.png"), 1600, 1000, "Current")
            if not window.screen().grabWindow(window.winId()).save(str(path), "PNG"):
                raise RuntimeError("native FreeCAD window capture failed")
            record.update(screenshot_sha256=hashlib.sha256(path.read_bytes()).hexdigest(), source_sha256_after=hashlib.sha256(source.read_bytes()).hexdigest())
            (output / "FreecadSource.json").write_text(json.dumps(record, indent=2) + "\n")
        except Exception as error:
            record["capture_exception"] = repr(error)
            (output / "FreecadSource.json").write_text(json.dumps(record, indent=2) + "\n")
        finally:
            App.closeDocument(document.Name)
            QtWidgets.QApplication.instance().quit()

    QtCore.QTimer.singleShot(5000, capture)


try:
    main()
except Exception as error:
    job = json.loads(Path(os.environ["KIT_PUBLIC_SOURCE_JOB"]).read_text())
    output = Path(job["output"])
    output.mkdir(parents=True, exist_ok=True)
    (output / "FreecadSourceFailure.json").write_text(json.dumps({"exception": repr(error)}, indent=2) + "\n")
    for name in tuple(App.listDocuments()):
        App.closeDocument(name)
    QtWidgets.QApplication.instance().quit()
