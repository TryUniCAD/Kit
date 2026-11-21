from codecs import lookup
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
from struct import pack
import sys


HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(HERE.parent)]

from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

audit = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")
sys.addaudithook(audit.InspectEvent)

from convert.adapters.solidworks.Archive.Config.MakeLinkContext import MakeLinkContext
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Construction.Extrusion.MakeBlindMut import MakeBlindMut
from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import SelfFileInput
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import PersistentIds
from convert.adapters.solidworks.Archive.Construction.Part.CheckPartInput import CheckPartInput
from convert.adapters.solidworks.Archive.Construction.Part.MakePartBaseMut import MakePartBaseMut
from convert.adapters.solidworks.Archive.Construction.Part.MakePartProfMut import MakePartProfMut
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectPlain import ProjectPlain
from convert.adapters.solidworks.Archive.Construction.Part.SelectBlindEnd import SelectBlindEnd
from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import DatumTime
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName, RequireNode
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from interchange.document.Validation.DocumentAssemblyValidate import GetAssemblyErrs
from interchange.document.Validation.DocumentFeatureValidate import GetFeatureErrs
from interchange.document.Validation.DocumentReferenceValidate import GetRefErrors
from interchange.serialization.Deserialize import FromData

from MakePatternHingeAxis import make_hinge_mut
from PatternHingeGeometry import AXIS, ORIGIN
from PatternHingeWire import read_axis_stream, write_roots


def require(value, message):
    if not value:
        raise ValueError(message)


def coords(value):
    return tuple(value[axis] for axis in "xyz")


def bind_readback(axis, roots, system, config, headers, shape):
    feature = RequireNode(axis, "moRefAxis_c").FieldsValue
    data = RequireNode(feature["f700"], "moPlaneInterAxisData_c").FieldsValue
    views = [RequireNode(data[key], "moPlaneRef_w").FieldsValue for key in ("f80", "f88")]
    linked_ids, component_vertices = [], []
    for name, key, kind in zip(("Top Plane", "Right Plane"), ("y", "x"), (2, 1), strict=True):
        plane_key = system.SystemValues.PlaneValues[key].FieldsValue["f08"]
        (datum,) = [node for node in roots if node is not None and node.FieldsValue.get("f08") == plane_key]
        require(ReadNodeName(datum) == name, "exact canonical support is outside the generated graph")
        expected = RequireNode(datum.FieldsValue["f6f8"], "moDefaultRefPlnData_c").FieldsValue
        view = views[len(linked_ids)]
        selection = RequireNode(view["f58"], "moCompRefPlane_c").FieldsValue
        component = RequireNode(selection["f58"], "moUnitComponent_c")
        require(selection["ff0"] == {"f00": plane_key, "f08": DatumTime(headers[0], plane_key)}
                and selection["f100"] == kind and selection["ff8"] is None and view["f60"] is None
                and view["f68"] == 1 and view["f08"] == headers[0].FieldsValue["f40"]
                and view["f0c"] == system.ConfigValues[0].FieldsValue["f08"]
                and component.FieldsValue["owner"] is config.RootValue and component is not config.RootValue.FieldsValue["f990"]
                and component.FieldsValue["has_ext"] == 0, "generated axis lost linked actual selection")
        require(all(view[field] == expected[f"b{i}"] for i, field in enumerate(("fb0", "fb8", "fc0", "fc8")))
                and view["fd0"] == expected["root"] and view["fe8"] == expected["normal"] and view["f100"] == expected["f20"],
                "generated axis wrapper lost the actual selected presentation and frame")
        linked_ids.append(plane_key)
        component_vertices.append(component)
    require(component_vertices[0] is not component_vertices[1], "actual selected references need distinct component ownership")
    center = shape[2] / 2.0
    half = shape[2] * 0.5 + shape[2] * 0.05
    start, finish = (0.0, 0.0, center + half), (0.0, 0.0, center - half)
    require(pack("<8d", *coords(data["f18"]), *coords(data["f30"]), data["f08"], data["f10"])
            == pack("<8d", *start, *finish, start[2], -finish[2])
            and coords(data["f50"]) == AXIS and coords(data["f68"]) == ORIGIN and feature["f6c0"] == data["f18"],
            "finite signed endpoint and presentation identities changed on readback")
    return {"axis_id": feature["f08"], "support_ids_in_wire_order": linked_ids, "start_m": start, "finish_m": finish}


