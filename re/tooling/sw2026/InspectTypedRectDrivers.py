from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import time


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('root', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--source-manifest', type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    sys.path[:0] = [str(root / 'src'), str(root)]
    manifest = json.loads(args.source_manifest.read_bytes())

    def verify():
        for row in manifest['files']:
            if digest(root / row['path']) != row['sha256']:
                raise ValueError('source changed: ' + row['path'])

    verify()
    from tests.Convert.Solidworks.Research.Resolved.LineDimensions.RectDriveReadTests import TestRectDrivers
    from tests.Convert.Solidworks.Research.Resolved.LineDimensions.RectDriveScopeTests import TestRectScope
    from tests.Convert.Solidworks.Research.Resolved.Lines.LineReadTests import TestLineRead
    from tests.Convert.Solidworks.Research.Resolved.Lines.LineScopeTests import TestLineScope
    from tests.Convert.Solidworks.Research.Resolved.Lines.LineIdentityTests import TestLineIds
    from tests.Convert.Solidworks.Research.Resolved.PublicGraphTests import TestPublicGraph
    from tests.Convert.Solidworks.Research.Resolved.Presentation.TreeGraphTests import TestDefaultTree
    from tests.Convert.Solidworks.Research.Resolved.Presentation.AuthoredTreeTests import TestCustomTree
    from tests.Convert.Solidworks.Research.Resolved.Presentation.AuthoredOrderTests import TestCustomOrder
    from tests.Convert.Solidworks.Research.Resolved.Presentation.LegacyTreeTests import TestOlderTree
    from tests.Convert.Solidworks.Core.SolidworksRectangleReaderTests import TestRectOpen, TestAnnulus, TestLegacyMixed
    from tests.Convert.Solidworks.Research.Curve.SavedRadialReadTests import TestRadialRead
    processes = 0

    def audit(event, fields):
        nonlocal processes
        if event == 'subprocess.Popen':
            processes += 1

    sys.addaudithook(audit)
    result = {'schema': 'kit.sw2026.typed-rectangle-drivers-sdk-regression.v1',
              'runner_sha256': digest(Path(__file__)),
              'source_manifest_sha256': digest(args.source_manifest),
              'source_files': len(manifest['files']), 'phases': [],
              'native_execution': False, 'heldout_inputs_read': 0,
              'public_writer_qualification_changed': False}
    with tempfile.TemporaryDirectory(prefix='kit-typed-rectangle-drivers-') as directory:
        for label, action in (
            ('fresh-rectangle-drivers', TestRectDrivers),
            ('malformed-driver-owners', TestRectScope),
            ('plain-line-loops', TestLineRead),
            ('plain-line-scope', TestLineScope),
            ('line-id-namespaces', TestLineIds),
            ('typed-blind-graph', TestPublicGraph),
            ('default-system-tree', TestDefaultTree),
            ('authored-system-tree', TestCustomTree),
            ('authored-folder-order', TestCustomOrder),
        ):
            destination = Path(directory) / label
            destination.mkdir()
            started, before = time.monotonic(), processes
            action(destination)
            result['phases'].append({'name': label, 'passed': True,
                                     'processes': processes - before,
                                     'elapsed_seconds': time.monotonic() - started})
        for label, action in (
            ('older-18000-tree', TestOlderTree),
            ('disclosed-native-rectangle', TestRectOpen),
            ('disclosed-annulus', TestAnnulus),
            ('older-mixed-sketch', TestLegacyMixed),
            ('saved-radial-drivers', TestRadialRead),
        ):
            started, before = time.monotonic(), processes
            action()
            result['phases'].append({'name': label, 'passed': True,
                                     'processes': processes - before,
                                     'elapsed_seconds': time.monotonic() - started})
    verify()
    result['passed'] = True
    result['processes'] = processes
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf-8') as output:
        output.write(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'passed': True, 'processes': processes, 'report_sha256': digest(args.output)}))


if __name__ == '__main__':
    main()
