from base64 import b64encode
from codecs import lookup
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(HERE.parent)]

from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

audit = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")
sys.addaudithook(audit.InspectEvent)

from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Config.MakeLinkContext import MakeLinkContext
from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import SelfFileInput
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import PersistentIds
from convert.adapters.solidworks.Archive.Construction.Part.CheckPartInput import CheckPartInput
from convert.adapters.solidworks.Archive.Construction.Part.FinishBlindMut import FinishBlindMut
from convert.adapters.solidworks.Archive.Construction.Part.MakeBlindPart import MakeBlindByPlan
from convert.adapters.solidworks.Archive.Construction.Part.MakePartBaseMut import MakePartBaseMut
from convert.adapters.solidworks.Archive.Construction.Part.MakePartProfMut import MakePartProfMut
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectPlain import ProjectPlain
from convert.adapters.solidworks.Archive.Construction.System.MakeDefaultData import MakeDefaultData
from convert.adapters.solidworks.Archive.Construction.System.PrincipalFrame import PrincipalFrame
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName, RequireNode
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from interchange.document.Validation.DocumentAssemblyValidate import GetAssemblyErrs
from interchange.document.Validation.DocumentFeatureValidate import GetFeatureErrs
from interchange.document.Validation.DocumentReferenceValidate import GetRefErrors
from interchange.serialization.Deserialize import FromData

from MakePatternPrincipalDisplay import point, put_principal_displays_mut
from PatternHingeGeometry import ORIGIN


LINKED = "Contents/Config-0-ResolvedFeatures"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def coordinates(data):
    return tuple(data[axis] for axis in "xyz")


def independent_part(document, plan, settings, sized):
    if not sized:
        return MakeBlindByPlan(document, settings, plan), {}
    CheckPartInput(document, settings, plan)
    allocator = PersistentIds()
    system = MakePartBaseMut(settings, plan, allocator)
    profile = MakePartProfMut(system, settings, plan, allocator)
    displays = put_principal_displays_mut(system, (ORIGIN, (plan.WidthValue, plan.HeightValue, plan.DepthValue)))
    return FinishBlindMut(system, profile, settings, plan, allocator), displays


def typed_replay(candidate, predicted):
    archive = SldprtArchive.from_bytes(candidate.BytesValue)
    require(archive.streams == candidate.StreamsValue and len(archive.streams) == 10,
            "expected complete shared ten-stream output")
    link = ReadNativeLink(archive, 0)
    scope = MakeLinkContext(link.ConfigValue, ReadCmgrMut(archive.require("Contents/CMgr"), 19000))
    resolved = link.ResolvedValue
    repeated, repeated_graph = WriteResolMut(resolved.RootsValue, resolved.ExtraFields, 19000, link.ConfigValue.MapValue, scope)
    require(repeated == archive.require(LINKED) and repeated_graph.MapValue == resolved.MapValue,
            "typed linked round trip changed the archive or map")
    displays = {}
    for axis, role in (("y", "Top Plane"), ("x", "Right Plane")):
        (node,) = [value for value in resolved.RootsValue if value.ClassValue.NameValue == "moRefPlane_c" and ReadNodeName(value) == role]
        native = RequireNode(node.FieldsValue["f6f8"], "moDefaultRefPlnData_c").FieldsValue
        displays[role] = {"display_root_m": coordinates(native["display_root"]),
                          "borders_m": tuple(native[f"b{i}"] for i in range(4)),
                          "name_location_m": coordinates(node.FieldsValue["f6c0"])}
        defaults = MakeDefaultData(axis, PrincipalFrame(axis)).FieldsValue
        native.update({name: defaults[name] for name in ("display_root", "b0", "b1", "b2", "b3")})
        node.FieldsValue["f6c0"] = point(ORIGIN)
    expected = predicted or {name: {"display_root_m": ORIGIN, "borders_m": (0.0,) * 4, "name_location_m": ORIGIN}
                             for name in displays}
    require(displays == expected, "generated principal presentation changed on typed read")
    defaulted, defaulted_graph = WriteResolMut(resolved.RootsValue, resolved.ExtraFields, 19000, link.ConfigValue.MapValue, scope)
    require(defaulted_graph.MapValue == resolved.MapValue, "resetting only geometric presentation changed the map")
    return displays, [link.ConfigValue.MapValue.CounterValue, resolved.MapValue.CounterValue], sha256(defaulted).hexdigest()


def main():
    for name in ("utf-16-le", "utf-8", "latin-1"):
        lookup(name)
    request = json.load(sys.stdin)
    audit.BeginBuild()
    require(type(request) is dict and set(request) == {"document", "path", "epoch", "sized"}
            and type(request["sized"]) is bool, "expected only authored neutral document, locator, clock and one presentation mode")
    document = FromData(request["document"])
    plan = ProjectPlain(document)
    require(plan.AxisValue == "z" and not plan.Reversed and min(x for x, _ in plan.VerticesValue) == 0.0
            and min(y for _, y in plan.VerticesValue) == 0.0, "expected a forward Front origin plate")
    recipe = MakePartRecipe(plan, request["epoch"])
    settings = replace(recipe, OutputValue=SelfFileInput(request["path"], request["epoch"]))
    candidate, predicted = independent_part(document, plan, settings, request["sized"])
    displays, counters, without_local_sizing = typed_replay(candidate, predicted)
    print(json.dumps({"passed": True, "sized": request["sized"], "bytes": len(candidate.BytesValue),
                      "sha256": sha256(candidate.BytesValue).hexdigest(),
                      "streams": {name: {"bytes": len(data), "sha256": sha256(data).hexdigest()}
                                  for name, data in candidate.StreamsValue.items()},
                      "map_counters": counters, "displays": displays, "unsized_resolved_sha256": without_local_sizing,
                      "runtime_input_reads": len(audit.DeniedReads), "native_acceptance": False,
                      "blob": b64encode(candidate.BytesValue).decode("ascii")}, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
