from base64 import b64encode
from codecs import lookup
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(sys.argv[1]).resolve()
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(ROOT / "re/tooling/sw2026")]

from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

AUDIT = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")
sys.addaudithook(AUDIT.InspectEvent)

from SdkBlindPartSettings import settings
from SdkRectDimRejects import input_value
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
from convert.adapters.solidworks.Archive.Config.MakeLinkContext import MakeLinkContext
from convert.adapters.solidworks.Archive.Config.Material.MatTypes import KDensityClass, KMaterialClass
from convert.adapters.solidworks.Archive.Config.ReadConfigMut import ReadConfigMut
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import PersistentIds
from convert.adapters.solidworks.Archive.Construction.Part.CheckPartInput import CheckPartInput
from convert.adapters.solidworks.Archive.Construction.Part.FinishBlindMut import FinishBlindMut
from convert.adapters.solidworks.Archive.Construction.Part.MakePartBaseMut import MakePartBaseMut
from convert.adapters.solidworks.Archive.Construction.Part.MakePartProfMut import MakePartProfMut
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectRectDims import ProjectRectDims
from convert.adapters.solidworks.Archive.Construction.Presentation.MakeModelVisual import MakeModelVisual
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.MakeRectDimsMut import MakeRectDimsMut
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.MakeSketchKeys import MakeSketchKeys
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Resolved.ReadResolvedMut import ReadResolvedMut
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Container.Container import SldprtArchive
from interchange.document.Models.DocumentModel import CadDocument
from interchange.document.Validation.DocumentAssemblyValidate import GetAssemblyErrs
from interchange.document.Validation.DocumentFeatureValidate import GetFeatureErrs
from interchange.document.Validation.DocumentReferenceValidate import GetRefErrors
from interchange.serialization.Deserialize import FromData

MODES = {
    "unassigned": (False, False, False),
    "part": (True, False, False),
    "configuration": (False, True, False),
    "identity": (False, False, True),
    "all": (True, True, True),
}


def require(check, message):
    if not check:
        raise ValueError(message)


def material_intent(document, assignment):
    require(type(document) is CadDocument and len(document.materials) == 1,
            "the experiment requires one actual neutral part material")
    require(set(assignment) == {"material_ref", "catalog", "catalog_id"},
            "material identity requires its explicit model reference and catalog key")
    material, = document.materials
    catalog, catalog_id = assignment["catalog"], assignment["catalog_id"]
    require(material.id == assignment["material_ref"], "material reference does not resolve")
    require(type(catalog) is str and all(
        token and token.isprintable() and "|" not in token and "/" not in token and chr(92) not in token
        for token in (catalog, material.name)
    ), "catalog and material must be distinct printable identity tokens")
    require(catalog_id is None or type(catalog_id) is int and 0 <= catalog_id < 2**31,
            "catalog identifier is absent or an explicit positive signed identifier")
    tokens = (catalog, material.name) if catalog_id is None else (catalog, material.name, str(catalog_id))
    return float(material.Density), "|".join(tokens)


def make_density(density):
    parameter = ArchiveNode(KDensityClass, {
        "f18": None, "f0c": 0, "f28": 0x40000000, "f08": -1, "f2c": 0,
        "f20": "", "f48": None, "f58": density, "f68": 0,
    })
    return ArchiveNode(KMaterialClass, {"f08": parameter})


def compose(document, inputs, dimensions, modes, density, identity):
    plan = ProjectRectDims(document)
    CheckPartInput(document, inputs, plan)
    allocator = PersistentIds()
    system = MakePartBaseMut(inputs, plan, allocator)
    profile = MakePartProfMut(system, inputs, plan, allocator)
    sketch = MakeRectDimsMut(profile, dimensions, allocator, plan.SketchDriverNames)
    root, configuration = system.RootValue.FieldsValue, system.ConfigValues[0].FieldsValue
    require(root["f1420"] is None and configuration["fc50"] == -1 and configuration["f78"] is None,
            "the ordinary unassigned constructors do not match the experimental baseline")
    part, active_density, active_identity = modes
    if part:
        root["f1420"] = make_density(density)
    if active_density:
        configuration["fc50"] = density
    if active_identity:
        visual = MakeModelVisual()
        visual.FieldsValue["f20"]["f20"] = identity
        configuration["f78"] = visual
    return FinishBlindMut(system, profile, inputs, plan, allocator,
                          MakeSketchKeys(sketch, inputs.DocumentUnits.LengthUnit))


