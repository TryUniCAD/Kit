from base64 import b64decode, b64encode
from codecs import lookup
from dataclasses import replace
from hashlib import sha256
from math import isclose, pi
from pathlib import Path
from struct import unpack
from xml.etree.ElementTree import fromstring
import json
import sys

ROOT = Path(sys.argv[1])
sys.path[:0] = [str(ROOT / "src"), str(ROOT), str(ROOT / "re/tooling/sw2026")]

from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

AUDIT = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")
sys.addaudithook(AUDIT.InspectEvent)

from SdkBlindPartChecks import name, node, require
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
from convert.adapters.solidworks.Archive.CmgrHeader.ReadMgrHeader import ReadMgrHeader
from convert.adapters.solidworks.Archive.CmgrHeader.WriteMgrHeader import WriteMgrHeader
from convert.adapters.solidworks.Archive.Config.MakeLinkContext import MakeLinkContext
from convert.adapters.solidworks.Archive.Config.ReadConfigMut import ReadConfigMut
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Construction.Metadata.FrameKeywords import FrameKeywords
from convert.adapters.solidworks.Archive.Construction.Part.MakeCirclePart import MakeCirclePart
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectCircle import ProjectCircle
from convert.adapters.solidworks.Archive.Definition.ReadModelDef import ReadModelDef
from convert.adapters.solidworks.Archive.Definition.WriteModelDef import WriteModelDef
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
from convert.adapters.solidworks.Archive.History.ReadHistMut import ReadHistMut
from convert.adapters.solidworks.Archive.History.WriteHistMut import WriteHistMut
from convert.adapters.solidworks.Archive.Resolved.ReadResolvedMut import ReadResolvedMut
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from convert.adapters.solidworks.Core.Preparation.BindPartIntent import BindPartIntent
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from interchange.document.Validation.DocumentAssemblyValidate import GetAssemblyErrs
from interchange.document.Validation.DocumentFeatureValidate import GetFeatureErrs
from interchange.document.Validation.DocumentReferenceValidate import GetRefErrors
from interchange.Features.FeatureExtrude import ExtrudeEnd
from interchange.geometry.Models.GeometryCurves import CircleGeometry
from interchange.serialization.Deserialize import FromData

CODECS = tuple(lookup(value) for value in ("utf-16-le", "utf-8", "latin-1"))
REQUEST = json.load(sys.stdin)
AUDIT.BeginBuild()


def identity(data):
    return {"bytes": len(data), "sha256": sha256(data).hexdigest()}


def expected(document):
    sketch, feature = document.sketches[0], document.feature_timeline[0]
    support = document.support_planes[0]
    definition = feature.definition
    circle = sketch.entities[0].geometry
    require(type(circle) is CircleGeometry and document.units == "mm", "expected authored millimetre circle")
    radial = next(row for row in document.parameters if row.owner_id == sketch.id)
    depths = {row.name: row for row in document.parameters if row.owner_id == feature.id}
    mode = next(row.kind for row in sketch.constraints if row.parameter_id == radial.id)
    x, y, radius = circle.center.x * 0.001, circle.center.y * 0.001, circle.radius * 0.001
    length = depths["D1"].value.value * 0.001
    second = depths["D2"].value.value * 0.001 if "D2" in depths else None
    condition = {ExtrudeEnd.KBlind: "blind", ExtrudeEnd.KMidPlane: "mid_plane",
                 ExtrudeEnd.KTwoLengths: "two_directions"}[definition.end_condition]
    frame = [[value.x, value.y, value.z] for value in
             (support.transform.x_axis, support.transform.y_axis, support.transform.z_axis)]
    normal = tuple(frame[2])
    axis = {(1, 0, 0): "x", (0, 1, 0): "y", (0, 0, 1): "z"}[normal]
    total = length + (second or 0)
    middle = 0.0 if condition == "mid_plane" else (length - (second or 0)) / 2
    if definition.reversed:
        middle = -middle
    return {
        "name": document.metadata["name"], "config": document.configurations[0].name,
        "sketch": sketch.name, "feature": feature.name, "support": support.name,
        "center_m": [x, y], "radius_m": radius, "depth_m": length, "mode": mode,
        "radial_m": radial.value.value * 0.001,
        "end_condition": condition, "reverse_direction": definition.reversed, "second_depth_m": second,
        "plane_axis": axis, "frame_columns": frame,
        "volume_m3": pi * radius ** 2 * total, "area_m2": 2 * pi * radius * (radius + total),
        "com_m": [x * u + y * v + middle * n for u, v, n in zip(*frame, strict=True)],
    }


