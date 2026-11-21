from argparse import ArgumentParser
from base64 import b64encode
from codecs import lookup
from hashlib import sha256
from importlib import import_module
import json
from pathlib import Path
import sys

parser = ArgumentParser(description="Build a through-all part from a guarded portable document")
parser.add_argument("repository", type=Path)
root = parser.parse_args().repository.resolve(strict=True)
sys.path[:0] = [str(root), str(root / "src")]

from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

audit = BuildAudit(root / "re/tooling/sw2026/serial/defs")
sys.addaudithook(audit.InspectEvent)
from convert.adapters.solidworks.Core.Preparation.ThroughAll.PrepareThroughPart import PrepareThroughPart
from interchange.document.Models.DocumentModel import CadDocument
from interchange.serialization.Deserialize import FromData

for encoding in ("utf-8", "utf-8-sig", "utf-16-le", "utf-16-be", "ascii", "latin-1"):
    lookup(encoding)
for name in (
    "interchange.document.Models.DocumentProvenance",
    "interchange.brep.Validation.BrepValidate",
    "interchange.document.Validation.DocumentAssemblyValidate",
    "interchange.document.Validation.DocumentFeatureValidate",
    "interchange.document.Validation.DocumentReferenceValidate",
):
    import_module(name)

request = json.load(sys.stdin)
if set(request) != {"document", "native_path", "written_at"}:
    raise ValueError("through-all input requires its neutral document, native path and writer event")
audit.BeginBuild()
document = FromData(request["document"])
if type(document) is not CadDocument:
    raise TypeError("through-all input must contain an actual portable CAD document")
candidate = PrepareThroughPart(document, request["native_path"], request["written_at"])
if audit.DeniedReads or candidate.CutValue is None or candidate.CutValue.DepthValue is not None:
    raise ValueError("through-all candidate acquired an external input or invalid depth owner")
source_prefix = str(root / "re") + "/"
research_modules = [
    name
    for name, module in tuple(sys.modules.items())
    if name != "__main__" and str(getattr(module, "__file__", "")).startswith(source_prefix)
]
if research_modules:
    raise ValueError("through-all SDK used a research module during generation")
payload = candidate.BytesValue
print(json.dumps({
    "passed": True,
    "runtime_input_file_reads": len(audit.DeniedReads),
    "sdk_runtime_research_imports": len(research_modules),
    "generated": b64encode(payload).decode("ascii"),
    "sha256": sha256(payload).hexdigest(),
    "bytes": len(payload),
    "streams": {name: {"bytes": len(data), "sha256": sha256(data).hexdigest()}
                for name, data in candidate.StreamsValue.items()},
    "stock_feature": candidate.PlanValue.FeatureName,
}, sort_keys=True, allow_nan=False))
