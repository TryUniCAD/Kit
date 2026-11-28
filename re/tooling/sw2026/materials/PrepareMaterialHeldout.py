from argparse import ArgumentParser
from base64 import b64encode
from codecs import lookup
from dataclasses import replace
from hashlib import sha256
import importlib
import json
from math import isclose, isfinite
from pathlib import Path, PureWindowsPath
import re
import sys


SCHEMA = "kit.sw2026.neutral-material-preparation.v1"
SCOPE = "origin-owned-physical-material"
PENDING = ("assigned_appearance", "numeric_catalog_identity", "material_tree")
CASE_FIELDS = {
    "id", "kind", "configuration", "width_m", "height_m", "depth_m", "edited_depth_m",
    "first_material_key", "second_material_key",
}
MATERIAL_FIELDS = {"database_name", "name", "density_kg_m3"}
DRIVERS = ("D1@AnchorSketch", "D2@AnchorSketch", "D1@AnchorBoss")
ALLOWED_CHANGES = {"Contents/CMgr", "Contents/Config-0", "Contents/Config-0-ResolvedFeatures"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(value):
    return sha256(value).hexdigest()


def encode(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False) + "\n").encode()


def pairs(rows):
    value = dict(rows)
    require(len(value) == len(rows), "duplicate preparation input field")
    return value


def token(value):
    return type(value) is str and bool(value) and value == value.strip() and value.isprintable() and not set(value) & {"|", "/", chr(92)}


def validate(request):
    require(type(request) is dict and set(request) == {"schema", "scope", "case", "catalog", "target"}
            and request["schema"] == SCHEMA, "expected the selected-case neutral preparation envelope")
    require(request["scope"] == SCOPE, "full source preservation requires the material appearance, numeric identity and MATERIALTREE owners")
    case, catalog, target = (request[key] for key in ("case", "catalog", "target"))
    require(type(case) is dict and set(case) == CASE_FIELDS and type(case["id"]) is str
            and re.fullmatch("[A-Za-z][A-Za-z0-9]{1,63}", case["id"])
            and case["kind"] in ("corner", "center") and case["configuration"] == "Default",
            "selected case requires its explicit corner or center intent and ordinary active configuration")
    require((case["first_material_key"], case["second_material_key"]) in (("A", "B"), ("B", "A")),
            "selected case must specify two different material selectors")
    require(all(type(case[key]) is float and isfinite(case[key]) and 0.001 < case[key] < 0.25
                for key in ("width_m", "height_m", "depth_m", "edited_depth_m"))
            and case["depth_m"] != case["edited_depth_m"], "selected case requires finite SI lengths and an actual depth edit")
    require(type(catalog) is dict and set(catalog) == {"A", "B"}, "need exactly two explicit catalog selections")
    result = {}
    for key, row in catalog.items():
        require(type(row) is dict and set(row) == MATERIAL_FIELDS and token(row["database_name"])
                and token(row["name"]), "material requires a two-token declared catalog and name")
        path = PureWindowsPath(row["database_name"])
        rho = row["density_kg_m3"]
        require(path.name == row["database_name"] and not path.drive and path.suffix.casefold() == ".sldmat" and token(path.stem)
                and type(rho) is float and isfinite(rho) and rho > 0.0 and isfinite(rho * 0.25**3),
                "material requires a catalog filename and finite positive SI density")
        result[key] = (path.stem, row["name"], rho)
    require(result["A"][:2] != result["B"][:2] and result["A"][2] != result["B"][2],
            "material selections must distinguish both identity and density")
    require(type(target) is dict and set(target) == {"path", "saved_at"} and type(target["path"]) is str,
            "need the explicit final candidate locator and save epoch")
    locator = PureWindowsPath(target["path"])
    require(locator.drive.casefold() == "c:" and locator.is_absolute() and ".." not in locator.parts
            and str(locator) == target["path"] and locator.suffix.casefold() == ".sldprt"
            and re.fullmatch("[A-Za-z][A-Za-z0-9]{1,63}", locator.stem)
            and all(not set(part) & set('<>:"|?*') and part == part.rstrip(" .") for part in locator.parts[1:])
            and type(target["saved_at"]) is int and 0 < target["saved_at"] <= 0xFFFFFFFF,
            "candidate needs an exact Windows-local SLDPRT locator and UTC save epoch")
    return case, result, locator


