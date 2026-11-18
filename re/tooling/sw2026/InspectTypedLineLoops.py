from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import time


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--source-manifest", type=Path)
    parser.add_argument("--native-cases", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    sys.path[:0] = [str(root / "src"), str(root)]
    manifest = None
    if args.source_manifest:
        manifest = json.loads(args.source_manifest.read_bytes())
        for row in manifest["files"]:
            if sha(root / row["path"]) != row["sha256"]:
                raise ValueError("source manifest mismatch: " + row["path"])
    from tests.Convert.Solidworks.Research.Resolved.Lines.LineReadTests import TestLineRead
    from tests.Convert.Solidworks.Research.Resolved.Lines.LineScopeTests import TestLineScope
    from tests.Convert.Solidworks.Research.Resolved.Lines.LineIdentityTests import TestLineIds
    from tests.Convert.Solidworks.Research.Resolved.PublicGraphTests import TestPublicGraph
    from tests.Convert.Solidworks.Research.Resolved.Presentation.TreeGraphTests import TestDefaultTree
    from tests.Convert.Solidworks.Research.Resolved.Presentation.AuthoredTreeTests import TestCustomTree
    from tests.Convert.Solidworks.Research.Resolved.Presentation.AuthoredOrderTests import TestCustomOrder
    from tests.Convert.Solidworks.Research.Resolved.Presentation.LegacyTreeTests import TestOlderTree
    from tests.Convert.Solidworks.Core.SolidworksRectangleReaderTests import TestRectOpen, TestAnnulus, TestLegacyMixed
    from tests.Convert.Solidworks.Research.Curve.SavedRadialReadTests import TestSavedRadialRead
    phases = []
    process_count = 0

    def audit(event, fields):
        nonlocal process_count
        if event == "subprocess.Popen":
            process_count += 1

    sys.addaudithook(audit)
    with tempfile.TemporaryDirectory(prefix="kit-typed-line-loops-") as temporary:
        for label, action in (
            ("fresh-neutral-line-loops", TestLineRead),
            ("admission-and-extended-fields", TestLineScope),
            ("native-identity-namespaces", TestLineIds),
            ("prior-typed-blind-graph", TestPublicGraph),
            ("default-system-tree", TestDefaultTree),
            ("custom-system-tree", TestCustomTree),
            ("custom-folder-order", TestCustomOrder),
        ):
            target = Path(temporary) / label
            target.mkdir()
            started = time.monotonic()
            before = process_count
            action(target)
            phases.append({"name": label, "passed": True, "processes": process_count - before,
                           "elapsed_seconds": time.monotonic() - started})
        for label, action in (
            ("older-18000-tree", TestOlderTree),
            ("disclosed-dimensioned-rectangle", TestRectOpen),
            ("disclosed-annulus", TestAnnulus),
            ("older-mixed-circle-and-rectangles", TestLegacyMixed),
            ("saved-radius-and-diameter", TestSavedRadialRead),
        ):
            started = time.monotonic()
            before = process_count
            action()
            phases.append({"name": label, "passed": True, "processes": process_count - before,
                           "elapsed_seconds": time.monotonic() - started})
    native_cases = []
    if args.native_cases:
        from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
        from convert.adapters.solidworks.Container.Container import SldprtArchive
        from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
        from tests.Convert.Solidworks.Research.Resolved.Lines.AssertLineRead import AssertLineRead
        from tests.Convert.Solidworks.Research.Resolved.RunPublicRead import RunPublicRead
        job = json.loads(args.native_cases.read_bytes())
        for row in job["cases"]:
            path = Path(row["path"])
            if sha(path) != row["sha256"]:
                raise ValueError("native input changed: " + row["label"])
            archive = SldprtArchive.from_bytes(path.read_bytes())
            link = ReadNativeLink(archive, 0)
            resolved = link.ResolvedValue
            encoded, repeated = WriteResolMut(resolved.RootsValue, resolved.ExtraFields, 19000,
                                              link.ConfigValue.MapValue, resolved.ContextValue)
            assert encoded == archive.require(link.StreamName)
            assert repeated.MapValue == resolved.MapValue
            document = RunPublicRead(path)
            vertices = tuple(tuple(point) for point in row["vertices_mm"])
            AssertLineRead(document, vertices, row["depth_mm"])
            assert sha(path) == row["sha256"]
            native_cases.append({"label": row["label"], "sha256": row["sha256"],
                                 "neutral_spec_sha256": row["neutral_spec_sha256"],
                                 "lines": len(vertices), "closed_loops": 1,
                                 "exact_endpoints_and_bounds": True, "resolved_roundtrip_equal": True,
                                 "actual_handle_adjacency": True, "inputs_unchanged": True,
                                 "passed": True})
    if manifest is not None:
        for row in manifest["files"]:
            if sha(root / row["path"]) != row["sha256"]:
                raise ValueError("source changed during proof: " + row["path"])
    result = {
        "schema": "kit.solidworks.typed-line-loops.sdk.v1",
        "passed": True,
        "source_manifest_sha256": sha(args.source_manifest) if args.source_manifest else None,
        "source_files": len(manifest["files"]) if manifest else None,
        "runner_sha256": sha(Path(__file__)),
        "processes": process_count,
        "phases": phases,
        "disclosed_native_input_reads": native_cases,
        "new_native_execution": False,
        "held_out_inputs_read": 0,
        "broad_geometry_coverage": False,
        "public_writer_qualification_changed": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as output:
        output.write(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"passed": True, "report_sha256": sha(args.output), "processes": process_count}))


if __name__ == "__main__":
    main()
