from base64 import b64decode, b64encode
from codecs import lookup
from dataclasses import replace
from hashlib import sha256
from json import dumps, load
from pathlib import Path
import sys
from xml.etree.ElementTree import fromstring

root = Path(sys.argv[1]).resolve()
mode = sys.argv[2]
sys.path[:0] = [str(root), str(root / "src"), str(Path(__file__).resolve().parent)]

from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

audit = BuildAudit(root / "re/tooling/sw2026/serial/defs")
sys.addaudithook(audit.InspectEvent)

from convert.adapters.solidworks.Archive.Construction.Part.MakeBlindPart import MakeBlindPart
from convert.adapters.solidworks.Archive.Construction.Part.MakePocketPart import MakePocketPart
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectPocket import ProjectPocket
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from interchange.document.Models.DocumentModel import CadDocument
from interchange.document.Validation.DocumentAssemblyValidate import GetAssemblyErrs
from interchange.document.Validation.DocumentFeatureValidate import GetFeatureErrs
from interchange.document.Validation.DocumentReferenceValidate import GetRefErrors
from interchange.serialization.Deserialize import FromData

if mode == "audit":
    from SdkNativeRoundTrips import roundtrips


def require(condition, label):
    if not condition:
        raise ValueError(label)


def read_depth(feature, operation, reversal, expected):
    fields = feature.FieldsValue
    end = ArchiveNode.RequireNode(fields["f818"])
    require(fields["f810"] == operation and end.FieldsValue["f08"] == 1
            and end.FieldsValue["f0c"] == 0 and end.FieldsValue["f8c"] == reversal,
            "ordinary blind extrusion operation or direction differs")
    display = ArchiveNode.RequireNode(end.FieldsValue["f18"])
    handles = display.FieldsValue["f850"]
    require(display.FieldsValue["n850"] == len(handles) == 1, "depth display lost its real handle")
    handle = ArchiveNode.RequireNode(handles[0]["o"])
    dimension = ArchiveNode.RequireNode(handle.FieldsValue["ff0"])
    parameter = ArchiveNode.RequireNode(dimension.FieldsValue["f28"])
    require(ReadNodeName(parameter) == "D1" and parameter.FieldsValue["f58"] == expected,
            "depth parameter differs from its neutral owner")
    return dimension.FieldsValue["f50"]


def check_history(features, plan):
    boss_profile, boss, profile, cut = features[-4:]
    expected = (
        ("moProfileFeature_c", plan.BossValue.SketchName),
        ("moExtrusion_c", plan.BossValue.FeatureName),
        ("moProfileFeature_c", plan.SketchName),
        ("moICE_c", plan.FeatureName),
    )
    for feature, (cls, name) in zip((boss_profile, boss, profile, cut), expected, strict=True):
        require(feature.ClassValue.NameValue == cls and ReadNodeName(feature) == name,
                "features lost their actual ordered class or name")
    for extrude, sketch in ((boss, boss_profile), (cut, profile)):
        require(extrude.FieldsValue["f60"]["list"]["items"][0]["o"] is sketch,
                "extrusion dependency lost the actual sketch identity")
    boss_depth = read_depth(boss, -1, 0, plan.BossValue.DepthValue)
    cut_depth = read_depth(cut, 1, 1, plan.EndValue.DepthValue)
    require(boss_depth != cut_depth, "owned depth identities must be independent")
    fields = cut.FieldsValue
    require(fields["f28"] & 0x201CA == 0x201CA
            and all(fields[key] == 0 for key in ("f544", "has_f528", "has_f530", "has_f548", "has_f4c0"))
            and fields["f538"] is None, "fresh all-bodies cut acquired unmodeled body or chooser state")
    end = fields["f818"].FieldsValue
    require(end["f20"] is None and end["fc8"] is None and end["fd0"] is None
            and end["f140"].FieldsValue["t"] == 0,
            "ordinary cut acquired an alternate live end or start owner")
    return {"boss": boss_depth, "cut": cut_depth}