def neutral(case, locator, material):
    from interchange.document.Models.DocumentModel import CadDocument
    from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
    from interchange.Enums.EnumGeometry import GeometryKind
    from interchange.Enums.EnumUnits import UnitSystem
    from interchange.Enums.EnumValues import ParameterRole, ValueKind
    from interchange.Features.FeatureBody import DesignBody
    from interchange.Features.FeatureExtrude import ExtrudeEnd, ExtrudeFeature
    from interchange.Features.FeatureStep import FeatureStep
    from interchange.geometry.Models.GeometryCurves import LineGeometry
    from interchange.geometry.Models.Sketch import ConstraintRef, Sketch, SketchEntity, SketchRelation
    from interchange.geometry.Models.SupportPlane import SupportPlane
    from interchange.geometry.Models.Transform import Transform
    from interchange.geometry.Models.VectorPlane import PlaneVector
    from interchange.Records.RecordConfig import Configuration
    from interchange.Records.RecordParameter import Parameter, ParameterValue
    from interchange.Records.RecordSource import CadSource

    width, height, depth = (case[key] * 1000.0 for key in ("width_m", "height_m", "depth_m"))
    left, bottom = (0.0, 0.0) if case["kind"] == "corner" else (-width / 2, -height / 2)
    points = ((left, bottom), (left + width, bottom), (left + width, bottom + height), (left, bottom + height))
    edges = tuple(SketchEntity(f"profile/edge/{index}", GeometryKind.KLine,
                              LineGeometry(PlaneVector(*point), PlaneVector(*points[(index + 1) % 4])))
                  for index, point in enumerate(points))
    profile_id, boss_id, support_id = "sketch/profile", "feature/boss", "plane/front"
    parameters = tuple(Parameter(f"driver/{role}", name, ParameterValue(value, ValueKind.KLength, "mm"),
                                 ParameterRole.KDriving, owner_id=owner)
                       for role, name, value, owner in (("width", "D1", width, profile_id),
                                                        ("height", "D2", height, profile_id),
                                                        ("depth", "D1", depth, boss_id)))
    directions = tuple(SketchRelation(f"axis/{index}", "horizontal" if index % 2 == 0 else "vertical",
                                      (ConstraintRef(edge.id),)) for index, edge in enumerate(edges))
    lengths = tuple(SketchRelation(f"length/{index}", "distance",
                                    (ConstraintRef(edge.id, "start"), ConstraintRef(edge.id, "end")), param.id)
                    for index, (edge, param) in enumerate(zip(edges[:2], parameters[:2], strict=True)))
    sketch = Sketch(profile_id, "AnchorSketch", support_id, edges, (*directions, *lengths),
                    parameter_ids=tuple(value.id for value in parameters[:2]),
                    closed_profile_entity_ids=(tuple(edge.id for edge in edges),))
    boss = FeatureStep(boss_id, "AnchorBoss", FeatureKind.KExtrusion, 0, sketch_id=profile_id,
                       parameter_ids=(parameters[2].id,), operation=BooleanOp.KCreate,
                       definition=ExtrudeFeature(parameters[2].value, ExtrudeEnd.KBlind, False, False))
    return CadDocument(
        CadSource("kit-neutral", "<selected-case-intent>", digest(encode(case))),
        (Configuration("configuration/default", case["configuration"], True),), parameters,
        (SupportPlane(support_id, "Front Plane", Transform()),), (sketch,), (), (boss,),
        (DesignBody("body/boss", boss.name, boss.id),),
        materials=(material,), metadata={"name": locator.stem}, units=UnitSystem.KMillimeter,
    )


def analytic(case, depth, catalog_row):
    width, height = (case[key] for key in ("width_m", "height_m"))
    left, bottom = (0.0, 0.0) if case["kind"] == "corner" else (-width / 2, -height / 2)
    catalog, material, density = catalog_row
    volume = width * height * depth
    return {
        "configuration": case["configuration"], "solid_body_count": 1, "density_kg_m3": density,
        "part_material": {"database": catalog, "material": material}, "mass_kg": density * volume,
        "geometry": {"volume": volume, "area": 2 * (width * height + depth * (width + height)),
                     "com": [left + width / 2, bottom + height / 2, depth / 2],
                     "bounds": [[left, bottom, 0.0], [left + width, bottom + height, depth]]},
        "dimensions_m": dict(zip(DRIVERS, (width, height, depth), strict=True)),
    }


