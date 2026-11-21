from argparse import ArgumentParser
import json
from math import dist, isclose
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from AuditRevEndOwners import audit_streams, digest, guard_runtime
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.ReadDimHandle import ReadDimHandle
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.ReadDimRows import ReadDimRows
from convert.adapters.solidworks.Core.TypedResolved.Lines.LineIndex import LineIndex
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.ReadParents import ReadParents
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from convert.adapters.solidworks.Core.TypedResolved.Revolves.ReadRevAxisRef import ReadRevAxisRef


def inspect(raw):
    archive = SldprtArchive.from_bytes(raw)
    link = ReadNativeLink(archive, 0)
    revolve, = (node for node in link.ResolvedValue.RootsValue if node.ClassValue.NameValue == "moRevolution_c")
    profile, = ReadParents(revolve)
    axis = ReadRevAxisRef(revolve, profile, link.ConfigValue.RootValue)
    sketch = RequireNative(profile.FieldsValue["pd_f80"], "sgSketch")
    fields = sketch.FieldsValue
    dims = NativeRecord(fields["dims"])
    binary, = ReadDimRows(dims, "nlog2", "log_g2")
    unary = ReadDimRows(dims, "nlog1", "log_g1")
    assert len(unary) == 4
    owner_counts = {}
    for row in unary:
        index = ReadDimHandle(NativeRecord(row["d"])["h1"], "sgLineHandle")
        owner_counts[index] = owner_counts.get(index, 0) + 1
    values = NativeRecord(binary["d"])
    pair = [ReadDimHandle(values[name], "sgLineHandle") for name in ("h1", "h2")]
    assert values["f80"] == 14 and len(set(pair)) == 2 and axis.IndexValue not in pair
    assert set(pair) <= set(owner_counts) and set(owner_counts.values()) == {1}
    lines = NativeRows(fields["lines"])
    points = NativeRows(fields["points"])
    lengths = []
    reference_counts = []
    for index in pair:
        line = NativeRecord(lines[index]["line"])
        reference_counts.append(line["f20"])
        endpoints = (LineIndex(line, "fc8_s", "fc8", 65535), LineIndex(line, "fcc_s", "fcc", 65535))
        coordinates = []
        for endpoint in endpoints:
            point = NativeRecord(points[endpoint]["point"])
            position = NativeRecord(point["pos"])
            coordinates.append((position["x"], position["y"]))
        lengths.append(dist(*coordinates))
    assert reference_counts == [2, 2] and isclose(*lengths, rel_tol=0.0, abs_tol=1e-10)
    words = {name: value for name, value in values.items() if name not in ("h1", "h2") and (value is None or type(value) in (int, float, bool, str))}
    references = {name: (values[name] is not None) for name in ("h1", "h2", "ext1", "ext2", "ext3", "f108")}
    replay = audit_streams(archive, link)
    return {"source_sha256": digest(raw), "end_mode": NativeRecord(revolve.FieldsValue["f8d8"].FieldsValue)["f0c"],
            "binary_equal_owners": pair, "unary_count": len(unary), "equal_lengths_verified": True,
            "line_reference_counts": reference_counts, "words": words, "references": references,
            "streams": replay}


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--asset", type=Path, required=True)
    parser.add_argument("--sha256", required=True)
    args = parser.parse_args()
    source = args.asset.read_bytes()
    assert digest(source) == args.sha256
    blocked = guard_runtime()
    result = inspect(source)
    assert not blocked
    print(json.dumps(result | {"runtime_external_access_attempts": len(blocked)}, sort_keys=True, allow_nan=False))
