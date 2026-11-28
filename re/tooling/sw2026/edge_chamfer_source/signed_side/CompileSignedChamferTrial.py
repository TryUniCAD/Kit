from base64 import b64decode
from codecs import lookup
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent.parent / "sealed"))

from CompileSealedChamfer import audit, compile_part, external
from ProveChamferEdgeOwners import check_owners, digest, key, require
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink


def proof(data):
    row = compile_part(data)
    archive = SldprtArchive.from_bytes(b64decode(row["model_base64"], validate=True))
    link = ReadNativeLink(archive, 0, ReadChamfers=True)
    root = link.ConfigValue.RootValue
    feature = link.ResolvedValue.RootsValue[-1]
    fields = feature.FieldsValue
    owners, _, _ = check_owners(feature, fields["f538"], root, cold=True)
    words = [entry.FieldsValue["f68"] for entry in (fields["f888"].FieldsValue["items"][0]["o"], fields["f8a8"])]
    require(words == [0, 0] and fields["f860"] == 0 and not audit.DeniedReads and not external,
            "signed modeled coedge requires unflipped detached and selected wrappers")
    try:
        ReadNativeLink(archive, 0)
    except ValueError as issue:
        reason = str(issue)
        require(reason == "unsupported SOLIDWORKS body class Chamfer_c schema 1",
                "ordinary native read stopped outside the expected scope guard")
    else:
        raise ValueError("ordinary native reader unexpectedly admits the research profile")
    require(not audit.DeniedReads and not external, "fresh ordinary refusal accessed an external source")
    streams = {name: digest(archive.require(name)) for name in archive.streams}
    return row | {"schema": "kit.sw2026.disclosed-chamfer-signed-compiler.v1",
                  "face_roles": [key(owner) for owner in owners], "component_f68_words": words,
                  "feature_f860": fields["f860"], "ordinary_read_refusal": reason, "stream_sha256": streams}


if __name__ == "__main__":
    tuple(lookup(name) for name in ("ascii", "utf-8", "utf-16-le", "latin-1", "cp1252"))
    audit.BeginBuild()
    data = sys.stdin.buffer.read(65537)
    require(not sys.argv[1:] and 0 < len(data) <= 65536, "expected one complete neutral request on stdin")
    print(json.dumps(proof(data), allow_nan=False, sort_keys=True))