def build(document, authored):
    plan = ProjectCircle(document)
    recipe = MakePartRecipe(plan, REQUEST["created_at"])
    candidate = MakeCirclePart(document, BindPartIntent(document, plan, recipe, recipe.OutputValue))
    sketch = candidate.ProfileValue.GeometryValue.SketchValue
    require(candidate.ResolvedValue.RootsValue[-2] is candidate.ProfileValue.ProfileValue and
            candidate.ResolvedValue.RootsValue[-1] is candidate.BossValue.FeatureValue and
            candidate.ConfigValue.RootValue is candidate.SystemValue.RootValue and
            candidate.BossValue.FeatureValue.FieldsValue["f60"]["list"]["items"][0]["o"] is candidate.ProfileValue.ProfileValue and
            sketch.FieldsValue["narcs"] == 1 and not sketch.FieldsValue["lines"],
            "generated part lost its analytic profile or owner graph")
    sketch_model = document.sketches[0]
    circle = sketch_model.entities[0]
    wrong_radius = replace(circle, geometry=replace(circle.geometry, radius=circle.geometry.radius * 2))
    cases = {
        "missing_fixed_center": replace(sketch_model, constraints=sketch_model.constraints[1:]),
        "lost_value_owner": replace(sketch_model, parameter_ids=()),
        "construction_circle": replace(sketch_model, entities=(replace(circle, construction=True),)),
        "different_radius": replace(sketch_model, entities=(wrong_radius,)),
        "open_loop": replace(sketch_model, closed_profile_entity_ids=()),
        "unknown_relation_payload": replace(sketch_model, constraints=(replace(sketch_model.constraints[0], attributes={"extra": True}), sketch_model.constraints[1])),
    }
    rejected = []
    for key, variant in cases.items():
        try:
            MakeCirclePart(replace(document, sketches=(variant,)), recipe)
        except (ValueError, TypeError, KeyError) as error:
            rejected.append({"case": key, "reason": str(error)})
        else:
            raise ValueError("unsupported circle was accepted: " + key)
    return {
        **identity(candidate.BytesValue), "blob": b64encode(candidate.BytesValue).decode("ascii"),
        "streams": {key: identity(value) for key, value in candidate.StreamsValue.items()},
        "dimensions": authored, "rejections": rejected, "stored_self_path": recipe.OutputValue.PathName,
    }


