from base64 import b64encode
from codecs import lookup
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path
import json
import sys


HERE = Path(__file__).resolve()
ROOT = HERE.parents[6]
TOOLS = HERE.parents[3]
sys.path[:0] = [str(HERE.parent), str(ROOT), str(ROOT / "src"), str(TOOLS / "linear_pattern"),
                str(TOOLS / "linear_pattern/neutral"), str(TOOLS), str(TOOLS / "serial")]

from PatternParityPacket import APPLICATIONS, check_request, encode, require


def ready():
    for codec in ("utf-8", "utf-16-le", "latin-1", "us-ascii"):
        lookup(codec)
    return json.load(sys.stdin)


def check_purity(audit):
    require(not audit.DeniedReads and not APPLICATIONS.intersection(name.split(".")[0] for name in sys.modules),
            "pattern worker opened an input or imported an application")


def bridge():
    from ProveNeutralPattern import author_document
    from interchange import PlaneAxis
    from interchange.document.Behavior import DocumentIo
    from interchange.serialization.TypeRegistry import KTypeRegistry
    from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

    model = ready()
    audit = BuildAudit(TOOLS / "serial/defs")
    sys.addaudithook(audit.InspectEvent)
    audit.BeginBuild()
    require(KTypeRegistry["PlaneIntersectionAxis"] is PlaneAxis, "working public hinge tag required")
    authored = author_document(model)
    value = check_request({"document": authored.document.to_dict(), "target": asdict(authored.output)})
    require(KTypeRegistry["PlaneIntersectionAxis"] is PlaneAxis, "bridge changed the portable definition registry")
    check_purity(audit)
    sys.stdout.buffer.write(encode(value))


def emit():
    from LocalPatternContainerProcess import audit, linked
    from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import SelfFileInput
    from convert.adapters.solidworks.Archive.Construction.Patterns.Emission.EmitPatArchive import EmitPatArchive
    from convert.adapters.solidworks.Archive.Construction.Patterns.Graph.MakePatGraph import MakePatGraph
    from convert.adapters.solidworks.Core.Preparation.Patterns.PlanLinPattern import PlanLinPattern
    from interchange import PlaneAxis
    from interchange.document.Behavior import DocumentIo
    from interchange.document.Validation import DocumentAssemblyValidate, DocumentFeatureValidate, DocumentReferenceValidate
    from interchange.document.Models.DocumentModel import CadDocument

    request = check_request(ready())
    document_wire = encode(request["document"])
    audit.BeginBuild()
    document = CadDocument.from_json(document_wire.decode("utf-8"))
    require(type(document.feature_timeline[2].definition) is PlaneAxis, "working portable axis required")
    target = SelfFileInput(**request["target"])
    graph = MakePatGraph(PlanLinPattern(document, target))
    streams, binary = EmitPatArchive(graph)
    link, headers = linked(binary, streams)
    require(len(streams) == 10 and len(graph.RootsValue) == len(link.ResolvedValue.RootsValue) == 24
            and len(headers) == 2 and len(graph.DriverValues) == 6 and encode(document.to_dict()) == document_wire,
            "complete pattern archive or neutral owner inventory changed")
    check_purity(audit)
    sys.stdout.buffer.write(encode({
        "payload": b64encode(binary).decode("ascii"), "sha256": sha256(binary).hexdigest(), "bytes": len(binary),
        "streams": {name: sha256(raw).hexdigest() for name, raw in streams.items()}, "root_count": 24,
        "typed_replays": 9, "runtime_reads": len(audit.DeniedReads),
    }))


if __name__ == "__main__":
    if sys.argv[1:] == ["--bridge"]:
        bridge()
    elif sys.argv[1:] == ["--emit"]:
        emit()
    else:
        raise SystemExit("invalid isolated pattern worker mode")
