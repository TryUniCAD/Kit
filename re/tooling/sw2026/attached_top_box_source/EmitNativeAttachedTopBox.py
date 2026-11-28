from argparse import ArgumentParser
from base64 import b64encode
from codecs import lookup
from hashlib import sha256
from importlib import import_module
import json
from pathlib import Path
import sys


def main():
    parser = ArgumentParser(description="Emit a neutral attached Top box with the guarded shared writer")
    parser.add_argument("--root", type=Path)
    root = (parser.parse_args().root or Path(__file__).resolve().parents[4]).resolve(strict=True)
    sys.path[:0] = [str(root), str(root / "src")]

    from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

    audit = BuildAudit(root / "re/tooling/sw2026/serial/defs")
    sys.addaudithook(audit.InspectEvent)

    from convert.adapters.solidworks.Archive.Construction.Metadata.Properties.PartTextInput import PartTextInput
    from convert.adapters.solidworks.Core.Preparation.FreecadBox.MakeOriginBoxPart import MakeOriginBoxPart
    from interchange import CadDocument
    from interchange.serialization.Deserialize import FromData

    for module in ("interchange.brep.Validation.BrepValidate",
                   "interchange.document.Validation.DocumentAssemblyValidate",
                   "interchange.document.Validation.DocumentFeatureValidate",
                   "interchange.document.Validation.DocumentReferenceValidate"):
        import_module(module)
    for name in ("utf-16-le", "utf-8", "latin-1"):
        lookup(name)

    request = json.load(sys.stdin)
    audit.BeginBuild()
    if type(request) is not dict or set(request) != {"document", "native_path", "creation_epoch"}:
        raise ValueError("attached Top generation requires a neutral document and authored destination")
    document = FromData(request["document"])
    if type(document) is not CadDocument or document.source.format_id != "kit.neutral.box":
        raise ValueError("attached Top generation requires the clean neutral box model")
    candidate = MakeOriginBoxPart(
        document, request["native_path"], request["creation_epoch"],
        PartTextInput({}, {}, {}), TopAttached=True,
    )
    print(json.dumps({
        "passed": True,
        "native_acceptance": False,
        "public_writer_qualified": False,
        "sha256": sha256(candidate.BytesValue).hexdigest(),
        "bytes": len(candidate.BytesValue),
        "streams": {name: {"bytes": len(data), "sha256": sha256(data).hexdigest()}
                    for name, data in candidate.StreamsValue.items()},
        "runtime_input_file_reads": len(audit.DeniedReads),
        "blob": b64encode(candidate.BytesValue).decode("ascii"),
    }, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
