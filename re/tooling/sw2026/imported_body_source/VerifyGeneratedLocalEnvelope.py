from codecs import lookup
from hashlib import sha256
from pathlib import Path
import json
import sys

from BuildLocalBodyKernel import CASES, make_nodes, prism_model
from LocalBodyEnvelope import LocalBody, decode, encode
from LocalBodyKernel import _render_local, require
from convert.adapters.solidworks.Archive.Partition.LocalWrite.EncodeLocalBody import EncodeLocalBody
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.ReadLocalEnvelope import ReadLocalWrap
from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit


ROOT = Path(__file__).resolve().parents[4]
KEYS = ("Imported geometry", "Transfer Δ17", "Ω" + "x" * 254)


def model_rows(shape, case):
    points, levels, _ = case
    model = prism_model(shape, points, levels)
    source_nodes = make_nodes(model)
    raw = _render_local(source_nodes)
    nodes = tuple(XmtNode(row.index, row.kind, row.fields) for row in source_nodes)
    result = []
    for key in KEYS:
        body = EncodeLocalBody(key, nodes)
        reference = LocalBody(key, raw)
        require(body == encode(reference) and decode(body) == reference, "generated local framing differs")
        require(ReadLocalWrap(body, raw) == key, "SDK reader lost the actual Unicode group key")
        result.append({"key": key, "bytes": len(body), "sha256": sha256(body).hexdigest()})
    require(len({row["bytes"] for row in result}) == len(KEYS), "group key changes did not affect output length")
    return nodes, result


def refuses(key, nodes):
    try:
        EncodeLocalBody(key, nodes)
    except ValueError:
        return True
    raise ValueError("unqualified key or kernel input was accepted")


def verify():
    tuple(lookup(name) for name in ("utf-8", "utf-16-le", "latin-1"))
    audit = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")
    audit.BeginBuild()
    active = True

    def guard(event, arguments):
        if active:
            audit.InspectEvent(event, arguments)
            if event.startswith("socket.") or event in ("subprocess.Popen", "ctypes.dlopen"):
                raise PermissionError("local body envelope used runtime external state")

    sys.addaudithook(guard)
    try:
        receipts = {shape: model_rows(shape, case) for shape, case in CASES.items()}
        nodes = receipts["Rectangular"][0]
        refusals = {name: refuses(value, nodes) for name, value in
                    (("empty", ""), ("nil", None), ("embedded_null", "bad\0name"), ("newline", "two\nlines"))}
        refusals["opaque_kernel"] = refuses(KEYS[0], b"an opaque stream")
    finally:
        active = False
    require(not audit.DeniedReads, "local body envelope used runtime input files")
    rows = {shape: result for shape, (_, result) in receipts.items()}
    return {"schema": "kit.sw2026.generated-local-body-envelope.v1", "cases": rows,
            "exact_local_envelopes": sum(len(result) for result in rows.values()),
            "runtime_input_file_reads": len(audit.DeniedReads), "refusals": refusals}


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2, sort_keys=True, allow_nan=False))