def compose(plan, settings, anchor, physical, density, identity):
    from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import PersistentIds
    from convert.adapters.solidworks.Archive.Construction.Part.FinishBlindMut import FinishBlindMut
    from convert.adapters.solidworks.Archive.Construction.Part.MakePartBaseMut import MakePartBaseMut
    from convert.adapters.solidworks.Archive.Construction.Part.MakePartProfMut import MakePartProfMut
    from convert.adapters.solidworks.Archive.Construction.RectangleAnchors.MakeCornerMut import MakeCornerMut
    from convert.adapters.solidworks.Archive.Construction.RectangleCenters.MakeCenterMut import MakeCenterMut
    from convert.adapters.solidworks.Archive.Construction.SketchDimensions.MakeRectDimsMut import MakeRectDimsMut
    from convert.adapters.solidworks.Archive.Construction.SketchDimensions.MakeSketchKeys import MakeSketchKeys

    allocator = PersistentIds()
    system = MakePartBaseMut(settings, plan, allocator)
    profile = MakePartProfMut(system, settings, plan, allocator)
    dimensions = MakeRectDimsMut(profile, anchor.DimensionsValue, allocator, plan.SketchDriverNames)
    (MakeCornerMut if anchor.KindValue == "corner" else MakeCenterMut)(profile, system.OriginValue)
    part, config = system.RootValue.FieldsValue, system.ConfigValues[0].FieldsValue
    require((part["f1420"], config["fc50"], config["f78"]) == (None, -1, None),
            "underlying fresh part and configuration material owners changed")
    visual = physical.MakeModelVisual()
    visual.FieldsValue["f20"]["f20"] = identity
    part["f1420"], config["fc50"], config["f78"] = physical.make_density(density), density, visual
    return FinishBlindMut(system, profile, settings, plan, allocator,
                          MakeSketchKeys(dimensions, settings.DocumentUnits.LengthUnit))


def check_written_anchor(candidate, case, expected):
    from SdkBlindPartChecks import index as compact_index
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink

    linked = ReadNativeLink(SldprtArchive.FromBytes(candidate.BytesValue), 0)
    profile, = [node for node in linked.ResolvedValue.RootsValue if node.ClassValue.NameValue == "moProfileFeature_c"]
    origin, = [node for node in linked.ResolvedValue.RootsValue if node.ClassValue.NameValue == "moOriginProfileFeature_c"]
    sketch = profile.FieldsValue["pd_f80"]
    fields = sketch.FieldsValue
    dims = fields["dims"]
    points = fields["points"]
    external = points[-1]["point"]
    reference = external["ext"].FieldsValue["f08"].FieldsValue["f58"].FieldsValue
    center = case["kind"] == "center"
    require((fields["npoints"], fields["nlines"], dims["nlog2"], dims["nlog1"], dims["ng2"]) ==
            (expected["point_count"], expected["line_count"], expected["coincidence_count"], 4, 2),
            "written anchor topology does not match the constructed owner graph")
    last = dims["log_g2"][-1]["d"]
    require(points[-1]["kind"] == 1 and last["f80"] == 9, "missing written origin coincidence")
    compact_index(last["h1"].FieldsValue, "idx", "f18", 0x777F, len(points) - 1)
    compact_index(last["h2"].FieldsValue, "idx", "f18", 0x777F, 4 if center else 0)
    require(reference["ff0"]["f00"] == origin.FieldsValue["f08"] and reference["f100"] == 1,
            "written anchor does not reference the actual resolved Origin")
    if center:
        for index, row in enumerate(dims["log_g2"][:-1]):
            relation = row["d"]
            line = fields["lines"][index + 4]["line"]
            compact_index(relation["h1"].FieldsValue, "idx", "f18", 0x777F, 4)
            compact_index(relation["h2"].FieldsValue, "idx", "f18", 0x777F, index + 4)
            require(relation["f80"] == 9 and line["f54"] & 8
                    and line["fc8_s"] == index and line["fcc_s"] == index + 2,
                    "written center does not reference both actual diagonal segments")
    return True