def inspect(candidate, modes, density, identity):
    streams = SldprtArchive.from_bytes(candidate.BytesValue).streams
    require(streams == candidate.StreamsValue and "swXmlContents/MATERIALTREE" not in streams,
            "the isolated experiment must preserve generated stream ownership without material xml")
    names = ("Contents/Config-0", "Contents/CMgr", "Contents/Config-0-ResolvedFeatures")
    header = ReadHeaderGraph(streams["Contents/Config-0-ModelHeader"], 19000)
    cfg = ReadConfigMut(streams[names[0]], 19000, header)
    mgr = ReadCmgrMut(streams[names[1]], 19000)
    ctx = MakeLinkContext(cfg, mgr)
    res = ReadResolvedMut(streams[names[2]], 19000, cfg.MapValue, ctx)
    material = cfg.RootValue.FieldsValue["f1420"]
    conf = mgr.RootValue.FieldsValue["f360"]
    require(conf is mgr.RootValue.FieldsValue["f368"] is mgr.RootValue.FieldsValue["f370"]["items"][0]["o"],
            "manager lost the real active single-configuration identity")
    fields = conf.FieldsValue
    actual = (material.FieldsValue["f08"].FieldsValue["f58"] if material else None,
              fields["fc50"], fields["f78"].FieldsValue["f20"]["f20"] if fields["f78"] else None)
    part, active_density, active_identity = modes
    require(actual == (density if part else None, density if active_density else -1, identity if active_identity else None),
            "typed archive readback lost one of the independent requested owner fields")
    rebuilt = (WriteConfigMut(cfg.RootValue, 19000, header)[0],
               WriteCmgrMut(mgr.RootValue, 19000),
               WriteResolMut(res.RootsValue, res.ExtraFields, 19000, cfg.MapValue, ctx)[0])
    require(rebuilt == tuple(streams[name] for name in names), "generated linked owners fail exact typed replay")
    require(res.MapBase == cfg.MapValue.CounterValue, "config map does not continue into resolved features")
    return {"part_density": actual[0], "config_density": actual[1], "config_identity": actual[2],
            "config_map_counter": cfg.MapValue.CounterValue, "resolved_map_counter": res.MapValue.CounterValue,
            "exact_linked_streams": len(rebuilt)}


def main():
    tuple(lookup(name) for name in ("utf-16-le", "utf-8", "latin-1"))
    request = json.load(sys.stdin)
    require(set(request) == {"document", "settings", "rectangle_dimensions", "mode", "assignment"},
            "the material probe only accepts explicit neutral geometry, presentation and assignment")
    AUDIT.BeginBuild()
    document, inputs = FromData(request["document"]), settings(request["settings"])
    dimensions = input_value(request["rectangle_dimensions"], inputs)
    modes = MODES[request["mode"]]
    density, identity = material_intent(document, request["assignment"])
    geometry_document = replace(document, materials=())
    candidate = compose(geometry_document, inputs, dimensions, modes, density, identity)
    repeated = compose(geometry_document, inputs, dimensions, modes, density, identity)
    require(candidate.BytesValue == repeated.BytesValue, "repeated neutral construction changed bytes")
    measured = inspect(candidate, modes, density, identity)
    baseline = compose(geometry_document, inputs, dimensions, MODES["unassigned"], density, identity)
    changes = {name for name, item in candidate.StreamsValue.items() if item != baseline.StreamsValue[name]}
    permitted = {"Contents/Config-0", "Contents/Config-0-ResolvedFeatures", "Contents/CMgr"}
    require(changes <= permitted and (("Contents/Config-0" in changes) == modes[0])
            and (("Contents/CMgr" in changes) == any(modes[1:])),
            "material probe changed unrelated stream topology or missed its target")
    require(not AUDIT.DeniedReads, "guarded material probe accessed an external file or process")
    return {"schema": "kit.sw2026.assigned-material-probe-build.v1", "mode": request["mode"],
            "requested_density": density, "requested_identity": identity, "typed_readback": measured,
            "bytes": len(candidate.BytesValue), "sha256": sha256(candidate.BytesValue).hexdigest(),
            "artifact_base64": b64encode(candidate.BytesValue).decode("ascii"),
            "changed_streams": sorted(changes), "runtime_file_access_attempts": 0,
            "native_acceptance": False, "public_writer_qualified": False}


if __name__ == "__main__":
    print(json.dumps(main(), sort_keys=True, allow_nan=False))
