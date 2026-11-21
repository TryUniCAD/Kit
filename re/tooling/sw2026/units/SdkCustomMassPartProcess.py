from __future__ import annotations

from base64 import b64encode
from codecs import lookup
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
import json
import sys


ROOT = Path(sys.argv[1]).resolve(strict=True)
sys.path[:0] = [str(ROOT / "src"), str(ROOT)]

from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectPlain import ProjectPlain
from convert.adapters.solidworks.Archive.Construction.Units.UnitInput import UnitInput
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from convert.adapters.solidworks.Core.Preparation.PreparePart import PreparePart
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from interchange.brep.Validation.BrepValidate import GetBrepErrors
from interchange.document.Models.DocumentModel import CadDocument
from interchange.document.Validation.DocumentAssemblyValidate import GetAssemblyErrs
from interchange.document.Validation.DocumentFeatureValidate import GetFeatureErrs
from interchange.document.Validation.DocumentReferenceValidate import GetRefErrors
from interchange.serialization.Deserialize import FromData
from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit


CODECS = tuple(lookup(name) for name in ("utf-16-le", "utf-8", "latin-1"))
AUDIT = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")


def build(request):
    if set(request) != {"document", "native_path", "created_at", "units"}:
        raise ValueError("custom mass construction requires one model and explicit target settings")
    document = FromData(request["document"])
    if type(document) is not CadDocument:
        raise TypeError("custom mass construction requires an actual neutral model")
    plan = ProjectPlain(document)
    recipe = MakePartRecipe(plan, request["created_at"])
    raw_units = request["units"]
    if raw_units is not None:
        if type(raw_units) is not list or len(raw_units) != 5:
            raise ValueError("custom mass experiment requires five semantic unit inputs")
        recipe = replace(recipe, DocumentUnits=UnitInput(*raw_units))
    candidate = PreparePart(document, request["native_path"], recipe)
    archive = SldprtArchive.from_bytes(candidate.BytesValue)
    link = ReadNativeLink(archive, 0)
    config = link.ConfigValue
    cfg, context = WriteConfigMut(config.RootValue, 19000, config.HeaderValue)
    resolved, _ = WriteResolMut(link.ResolvedValue.RootsValue, link.ResolvedValue.ExtraFields,
                                19000, context.MapValue, link.ResolvedValue.ContextValue)
    if cfg != archive.require(link.ConfigName) or resolved != archive.require(link.StreamName):
        raise ValueError("linked custom mass graph did not re-emit its complete part streams")
    table = config.RootValue.FieldsValue["f9b8"].FieldsValue
    units = {row["o"].ClassValue.NameValue: row["o"].FieldsValue for row in table["items"]}
    length, density, system = (units[name] for name in (
        "moLengthUserUnits_c", "moDensityUnits_c", "moUnitSysUnits_c",
    ))
    attached = density.get("fb8")
    source_length = dict(length)
    source_length.update({"fb8": None, "f88": 0.0})
    return {
        "passed": True, "target": request["native_path"], "bytes": len(candidate.BytesValue),
        "sha256": sha256(candidate.BytesValue).hexdigest(), "blob": b64encode(candidate.BytesValue).decode(),
        "numeric_dimensions_m": [plan.WidthValue, plan.HeightValue, plan.DepthValue],
        "archive_preferences": {"system": system["fb0"], "mass": density["fc4"],
                                "length": length["fb0"], "length_precision": length["f0c"],
                                "volume": [density["fc0"], density["fc8"], density["fcc"]],
                                "density_has_independent_length": attached is not None,
                                "density_matches_primary_with_neutral_caches": attached is not None
                                and attached.FieldsValue == source_length},
        "streams": {name: {"bytes": len(raw), "sha256": sha256(raw).hexdigest()}
                    for name, raw in candidate.StreamsValue.items()},
        "runtime_input_reads": len(AUDIT.DeniedReads), "native_acceptance": False,
    }


if __name__ == "__main__":
    request = json.load(sys.stdin)
    sys.addaudithook(AUDIT.InspectEvent)
    AUDIT.BeginBuild()
    print(json.dumps(build(request), sort_keys=True, allow_nan=False))
