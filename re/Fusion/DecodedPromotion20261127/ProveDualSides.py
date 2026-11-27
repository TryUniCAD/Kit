import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import traceback

from convert.Geometry.Extrude.Circular.DualSide.BuildDualSide import BuildDualSide
from interchange.serialization.JsonCodec import DumpJson, LoadJson
from tests.Convert.Integration.Fusion.DualSide.CheckDualNative import CheckDualNative
from tests.Convert.Integration.Fusion.DualSide.ReadDualCase import ReadDualCase
from tests.Convert.Integration.Fusion.DualSide.ReadDualCases import ReadDualCases


root = Path(sys.argv[1]).resolve()
output = Path(sys.argv[2]).resolve()
output.mkdir(parents=True, exist_ok=False)
(output / 'Geometry').mkdir()
capture_path = root / 're/Fusion/TwoSidedDraft20261127/Capture.json'
capture = json.loads(capture_path.read_text())
sources = [*sorted((root / 'src/convert/Geometry/Extrude/Circular/DualSide').glob('*.py')), *sorted((root / 'tests/Convert/Integration/Fusion/DualSide').glob('*.py'))]
report = dict(sdk_base=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip(), source_capture_sha256=hashlib.sha256(capture_path.read_bytes()).hexdigest(), source_files={str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}, models=False, native_calls=False, reader_admission='unchanged', writer_qualification='not_established', observations=[], native_archives=[])
for case in capture['cases']:
    for observation in case['observations']:
        identity = case['id'] + '_' + observation['stage']
        row = dict(case=case['id'], stage=observation['stage'], holdout=case['id'].startswith('holdout'), checks={})
        try:
            sample = ReadDualCase(capture_path, report['source_capture_sha256'], identity, observation['value'])
            geometry, volume, area, center, bounds = BuildDualSide(sample.Identity, sample.Frame, sample.Profile, sample.FirstMm, sample.SecondMm, sample.FirstTaper, sample.SecondTaper)
            actual = sample.Reading
            row['checks']['valid_closed_geometry'] = not geometry.validate(frozenset((sample.Identity,)))
            row['checks']['volume'] = math.isclose(volume, actual['volume_cm3'] * 1000, rel_tol=1e-8)
            row['checks']['area'] = math.isclose(area, actual['area_cm2'] * 100, rel_tol=1e-8)
            for index, (value, wanted) in enumerate(zip((center.x, center.y, center.z), actual['center_cm'], strict=True)):
                row['checks']['center_' + str(index)] = math.isclose(value, wanted * 10, abs_tol=1e-6)
            for index, (point, wanted) in enumerate(zip((bounds.minimum, bounds.maximum), actual['bounds_cm'], strict=True)):
                for axis, (value, target) in enumerate(zip((point.x, point.y, point.z), wanted, strict=True)):
                    row['checks'][f'bound_{index}_{axis}'] = math.isclose(value, target * 10, abs_tol=1e-7)
            document = DumpJson(geometry)
            row['checks']['neutral_json_roundtrip'] = LoadJson(document) == geometry
            path = output / 'Geometry' / (identity + '.json')
            path.write_text(document)
            row.update(geometry_file=str(path.relative_to(output)), geometry_sha256=hashlib.sha256(path.read_bytes()).hexdigest(), faces=len(geometry.faces), edges=len(geometry.edges), values_mm=dict(first=sample.FirstMm, second=sample.SecondMm, radius=sample.Profile.radius), angles_radians=dict(first=sample.FirstTaper, second=sample.SecondTaper))
        except Exception:
            row['error'] = traceback.format_exc().replace(str(root), '<checkout>')
        report['observations'].append(row)
for sample in ReadDualCases():
    row = dict(source=str(sample.Source.relative_to(root)), sha256=sample.Digest)
    try:
        geometry, *_ = BuildDualSide(sample.Identity, sample.Frame, sample.Profile, sample.FirstMm, sample.SecondMm, sample.FirstTaper, sample.SecondTaper)
        CheckDualNative(sample, geometry)
        row['passed'] = True
    except Exception:
        row.update(passed=False, error=traceback.format_exc().replace(str(root), '<checkout>'))
    report['native_archives'].append(row)
report['summary'] = dict(observations=len(report['observations']), comparisons=sum(len(r['checks']) for r in report['observations']), failed=sum(v is not True for r in report['observations'] for v in r['checks'].values()), errors=sum('error' in r for r in report['observations']), native_archives=len(report['native_archives']), native_archive_passes=sum(r['passed'] for r in report['native_archives']))
(output / 'Receipt.json').write_text(json.dumps(report, indent=2, sort_keys=True))
print(json.dumps(report['summary'], indent=2))
