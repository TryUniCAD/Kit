# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


import difflib
import hashlib
import json
from pathlib import Path
import subprocess
import sys


def field(data, pos, width, order, codec):
    if pos + width > len(data):
        return None
    length = int.from_bytes(data[pos:pos + width], order)
    if not 1 <= length <= 4096:
        return None
    start = pos + width
    end = start + length * (1 if codec == "ascii" else 2)
    if end > len(data):
        return None
    try:
        value = data[start:end].decode(codec)
    except UnicodeError:
        return None
    if not value.isascii() or not value.isprintable() or not value.strip():
        return None
    return {"offset": pos, "end": end, "codec": codec, "value": value}


def infer(data):
    layouts = []
    for width in (1, 2, 4, 8):
        for order in (("little",) if width == 1 else ("little", "big")):
            rows = []
            pos = 0
            for _ in range(64):
                found = [r for c in ("ascii", "utf-16le", "utf-16be")
                         if (r := field(data, pos, width, order, c)) is not None]
                if len(found) != 1:
                    break
                rows.append(found[0])
                pos = found[0]["end"]
            if len(rows) >= 2:
                layouts.append((width, order, rows))
    return layouts


def text_reader(root, scratch, data, pin, controls):
    layouts = infer(data)
    if len(layouts) != 1:
        return None, None
    width, order, rows = layouts[0]
    report = {"width": width, "order": order, "records": rows, "prefix_bytes": rows[-1]["end"],
              "status": "candidate_text_prefix"}
    if len(controls) < 2:
        return report, None
    samples = [(data, rows)]
    for blob in controls:
        found = infer(blob)
        if len(found) != 1 or found[0][:2] != (width, order):
            return report, None
        samples.append((blob, found[0][2]))
    codecs = []
    for group in zip(rows, samples[1][1]):
        if len({entry["codec"] for entry in group}) != 1:
            break
        codecs.append(group[0]["codec"])
    if len(codecs) < 2 or any([r["codec"] for r in entries[:len(codecs)]] != codecs for _, entries in samples[2:]):
        return report, None
    if not any(tuple(r["value"] for r in entries[:len(codecs)]) != tuple(r["value"] for r in rows[:len(codecs)])
               for _, entries in samples[2:]):
        return report, None
    code = '''import json
from pathlib import Path
import sys

from InferenceGrid.CountedText import field
from InferenceInputs import read_file


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("supply one binary stream")
    data = read_file(Path(sys.argv[1]), 128 * 1024 * 1024)
    rows = []
    pos = 0
    for codec in CODECS:
        row = field(data, pos, WIDTH, ORDER, codec)
        if row is None:
            raise SystemExit(2)
        rows.append(row)
        pos = row["end"]
    print(json.dumps(rows))
'''.replace("CODECS", repr(tuple(codecs))).replace("WIDTH", str(width)).replace("ORDER", repr(order))
    digest = hashlib.sha256(code.encode()).hexdigest()
    path = "re/DerivedReaders/CountedText" + digest[:12] + ".py"
    if (root / path).exists():
        return report, None
    import os
    script = scratch / "CountedTextReader.py"
    script.write_text(code)
    probe = scratch / "counted-text.bin"
    for blob, entries in samples:
        probe.write_bytes(blob)
        process = subprocess.run([sys.executable, script, probe], cwd=scratch,
                                 env={**os.environ, "PYTHONPATH": str(root / "re/automation")},
                                 capture_output=True, timeout=30)
        if process.returncode or json.loads(process.stdout) != entries[:len(codecs)]:
            return report, None
    report.update(status="replayed_text_prefix", shared_codecs=codecs)
    from convert.Formats.Fusion.SourceProof.Auxiliary.Manifest.ReadAssetMeta import ReadAssetMeta
    checks = []
    for blob, entries in samples:
        try:
            asset, snapshot, _ = ReadAssetMeta(blob)
        except ValueError:
            continue
        values = [r["value"] for r in entries[:len(codecs)]]
        checks.append({"sha256": hashlib.sha256(blob).hexdigest(),
                       "asset_id_matches": len(values) > 1 and values[1] == asset,
                       "snapshot_id_matches": len(values) > 2 and values[2] == snapshot})
    if checks:
        report["fusion_manifest_checks"] = checks
    return report, {"path": path, "reader_sha256": digest, "input_sha256": pin,
                    "base": subprocess.check_output(["git", "-C", root, "rev-parse", "HEAD"], text=True).strip(),
                    "control_sha256": [hashlib.sha256(b).hexdigest() for b in controls],
                    "patch": "".join(difflib.unified_diff([], code.splitlines(True), "/dev/null", "b/" + path))}