def crosses_rejected(axis, roots, system, config, headers, shape):
    data = axis.FieldsValue["f700"].FieldsValue
    left, right = data["f80"], data["f88"]
    left_ref, right_ref = (node.FieldsValue["f58"].FieldsValue for node in (left, right))
    probes = (("crossed_order", data, "f80", right), ("aliased_selected_component", right_ref, "f58", left_ref["f58"]))
    result = {}
    for label, fields, key, mutant in probes:
        prior = fields[key]
        fields[key] = mutant
        try:
            bind_readback(axis, roots, system, config, headers, shape)
        except ValueError as error:
            result[label] = str(error)
        finally:
            fields[key] = prior
    require(len(result) == len(probes), "one crossed finite hinge owner survived strict readback")
    return result


def main():
    for encoding in ("utf-16-le", "utf-8", "latin-1"):
        lookup(encoding)
    request = json.load(sys.stdin)
    audit.BeginBuild()
    require(type(request) is dict and set(request) == {"document", "path", "epoch", "axis_name"},
            "finite hinge research requires only authored geometry, output locator, clock and name")
    document = FromData(request["document"])
    plan = ProjectPlain(document)
    require(plan.AxisValue == "z" and not plan.Reversed and min(x for x, _ in plan.VerticesValue) == 0.0
            and min(y for _, y in plan.VerticesValue) == 0.0, "finite hinge prototype requires a forward Front origin plate")
    recipe = MakePartRecipe(plan, request["epoch"])
    settings = replace(recipe, OutputValue=SelfFileInput(request["path"], request["epoch"]))
    CheckPartInput(document, settings, plan, (request["axis_name"],))
    allocator = PersistentIds()
    system = MakePartBaseMut(settings, plan, allocator)
    profile = MakePartProfMut(system, settings, plan, allocator)
    boss = MakeBlindMut(plan.FeatureName, system.RootValue, profile, SelectBlindEnd(plan, None, None), settings.TargetValue,
                        allocator, settings.DesignIntent, settings.SelectedLeader)
    shape = (plan.WidthValue, plan.HeightValue, plan.DepthValue)
    axis, headers = make_hinge_mut(system, settings, allocator, request["axis_name"], (ORIGIN, shape))
    roots = (*system.FeatureValues, profile.ProfileValue, boss.FeatureValue)
    config_bytes, config = WriteConfigMut(system.RootValue, 19000, headers[0])
    scope = {"model_is_part": 1, "model_compressed_stream": 1, "cmgr_f658": system.ManagerValue.FieldsValue["f658"]}
    plain, plain_map = write_roots(roots, config.MapValue, scope)
    common, common_graph = WriteResolMut(roots, None, 19000, config.MapValue, scope)
    require(plain == common and plain_map == common_graph.MapValue, "existing ordinary SDK sections must stay identical")
    resolved, emitted = write_roots((*roots, axis), config.MapValue, scope)
    decoded, loaded = read_axis_stream(resolved, config.MapValue, scope)
    repeated, repeat_map = write_roots(decoded, config.MapValue, scope)
    require(repeated == resolved and repeat_map == loaded and emitted.CounterValue == loaded.CounterValue,
            "finite hinge graph lost byte or linked map equality")
    measured = bind_readback(decoded[-1], decoded, system, config, headers, shape)
    refusals = crosses_rejected(decoded[-1], decoded, system, config, headers, shape)
    require(measured["axis_id"] + 1 == headers[0].FieldsValue["f08"] == headers[1].FieldsValue["f08"]
            and measured["axis_id"] == system.ConfigValues[0].FieldsValue["f85c"], "finite hinge allocation is not shared")
    print(json.dumps({"completed_model_fragment": True, "native_acceptance": False, "container_written": False,
                      "config_sha256": sha256(config_bytes).hexdigest(), "resolved_sha256": sha256(resolved).hexdigest(),
                      "resolved_bytes": len(resolved), "roots": len(decoded), "model_bounds_m": [ORIGIN, shape],
                      "map_counters": [config.MapValue.CounterValue, loaded.CounterValue], "axis": measured, "refusals": refusals,
                      "guarded_runtime_reads": len(audit.DeniedReads)}, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
