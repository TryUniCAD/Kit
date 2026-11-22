from argparse import ArgumentParser
from codecs import lookup
from dataclasses import replace
from hashlib import sha256
from importlib import import_module
import json
from math import isclose
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src"))

from convert.adapters.solidworks.Archive.Construction.Part.MakeBlindPart import MakeBlindByPlan
from convert.adapters.solidworks.Archive.Construction.Shells.MakeShellMut import MakeShellMut
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from convert.adapters.solidworks.Core.Preparation.Shells.PlanOpenShell import PlanOpenShell
from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.Enums.EnumGeometry import GeometryKind
from interchange.Enums.EnumValues import ParameterRole, ValueKind
from interchange.Features.FeatureBody import DesignBody
from interchange.Features.FeatureExtrude import ExtrudeEnd, ExtrudeFeature
from interchange.Features.FeatureKinds import ShellFeature
from interchange.Features.FeatureStep import FeatureStep
from interchange.document.Models.DocumentModel import CadDocument
from interchange.geometry.Models.GeometryCurves import LineGeometry
from interchange.geometry.Models.Selection import SelectPathElem, Selection
from interchange.geometry.Models.Sketch import Sketch, SketchEntity
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorPlane import PlaneVector
from interchange.Records.RecordConfig import Configuration
from interchange.Records.RecordParameter import Parameter, ParameterValue
from interchange.Records.RecordSource import CadSource


def require(condition, error):
    if not condition:
        raise ValueError(error)


def document(name, width, depth, height, thickness, origin):
    x, y = origin
    points = tuple(PlaneVector(x + dx * width, y + dy * depth)
                   for dx, dy in ((-.5, -.5), (.5, -.5), (.5, .5), (-.5, .5)))
    lines = tuple(SketchEntity(f"line:{index}", GeometryKind.KLine, LineGeometry(first, second))
                  for index, (first, second) in enumerate(zip(points, (*points[1:], points[0]), strict=True)))
    sketch = Sketch("profile", "ShellStockSketch", support_plane_id="front", entities=lines,
                    closed_profile_entity_ids=(tuple(line.id for line in lines),))
    stock_size = ParameterValue(float(height), ValueKind.KLength, "mm")
    wall_size = ParameterValue(float(thickness), ValueKind.KLength, "mm")
    stock = FeatureStep("stock", "ShellStockBoss", FeatureKind.KExtrusion, 0,
                        definition=ExtrudeFeature(stock_size, ExtrudeEnd.KBlind, False, False),
                        sketch_id=sketch.id, operation=BooleanOp.KCreate, parameter_ids=("stock-depth",))
    shell = FeatureStep("shell", "OpenShell", FeatureKind.KShell, 1,
                        definition=ShellFeature(wall_size, False), input_feature_ids=(stock.id,),
                        selection_ids=("cap",), parameter_ids=("wall-depth",))
    choice = Selection("cap", "Removed cap", (SelectPathElem("feature", stock.id, "face:1"),))
    spec = json.dumps([name, width, depth, height, thickness, origin], allow_nan=False).encode()
    return CadDocument(
        CadSource("interchange.json", name + ".json", sha256(spec).hexdigest()),
        configurations=(Configuration("config", "Default", active=True),),
        support_planes=(SupportPlane("front", "Front Plane", Transform()),),
        sketches=(sketch,),
        bodies=(DesignBody("result", shell.name, shell.id),),
        feature_timeline=(stock, shell),
        selections=(choice,),
        parameters=(Parameter("stock-depth", "D1", stock_size, ParameterRole.KDriving, owner_id=stock.id),
                    Parameter("wall-depth", "D1", wall_size, ParameterRole.KDriving, owner_id=shell.id)),
        metadata={"name": name},
        units="mm",
    )