def check_profile(profile, root, boss, authored):
    fields = node(profile.FieldsValue["pd_f80"], "sgSketch").FieldsValue
    require(fields["npoints"] == 2 and fields["narcs"] == 1 and not fields["lines"],
            "typed circle lost the analytic rows")
    center, seam = (row["point"] for row in fields["points"])
    arc = fields["arcs"][0]["arc"]
    x, y = authored["center_m"]
    radius = authored["radius_m"]
    require(center["pos"] == {"x": x, "y": y} and seam["pos"] == {"x": x + radius, "y": y} and
            [arc[key] for key in ("fc8_s", "fcc_s", "fdc_s", "fd0")] == [1, 1, 0, 1] and
            center["f20"] == arc["f20"] == 1 and seam["f20"] == 0,
            "circle points, closure or actual relation counts differ")
    dims = fields["dims"]
    require(dims["ng1"] == dims["nlog1"] == 1 and not any(dims[key] for key in ("val_g2", "val_g3", "log_g2", "log_g3")),
            "circle sketch gained an unsupported constraint group")
    value = node(dims["val_g1"][0]["d"], "sgCircleDim").FieldsValue
    logical = dims["log_g1"][0]["d"]
    display = node(dims["f118"].FieldsValue["items"][0]["o"], "moDisplayRadialDim_c").FieldsValue
    handle = node(display["f850"][0]["o"], "moSkDimHandleRadial_c").FieldsValue
    parameter = node(value["f28"], "moLengthParameter_c")
    diameter = authored["mode"] == "diameter"
    require(value["f80"] == (15 if diameter else 3) and display["f6a0"]["f10"] == (17 if diameter else 20) and
            logical["f80"] == 17 and node(logical["h1"], "sgPointHandle").FieldsValue["idx"] == 0 and
            node(value["h1"], "sgArcHandle").FieldsValue["idx"] == 0 and handle["ff0"] is profile.FieldsValue["pd_f80"] and
            handle["ff8"] == 0 and name(parameter) == "D1" and
            isclose(parameter.FieldsValue["f58"], authored["radial_m"], rel_tol=1e-13) and
            unpack("<d", display["f5b0"]["data"])[0] == parameter.FieldsValue["f58"],
            "radial display or driving owners disagree with the model")
    support = node(profile.FieldsValue["pd_f78"], "moCompRefPlane_c")
    require(node(support.FieldsValue["f58"], "moUnitComponent_c").FieldsValue["owner"] is root and
            boss.FieldsValue["f60"]["list"]["items"][0]["o"] is profile,
            "decoded native support ownership or extrusion link differs")
    frame = profile.FieldsValue["pd_ff0"]
    rotation = [value for row in zip(*authored["frame_columns"], strict=True) for value in row]
    if authored["plane_axis"] == "z":
        require(frame["has_matrix"] == 0, "front plane acquired a rotation matrix")
    else:
        require(frame["has_matrix"] == 1 and [frame["f08"][f"m{index}"] for index in range(9)] == rotation,
                "typed plane frame differs from the actual neutral transform")
    return {"fixed_center": True, "owned_radial_parameter": True, "closed_circle": True,
            "display_matches_parameter": True, "actual_support_frame": True}


def check_boss_end(boss, authored):
    end = node(boss.FieldsValue["f818"], "moEndSpec_c").FieldsValue
    require([end[key] for key in ("f08", "f0c", "f10", "f88", "f8c")]
            == [int(authored["end_condition"] != "two_directions"),
                6 if authored["end_condition"] == "mid_plane" else 0,
                0, 0, int(authored["reverse_direction"])],
            "typed end specification differs from the neutral conditions")
    require(node(end["f140"], "moFromEndSpec_c").FieldsValue["t"] == 0,
            "typed boss unexpectedly gained a start reference")
    facts = []
    second = authored["second_depth_m"]
    for ordinal, (field, value) in enumerate((("f18", authored["depth_m"]),
                                              ("f20", authored["depth_m"] if second is None else second)), 1):
        display = node(end[field], "moDisplayDistanceDim_c").FieldsValue
        require(display["n850"] == len(display["f850"]) == 1, "end length lost its unique dimension handle")
        handle = node(display["f850"][0]["o"], "moFeatureDimHandle_c").FieldsValue
        dimension = node(handle["ff0"], "ParallelPlaneDistanceDim_c").FieldsValue
        parameter = node(dimension["f28"], "moLengthParameter_c")
        require(dimension["f50"] == 20 + ordinal and parameter.FieldsValue["f08"] == -1 and
                name(parameter) == f"D{ordinal}" and parameter.FieldsValue["f58"] == value,
                "the end length does not retain its actual driving value and identity")
        facts.append({"name": name(parameter), "length_m": value, "id": dimension["f50"],
                      "active": ordinal == 1 or second is not None})
    return facts


