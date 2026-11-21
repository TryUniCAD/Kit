from codecs import lookup
from dataclasses import replace
from importlib import import_module
import io
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from PrepareWidthDepthSameLocator import digest, host_paths, require


ROOT = Path(__file__).resolve().parents[4]


def author_document(request):
    from interchange import Expression, ParameterRole
    from interchange.Enums.EnumGeometry import GeometryKind
    from interchange.geometry.Models.GeometryCurves import PointGeometry
    from interchange.geometry.Models.Sketch import ConstraintRef, SketchEntity, SketchRelation
    from interchange.geometry.Models.VectorPlane import PlaneVector
    from interchange.serialization.Deserialize import FromData

    original = FromData(request["document"])
    (sketch,) = original.sketches
    (feature,) = original.feature_timeline
    width, _ = sketch.parameter_ids
    (depth,) = feature.parameter_ids
    require(request["equation"] == {"target": depth, "dependency": width, "divisor": 2},
            "the authored width-depth relationship is required")
    datum = SketchEntity("modeled-origin", GeometryKind.KPoint,
                         PointGeometry(PlaneVector(0.0, 0.0)), True, True)
    rule = SketchRelation(
        "modeled-origin-coincidence", "coincident",
        (ConstraintRef(datum.id), ConstraintRef(sketch.closed_profile_entity_ids[0][0], "start")),
    )
    return replace(
        original,
        sketches=(replace(sketch, entities=(*sketch.entities, datum),
                          constraints=(*sketch.constraints, rule)),),
        parameters=tuple(
            replace(row, role=ParameterRole.KDerived,
                    expression=Expression(f'"D1@{sketch.name}" / 2', (width,), "solidworks"))
            if row.id == depth else row
            for row in original.parameters
        ),
    )


def plain_part(document, locator, epoch, options):
    from convert.adapters.solidworks.Archive.Construction.BodyNames.AnchorPartInput import AnchorPartInput
    from convert.adapters.solidworks.Archive.Construction.Part.CheckPartInput import CheckPartInput
    from convert.adapters.solidworks.Archive.Construction.RectangleAnchors.MakeAnchorPart import MakeAnchorPart
    from convert.adapters.solidworks.Archive.Construction.SketchDimensions.RectDimInput import RectDimInput
    from convert.adapters.solidworks.Core.Preparation.BindPartIntent import BindPartIntent
    from convert.adapters.solidworks.Core.Preparation.Equations.PlanEqPart import PlanEqPart
    from convert.adapters.solidworks.Core.Preparation.FinalPartPath import FinalPartPath
    from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe

    projected, plan = PlanEqPart(document)
    recipe = MakePartRecipe(plan, epoch)
    path = FinalPartPath(locator, options, recipe.OutputValue, plan.NameValue)
    settings = BindPartIntent(projected, plan, recipe, path)
    CheckPartInput(projected, settings, plan)
    margin = min(plan.WidthValue, plan.HeightValue) / 4
    display = RectDimInput(
        (plan.WidthValue / 2, -margin), (plan.WidthValue + margin, plan.HeightValue / 2),
        settings.DesignIntent, settings.SelectedLeader, False,
    )
    return MakeAnchorPart(settings, plan, AnchorPartInput("corner", display))


def authored_settings(plan, epoch):
    from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe

    recipe = MakePartRecipe(plan, epoch)
    tree = recipe.SystemValue
    return {
        "system": {"folders": tree.FolderValues, "planes": dict(tree.PlaneNames),
                   "origin_name": tree.OriginName, "cabinet_name": tree.CabinetName},
        "density_kg_m3": 1.0,
        "document_density_preference_kg_m3": recipe.DensityValue,
    }


def build(lane):
    host_paths()
    from convert.adapters.base.WriteOptions import WriteOptions
    from convert.adapters.solidworks.Core.Preparation.Equations.PrepareEqPart import PrepareEqPart
    from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

    request = json.load(sys.stdin)
    for module in ("DocumentAssemblyValidate", "DocumentFeatureValidate", "DocumentReferenceValidate"):
        import_module("interchange.document.Validation." + module)
    for encoding in ("utf-16-le", "utf-8", "latin-1"):
        lookup(encoding)
    require(lane in ("Plain", "Reference"), "use one declared native lane")
    document = author_document(request)
    audit = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")
    sys.addaudithook(audit.InspectEvent)
    audit.BeginBuild()
    target = io.BytesIO()
    epoch = request["sdk_created_at"]
    options = WriteOptions(values={"final_destination": request["settings"]["output"]["path_name"]})
    if lane == "Reference":
        candidate = PrepareEqPart(document, target, epoch, options)
    else:
        candidate = plain_part(document, target, epoch, options)
    data = candidate.BytesValue
    expression = None
    if lane == "Reference":
        manager = candidate.SystemValue.RootValue.FieldsValue["f9d0"]
        (row,) = manager.FieldsValue["f58"]["items"]
        expression = row["o"].FieldsValue["f10"]
    report = {
        "expression": expression, "config_map_final": candidate.ConfigValue.MapValue.CounterValue,
        "resolved_map_final": candidate.ResolvedValue.MapValue.CounterValue,
        "runtime_input_file_reads": len(audit.DeniedReads), "sha256": digest(data), "bytes": len(data),
    }
    print(json.dumps(report, sort_keys=True), file=sys.stderr)
    sys.stdout.buffer.write(data)


if __name__ == "__main__":
    build(sys.argv[1])