def closed_plan(model):
    plan = PlanOpenShell(model)
    time = 1765500071
    settings = MakePartRecipe(plan.StockValue, time)
    stock = MakeBlindByPlan(model, settings, plan.StockValue)
    feature, driver = MakeShellMut(stock, plan, settings)
    atom = feature.FieldsValue["f538"]
    removed = feature.FieldsValue["f828"].FieldsValue["items"]
    require(len(removed) == 1, "shell has no unique removed face")
    face = removed[0]["o"]
    edge = feature.FieldsValue["f848"]
    slots = face.FieldsValue["fe8"].FieldsValue["f10"]
    types = [item["f08"].ClassValue.NameValue if item["f08"] is not None else None for item in slots]
    require(types == ["moEndFaceSurfIdRep_c", *(["moFromSktEntSurfIdRep_c"] * 4), None],
            "shell removed face lost its cap and four adjacent stock sides")
    role = slots[0]["f08"].FieldsValue["f38"]
    require(role == 1 and edge.ClassValue.NameValue == "moCompEdge_c", "shell confused the removed cap with the edge")
    fields = driver.DimensionValue.FieldsValue
    value = driver.ParameterValue.FieldsValue["f58"]
    require(fields["f28"] is driver.ParameterValue and driver.DisplayValue is feature.FieldsValue["f818"]
            and isclose(fields["fa0"]["x"] - fields["f80"]["x"], value, rel_tol=1e-12, abs_tol=1e-15),
            "actual wall driver and geometry anchors disagree")
    stock_values = stock.BossValue.FeatureValue.FieldsValue
    require((atom.FieldsValue["f12c"], atom.FieldsValue["f130"]) == (stock_values["f08"], feature.FieldsValue["f08"]),
            "shell result ownership differs from the actual stock chain")
    return {"source": model.source.sha256, "shell_class": feature.ClassValue.NameValue,
            "cap_roles": [None if item["f08"] is None else item["f08"].FieldsValue["f38"] for item in slots],
            "stock_id": stock_values["f08"], "shell_id": feature.FieldsValue["f08"], "atom_id": atom.FieldsValue["f140"],
            "driver_m": value, "dimension_id": fields["f50"], "outer_witness": fields["f80"], "inner_witness": fields["fa0"],
            "display_point": driver.DisplayValue.FieldsValue["f6a0"]["f38"]}


def main():
    parser = ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    inputs = (
        ("OpenShellCalibration", 53, 41, 28, 2.8, (0, 0)),
        ("OpenShellTranslated", 62, 38, 36, 4.15, (8.5, -12.25)),
        ("OpenShellDistinct", 45, 68, 23, 1.875, (-3, 7.5)),
    )
    for name in ("interchange.document.Behavior.DocumentIo",
                 "interchange.document.Validation.DocumentFeatureValidate",
                 "interchange.document.Validation.DocumentReferenceValidate",
                 "interchange.document.Validation.DocumentAssemblyValidate",
                 "interchange.document.Models.DocumentProvenance"):
        import_module(name)
    for encoding in ("utf-8", "utf-16-le", "cp1252", "latin-1"):
        lookup(encoding)
    models = tuple(document(*row) for row in inputs)
    Model = models[0]
    stock, shell = Model.feature_timeline
    wrong_end = replace(Model.selections[0], path=(SelectPathElem("feature", stock.id, "face:0"),))
    limits = (("Wrong end", replace(Model, selections=(wrong_end,))),
              ("Outward wall", replace(Model, feature_timeline=(stock, replace(shell, definition=replace(shell.definition, outward=True))))),
              ("Consumed cavity", document("ClosedShell", 30, 26, 21, 13, (0, 0))))
    active = True
    denied = []

    def audit(event, values):
        if active and event in {"open", "subprocess.Popen", "os.system", "socket.connect", "socket.__new__", "ctypes.dlopen"}:
            denied.append(event)
            raise RuntimeError(f"model-only shell construction performed an external access: {event}")

    sys.addaudithook(audit)
    plans = tuple(closed_plan(model) for model in models)
    refusals = {}
    for label, invalid in limits:
        try:
            PlanOpenShell(invalid)
        except ValueError as error:
            refusals[label] = str(error)
        else:
            raise ValueError(f"unqualified shell scope was accepted: {label}")
    active = False
    with args.output.open("x", encoding="utf-8") as file:
        json.dump({"schema": "kit-sw2026-open-shell-construction-plan-v1", "plans": plans,
                   "refusals": refusals, "runtime_accesses": denied,
                   "native_files_emitted": 0, "heldout_sources_read": 0}, file, indent=2, allow_nan=False)
        file.write("\n")


if __name__ == "__main__":
    main()