def prepare(authored):
    built = REQUEST["build"]
    blob = b64decode(built["blob"], validate=True)
    require(identity(blob) == {"bytes": built["bytes"], "sha256": built["sha256"]}, "artifact differs")
    streams = {row.name: row.data for row in SldprtArchive.from_bytes(blob).records}
    require({key: identity(value) for key, value in streams.items()} == built["streams"] and len(streams) == 10,
            "stream custody differs")
    header = ReadHeaderGraph(streams["Contents/Config-0-ModelHeader"], 19000)
    config = ReadConfigMut(streams["Contents/Config-0"], 19000, header)
    cmgr = ReadCmgrMut(streams["Contents/CMgr"], 19000)
    context = MakeLinkContext(config, cmgr)
    resolved = ReadResolvedMut(streams["Contents/Config-0-ResolvedFeatures"], 19000, config.MapValue, context)
    profile, boss = resolved.RootsValue[-2:]
    require(len(resolved.RootsValue) == 19 and name(profile) == authored["sketch"] and name(boss) == authored["feature"] and
            name(config.RootValue) == authored["name"] and name(cmgr.RootValue.FieldsValue["f360"]) == authored["config"],
            "decoded document names differ from their actual neutral owners")
    facts = check_profile(profile, config.RootValue, boss, authored)
    depths = check_boss_end(boss, authored)
    config_bytes, repeated = WriteConfigMut(config.RootValue, 19000, header)
    keywords = fromstring(streams["swXmlContents/KeyWords"][1:])
    dims = [[("D1", authored["radial_m"])], [("D1", authored["depth_m"])]]
    if authored["second_depth_m"] is not None:
        dims[1].append(("D2", authored["second_depth_m"]))
    require(keywords.attrib["Name"] == authored["name"] and
            [row.tag for row in keywords[-2:]] == ["Sketch", "Extrusion"] and
            all(len(row) == len(group) and
                all(dimension.attrib["Name"] == name_value and
                    isclose(float(dimension.text) * 0.001, length, rel_tol=1e-13)
                    for dimension, (name_value, length) in zip(row, group, strict=True))
                for row, group in zip(keywords[-2:], dims, strict=True)),
            "keyword dimensions lost their actual separate owners and driving lengths")
    roundtrip = {
        "Header2": WriteHeadGraph(ReadHeaderGraph(streams["Header2"], 19000), 19000),
        "Contents/Config-0-ModelHeader": WriteHeadGraph(header, 19000),
        "Contents/Config-0": config_bytes,
        "Contents/CMgr": WriteCmgrMut(cmgr.RootValue, 19000),
        "Contents/CMgrHdr2": WriteMgrHeader(ReadMgrHeader(streams["Contents/CMgrHdr2"], 19000).RootValue, 19000)[0],
        "Contents/Config-0-ResolvedFeatures": WriteResolMut(resolved.RootsValue, resolved.ExtraFields, 19000, repeated.MapValue, context)[0],
        "Contents/Definition": WriteModelDef(ReadModelDef(streams["Contents/Definition"], 19000).GraphValue).OutputValue,
        "swXmlContents/KeyWords": FrameKeywords(keywords, False),
    }
    for key in ("_MO_VERSION_19000/Biography", "_MO_VERSION_19000/History"):
        roundtrip[key] = WriteHistMut(ReadHistMut(streams[key], 19000).RootValue, 19000)[0]
    require(roundtrip == streams and BuildSldprt(streams, FormatVersion=4) == blob,
            "roundtrip changed a stream or container")
    return {"artifact": identity(blob), "streams": {key: {**identity(value), "byte_identity": True} for key, value in roundtrip.items()},
            "exact_repacked_archive": True, "typed_geometry": facts, "native_depths": depths, "dimensions": authored}


document_value = FromData(REQUEST["document"])
authored_values = expected(document_value)
if sys.argv[2] == "build":
    result = build(document_value, authored_values)
elif sys.argv[2] == "prepare":
    result = prepare(authored_values)
else:
    raise ValueError("expected build or prepare")
research = [key for key, module in sys.modules.items()
            if str(getattr(module, "__file__", "")).startswith(str(ROOT / "re") + "/")
            and key not in ("__main__", "SdkBlindPartChecks")]
require(not research and not AUDIT.DeniedReads, "circle SDK used research implementation or runtime inputs")
print(json.dumps({**result, "passed": True, "runtime_input_file_reads": 0,
                  "sdk_runtime_research_imports": 0, "module_reads": len(AUDIT.ModuleReads)}, sort_keys=True, allow_nan=False))