def check_keywords(archive, features, plan, units):
    rows = list(fromstring(archive.require("swXmlContents/KeyWords")[1:]))[-4:]
    for row, node in zip(rows, features[-4:], strict=True):
        require(row.attrib["id"] == str(node.FieldsValue["f08"])
                and row.attrib["Name"] == ReadNodeName(node), "keyword identity differs from generated history")
    require([row.tag for row in rows] == ["Sketch", "Extrusion", "Sketch", "Extrusion"]
            and "Type" not in rows[-1].attrib and rows[-1].attrib["DissectableChildren"] == rows[-2].attrib["id"],
            "cut keywords lost their actual dependency")
    scale = {"mm": 0.001, "m": 1.0, "in": 0.0254}[units]
    expected = [(rows[1], plan.BossValue.DepthValue), (rows[3], plan.EndValue.DepthValue)]
    if plan.RadialMode is None:
        require(len(rows[2]) == 0, "undimensioned circle acquired an authored radial driver")
    else:
        expected.append((rows[2], plan.CircleValue.RadiusValue * (2 if plan.RadialMode == "diameter" else 1)))
    for row, length in expected:
        require(len(row) == 1 and row[0].tag == "Dimension" and row[0].attrib["Name"] == "D1"
                and abs(float(row[0].text) * scale - length) <= 1e-13, "keyword dimensional value differs")


def compare_boss(document, candidate, inputs):
    boss = document.feature_timeline[0]
    original = replace(
        document,
        sketches=document.sketches[:1],
        feature_timeline=document.feature_timeline[:1],
        parameters=tuple(parameter for parameter in document.parameters if parameter.owner_id == boss.id),
        bodies=(replace(document.bodies[0], final_feature_id=boss.id),),
    )
    baseline = MakeBlindPart(original, inputs)
    path = "Contents/Config-0-ResolvedFeatures"
    before = len(baseline.StreamsValue[path])
    after = len(candidate.StreamsValue[path])
    require(len(candidate.ResolvedValue.RootsValue) == len(baseline.ResolvedValue.RootsValue) + 2
            and candidate.ResolvedValue.MapValue.CounterValue > baseline.ResolvedValue.MapValue.CounterValue
            and after > before, "neutral cut failed to extend the actual resolved topology and length")
    return {"boss_resolved_bytes": before, "pocket_resolved_bytes": after,
            "boss_map_counter": baseline.ResolvedValue.MapValue.CounterValue,
            "pocket_map_counter": candidate.ResolvedValue.MapValue.CounterValue}


def main(request):
    document = FromData(request["document"])
    require(type(document) is CadDocument, "worker expects a portable CAD document")
    plan = ProjectPocket(document)
    if mode == "build":
        inputs = MakePartRecipe(plan.BossValue, request["written_at"])
        inputs = replace(inputs, OutputValue=replace(inputs.OutputValue, PathName=request["native_path"]))
        candidate = MakePocketPart(document, inputs)
        require(candidate.CutValue is not None, "complete part lost its real cut graph")
        require(candidate.ResolvedValue.RootsValue[-1] is candidate.CutValue.FeatureValue,
                "complete resolved history lost its actual cut identity")
        identities = check_history(candidate.ResolvedValue.RootsValue, plan)
        topology = compare_boss(document, candidate, inputs)
        streams = {name: {"bytes": len(data), "sha256": sha256(data).hexdigest()}
                   for name, data in candidate.StreamsValue.items()}
        container = candidate.BytesValue
    elif mode == "audit":
        container = b64decode(request["generated"], validate=True)
        archive = SldprtArchive.from_bytes(container)
        link, _, _, _, streams = roundtrips(archive, False)
        identities = check_history(link.ResolvedValue.RootsValue, plan)
        check_keywords(archive, link.ResolvedValue.RootsValue, plan, document.units)
        require(BuildSldprt({row.name: row.data for row in archive.records}, FormatVersion=4) == container,
                "complete container repack differs")
    else:
        raise ValueError("expected build or audit")
    research_modules = sorted(name for name, module in tuple(sys.modules.items())
                              if name not in ("__main__", "SdkNativeRoundTrips")
                              and str(getattr(module, "__file__", "")).startswith(str(root / "re") + "/"))
    require(not audit.DeniedReads and not research_modules, "SDK runtime used file or research inputs")
    result = {"passed": True, "phase": mode, "bytes": len(container), "sha256": sha256(container).hexdigest(),
              "streams": streams, "depth_ids": identities, "runtime_input_file_reads": len(audit.DeniedReads),
              "sdk_runtime_research_imports": len(research_modules), "public_writer_qualified": False}
    if mode == "build":
        result["history_topology_comparison"] = topology
        result["generated"] = b64encode(container).decode("ascii")
    return result


codecs = tuple(lookup(name) for name in ("utf-16-le", "utf-8", "latin-1"))
request = load(sys.stdin)
audit.BeginBuild()
print(dumps(main(request), sort_keys=True, allow_nan=False))
