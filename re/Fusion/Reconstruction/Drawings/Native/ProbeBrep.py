import importlib
import json
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
common = importlib.reload(importlib.import_module("DrawingCommon"))

import adsk.core
import adsk.fusion

app = common.app
here = Path(__file__).resolve().parent
source = Path(
    sys.argv[1]
    if len(sys.argv) > 1
    else str(here.parents[4] / "re/Fusion/Study/bodymodes-405fbd002680/mirror_xy.f3d")
)
target = here / "Out" / "Designs" / ("Brep" + source.stem + ".json")
report = {"fusion_version": app.version, "source": source.name, "stage": "starting"}
owned = []


def checkpoint(stage):
    report["stage"] = stage
    common.save_json(target, report)


def settle(seconds):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        adsk.doEvents()


def run():
    checkpoint("importing")
    options = app.importManager.createFusionArchiveImportOptions(str(source))
    if options is None:
        raise RuntimeError("import options were not created")
    document = app.importManager.importToNewDocument(options)
    if document is None:
        raise RuntimeError("import did not produce a document")
    owned.append(document)
    settle(20)
    design = adsk.fusion.Design.cast(
        document.products.itemByProductType("DesignProductType")
    )
    if design is None:
        raise RuntimeError("Fusion did not present a design product")
    root = design.rootComponent
    bodies = []
    for index in range(root.bRepBodies.count):
        body = root.bRepBodies.item(index)
        bodies.append(
            {
                "name": common.safe(lambda body=body: body.name),
                "faces": common.safe(lambda body=body: body.faces.count),
                "edges": common.safe(lambda body=body: body.edges.count),
                "vertices": common.safe(lambda body=body: body.vertices.count),
                "volume_cm3": common.safe(lambda body=body: body.volume),
            }
        )
    report["bodies"] = bodies
    report["features"] = root.features.count
    report["status"] = "accepted"


try:
    run()
except Exception:
    report["status"] = "failed"
    report["traceback"] = traceback.format_exc()
finally:
    common.close_owned(owned, report)
    checkpoint("finished")
