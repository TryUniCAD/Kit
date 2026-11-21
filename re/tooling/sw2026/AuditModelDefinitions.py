from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from convert.adapters.solidworks.Archive.Definition.ReadModelDef import ReadModelDef
from convert.adapters.solidworks.Archive.Definition.WriteModelDef import WriteModelDef
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive


def digest(data):
    return sha256(data).hexdigest()


def audit(name, data):
    row = {"file": name, "file_sha256": digest(data)}
    try:
        archive = SldprtArchive.from_bytes(data)
        if ContainerMo(archive.streams) != 19000:
            raise ValueError("unsupported version")
        stream = archive.require("Contents/Definition")
        row.update(stream_sha256=digest(stream), bytes=len(stream))
        value = ReadModelDef(stream, 19000)
        encoded = WriteModelDef(value.GraphValue)
        if encoded.OutputValue != stream or value.MapValue.CounterValue != encoded.MapValue.CounterValue:
            raise ValueError("Definition bytes or archive map extent changed")
        if not (encoded.UsageValue.IsComplete and value.UsageValue.IsComplete):
            raise ValueError("the Definition was not completely consumed")
        row.update(passed=True, next_map_index=value.MapValue.CounterValue)
    except (ValueError, TypeError, KeyError) as error:
        row.update(passed=False, error=str(error), error_kind=type(error).__name__)
    return row


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus-root", type=Path, required=True)
    parser.add_argument("--corpus-revision", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    command = ["git", "-C", str(args.corpus_root)]
    revision = subprocess.check_output(command + ["rev-parse", args.corpus_revision], text=True).strip()
    names = subprocess.check_output(command + ["ls-tree", "-r", "--name-only", "-z", revision,
                                               "--", "re/solidworks/v2026/corpus"]).decode().split("\0")
    records = []
    for name in names:
        path = Path(name)
        if path.suffix.upper() not in (".SLDPRT", ".SLDASM") or path.stem.startswith(("H01", "H02")):
            continue
        records.append(audit(name, subprocess.check_output(command + ["show", f"{revision}:{name}"])))
    passed = bool(records and all(row["passed"] for row in records))
    by_suffix = Counter(Path(row["file"]).suffix.lower() for row in records)
    outcome = {"schema": "kit.sw2026.sdk-model-definition-corpus.v1", "corpus_revision": revision,
               "passed": passed, "file_count": len(records), "counts_by_suffix": dict(by_suffix),
               "distinct_definition_hashes": len({row["stream_sha256"] for row in records if row["passed"]}),
               "original_heldout_inputs_read": 0, "records": records}
    with args.output.open("x", encoding="utf-8") as report:
        json.dump(outcome, report, indent=2, sort_keys=True)
        report.write("\n")
    print(json.dumps({name: outcome[name] for name in ("passed", "file_count", "counts_by_suffix",
                                                       "distinct_definition_hashes")}, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