def prepare(request, physical, graph_check):
    from convert.adapters.solidworks.Archive.Construction.BodyNames.AnchorPartInput import AnchorPartInput
    from convert.adapters.solidworks.Archive.Construction.BodyNames.MakeAnchorBase import MakeAnchorBase
    from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import SelfFileInput
    from convert.adapters.solidworks.Archive.Construction.Part.CheckPartInput import CheckPartInput
    from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectRectDims import ProjectRectDims
    from convert.adapters.solidworks.Archive.Construction.SketchDimensions.RectDimInput import RectDimInput
    from convert.adapters.solidworks.Core.Preparation.BindPartIntent import BindPartIntent
    from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
    from interchange.document.Validation.DocumentValidate import AssertValid
    from interchange.materials.MaterialRecord import MaterialRecord
    from interchange.serialization.EncodeData import ToData

    case, catalog, locator = validate(request)
    before, after = [catalog[case[field]] for field in ("first_material_key", "second_material_key")]
    tint = physical.MakeModelVisual().FieldsValue["f0c"]
    default_color = tuple(((tint >> shift) & 255) / 255 for shift in (0, 8, 16)) + (1.0,)
    material = MaterialRecord("material/assigned-part", before[1], before[2], default_color)
    document = neutral(case, locator, material)
    AssertValid(document)
    density, identity = physical.material_intent(
        document, {"material_ref": material.id, "catalog": before[0], "catalog_id": None}
    )
    require(identity.count("|") == 1 and density == before[2], "physical owner changed its selected material")
    geometry_view = replace(document, materials=())
    plan = ProjectRectDims(geometry_view)
    epoch = request["target"]["saved_at"]
    settings = BindPartIntent(geometry_view, plan, MakePartRecipe(plan, epoch), SelfFileInput(str(locator), epoch))
    CheckPartInput(geometry_view, settings, plan)
    low, high = plan.VerticesValue[0], plan.VerticesValue[2]
    width, height = (case[key] for key in ("width_m", "height_m"))
    require(all(isclose(left, right, rel_tol=1e-12, abs_tol=1e-14) for left, right in zip(
        (plan.WidthValue, plan.HeightValue, plan.DepthValue), (width, height, case["depth_m"]), strict=True)),
        "actual neutral extrusion and its three drivers differ from selected intent")
    dimension_input = RectDimInput((low[0] + width / 2, low[1] - 0.3 * height),
                                   (high[0] + 0.3 * width, low[1] + height / 2),
                                   settings.DesignIntent, settings.SelectedLeader, False)
    anchor = AnchorPartInput(case["kind"], dimension_input)
    baseline = MakeAnchorBase(geometry_view, settings, anchor)
    candidate = compose(plan, settings, anchor, physical, density, identity)
    observed = physical.inspect(candidate, physical.MODES["all"], density, identity)
    graph = graph_check(candidate, case["kind"], document)
    graph["written_owner_readback"] = check_written_anchor(candidate, case, graph)
    streams = candidate.StreamsValue
    require(streams.keys() == baseline.StreamsValue.keys(), "material changed the ordinary stream inventory")
    changed = sorted(name for name, data in streams.items() if data != baseline.StreamsValue[name])
    require({"Contents/CMgr", "Contents/Config-0"} <= set(changed) <= ALLOWED_CHANGES,
            "material changed an unrelated generated lane or failed to reach both owners")
    expected = {
        "initial": analytic(case, case["depth_m"], before),
        "swapped": analytic(case, case["depth_m"], after),
        "depth_edit": analytic(case, case["edited_depth_m"], before),
        "swapped_depth_edit": analytic(case, case["edited_depth_m"], after),
    }
    return {
        "schema": "kit.sw2026.neutral-material-preparation-result.v1",
        "scope": SCOPE, "pending_domains": PENDING, "anchor": graph, "logical_locator": str(locator),
        "case_semantic_sha256": digest(encode(case)), "request_sha256": digest(encode(request)),
        "neutral_document_sha256": digest(encode(ToData(document))), "expectations": expected,
        "typed_owners": observed, "changed_streams": changed,
        "baseline_sha256": digest(baseline.BytesValue), "candidate_sha256": digest(candidate.BytesValue),
        "candidate_bytes": len(candidate.BytesValue), "artifact_base64": b64encode(candidate.BytesValue).decode("ascii"),
        "runtime_input_or_cad_access_attempts": 0, "native_acceptance": False, "full_source_preserved": False,
    }


def main():
    parser = ArgumentParser()
    parser.add_argument("sdk", type=Path)
    args = parser.parse_args()
    root = args.sdk.resolve()
    require(Path(__file__).resolve().is_relative_to(root), "worker must run inside its frozen source root")
    sys.path[:0] = [str(root / name) for name in (
        "re/tooling/sw2026/materials", "re/tooling/sw2026/body/NamedOutput/AnchoredProof/Harness01",
        "re/tooling/sw2026", "src", ".",
    )]
    import BuildAssignedMaterialProbe as physical
    import SdkBlindPartChecks
    from CheckAnchoredGraph import check_graph

    for module in (
        "convert.adapters.solidworks.Archive.Construction.BodyNames.MakeAnchorBase",
        "convert.adapters.solidworks.Core.Preparation.BindPartIntent",
        "convert.adapters.solidworks.Core.Preparation.MakePartRecipe",
        "convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink",
        "interchange.materials.MaterialRecord", "interchange.serialization.EncodeData",
        "interchange.document.Models.DocumentProvenance", "interchange.document.Validation.DocumentValidate",
        "interchange.document.Behavior.DocumentIo", "interchange.brep.Validation.BrepValidate",
    ):
        importlib.import_module(module)
    for name in ("ascii", "latin-1", "utf-8", "utf-16-le", "utf-16-be"):
        lookup(name)
    request = json.load(sys.stdin, object_pairs_hook=pairs)
    denied = []

    def guard(event, _):
        if event == "ctypes.dlopen" or event.startswith("socket."):
            denied.append(event)
            raise PermissionError("material construction attempted native library or network access")

    sys.addaudithook(guard)
    physical.AUDIT.BeginBuild()
    answer = prepare(request, physical, check_graph)
    require(not denied and not physical.AUDIT.DeniedReads, "construction attempted runtime input or CAD access")
    sys.stdout.buffer.write(encode(answer))


if __name__ == "__main__":
    main()
