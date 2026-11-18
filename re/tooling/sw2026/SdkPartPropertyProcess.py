from __future__ import annotations

from base64 import b64encode
from codecs import lookup
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import sys
from xml.etree.ElementTree import fromstring


ROOT = Path(sys.argv[1])
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(ROOT / "re/tooling/sw2026")]

from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

AUDIT = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")
sys.addaudithook(AUDIT.InspectEvent)

from builders.PartTextProperties import make_property_streams
from convert.adapters.solidworks.Archive.Construction.Part.MakeCirclePart import MakeCirclePart
from convert.adapters.solidworks.Archive.Construction.Part.MakePolygonBlindPart import MakePolygonBlindPart
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectBlind import ProjectBlind
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectCircle import ProjectCircle
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadLineLoop import ReadLineLoop
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from convert.adapters.solidworks.Core.Preparation.BindPartIntent import BindPartIntent
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from interchange.document.Models.DocumentModel import CadDocument
from interchange.document.Validation.DocumentAssemblyValidate import GetAssemblyErrs
from interchange.document.Validation.DocumentFeatureValidate import GetFeatureErrs
from interchange.document.Validation.DocumentReferenceValidate import GetRefErrors
from interchange.serialization.Deserialize import FromData

CODECS = tuple(lookup(name) for name in ("utf-8", "latin-1", "utf-16-le"))
REQUEST = json.load(sys.stdin)
AUDIT.BeginBuild()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def parts(document):
    require(type(document) is CadDocument and len(document.configurations) == 1,
            "text property construction requires one actual part configuration")
    config, = document.configurations
    meta = document.metadata
    require(set(meta) <= {"name", "document_summary", "custom_properties"}
            and set(config.attributes) <= {"custom_properties"}, "part property discovery found unprojected neutral data")
    streams = make_property_streams(meta.get("document_summary", {}), meta.get("custom_properties", {}),
                                    config.attributes.get("custom_properties", {}))
    modeled = replace(document, metadata={"name": meta["name"]}, configurations=(replace(config, attributes={}),))
    return modeled, streams


def main():
    document = FromData(REQUEST["document"])
    modeled, extra = parts(document)
    if REQUEST["profile"] == "polygon":
        plan, build = ProjectBlind(modeled, ReadLineLoop), MakePolygonBlindPart
    elif REQUEST["profile"] == "circle":
        plan, build = ProjectCircle(modeled), MakeCirclePart
    else:
        raise ValueError("unknown property discovery model profile")
    recipe = MakePartRecipe(plan, REQUEST["created_at"])
    candidate = build(modeled, BindPartIntent(modeled, plan, recipe, recipe.OutputValue))
    require(not (candidate.StreamsValue.keys() & extra.keys()), "part properties would collude with another binary stream owner")
    streams = {**candidate.StreamsValue, **extra}
    blob = BuildSldprt(streams, FormatVersion=4)
    check = SldprtArchive.FromBytes(blob)
    require(check.Streams == streams and all(fromstring(check.Require(key)) is not None for key in extra),
            "standalone property streams changed in the generated part")
    return {"schema": "kit.sw2026.sdk-part-text-property-candidate.v1", "passed": True,
            "file_bytes": len(blob), "file_sha256": sha256(blob).hexdigest(), "file_base64": b64encode(blob).decode("ascii"),
            "stream_lengths": {key: len(value) for key, value in streams.items()},
            "stream_sha256": {key: sha256(value).hexdigest() for key, value in streams.items()},
            "native_path": recipe.OutputValue.PathName, "runtime_input_file_reads": len(AUDIT.DeniedReads),
            "generated_property_streams": list(extra), "public_writer_qualified": False, "native_acceptance": False}


print(json.dumps(main(), sort_keys=True, ensure_ascii=False, allow_nan=False))
