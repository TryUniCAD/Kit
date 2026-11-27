import dataclasses
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import traceback

from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Graph.GraphValues import NumberValue, ObjectFields, PointCoords
from convert.adapters.Fusion.Native.Graph.SelectExtrusion import SelectExtrusion
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.Geometry.Extrude.Circular.DualSide.BuildDualSide import BuildDualSide
from convert.Geometry.Extrude.Circular.DualSide.MeasureDualMass import MeasureDualMass
from tests.Convert.Api.Fusion.Native.ChangeNative import ChangeField
from tests.Convert.Integration.Fusion.DualSide.ChangeDualMass import ChangeDualMass
from tests.Convert.Integration.Fusion.DualSide.CheckDualNative import CheckDualNative
from tests.Convert.Integration.Fusion.DualSide.ReadDualCases import ReadDualCases


root = Path(sys.argv[1]).resolve()
output = Path(sys.argv[2]).resolve()
output.mkdir(parents=True, exist_ok=False)
(output / 'Counterexamples').mkdir()
sources = [*sorted((root / 'src/convert/Geometry/Extrude/Circular/DualSide').glob('*.py')), *sorted((root / 'tests/Convert/Integration/Fusion/DualSide').glob('*.py'))]
report = dict(sdk_base=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(), source_files={str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}, models=False, native_api_calls=0, tensor_units='cm5 native volume inertia about world origin no density', relative_tolerance=1e-6, absolute_tolerance=1e-8, rows=[], counterexamples=[])
samples = ReadDualCases()
for sample in samples:
    row = dict(source=str(sample.Source.relative_to(root)), sha256=sample.Digest, checks=[])
    try:
        raw = sample.Source.read_bytes()
        assert hashlib.sha256(raw).hexdigest() == sample.Digest
        model = ReadDocument(raw)
        context = SelectExtrusion(BuildGraph(model))
        cache = ObjectFields(context.BodyNode.Fields['cache'])
        diagonal, cross = MeasureDualMass(sample.Frame,sample.Profile,sample.FirstMm,sample.SecondMm,sample.FirstTaper,sample.SecondTaper)
        geometry, volume, area, center, bounds = BuildDualSide(sample.Identity,sample.Frame,sample.Profile,sample.FirstMm,sample.SecondMm,sample.FirstTaper,sample.SecondTaper)
        expected = {'volume': (volume/1000,), 'area': (area/100,), 'cog': tuple(v/10 for v in (center.x,center.y,center.z)), 'moi': tuple(v/100000 for v in (diagonal.x,diagonal.y,diagonal.z)), 'moiOffDiag': tuple(v/100000 for v in (cross.x,cross.y,cross.z))}
        for field, values in expected.items():
            actual = (NumberValue(cache[field]),) if field in ('volume','area') else PointCoords(cache[field])
            for index,(value,wanted) in enumerate(zip(actual,values,strict=True)):
                row['checks'].append(dict(field=field,component=index,actual=value,expected=wanted,passed=math.isclose(value,wanted,rel_tol=1e-6,abs_tol=1e-8)))
        CheckDualNative(sample,geometry)
    except Exception:
        row['error'] = traceback.format_exc().replace(str(root),'<checkout>')
    report['rows'].append(row)
sample = next(s for s in samples if s.Identity == 'baseline')
model = ReadDocument(sample.Source.read_bytes())
context = SelectExtrusion(BuildGraph(model))
for field, axis in [('volume',''),('area',''), *[(name,axis) for name in ('cog','moi','moiOffDiag') for axis in ('x','y','z')]]:
    row = dict(field=field,axis=axis)
    try:
        cache = ChangeDualMass(context.BodyNode.Fields['cache'],field,axis)
        changed = ChangeField(model,context.BodyNode.ObjectId,'cache',cache)
        raw = EmitParsed(changed)
        path = output/'Counterexamples'/(field+'_'+(axis or 'scalar')+'.f3d')
        path.write_bytes(raw)
        row.update(file=str(path.relative_to(output)),sha256=hashlib.sha256(raw).hexdigest())
        changed_sample = dataclasses.replace(sample,Source=path,Digest=row['sha256'])
        geometry = BuildDualSide(sample.Identity,sample.Frame,sample.Profile,sample.FirstMm,sample.SecondMm,sample.FirstTaper,sample.SecondTaper)[0]
        try:
            CheckDualNative(changed_sample,geometry)
            row['passed'] = False
        except ValueError as error:
            row['reason'] = str(error)
            row['passed'] = str(error) == 'Native circular mass cache disagrees with analytic geometry'
    except Exception:
        row.update(passed=False,error=traceback.format_exc().replace(str(root),'<checkout>'))
    report['counterexamples'].append(row)
report['summary'] = dict(archives=len(report['rows']),comparisons=sum(len(r['checks']) for r in report['rows']),failed=sum(not c['passed'] for r in report['rows'] for c in r['checks']),errors=sum('error' in r for r in report['rows']),counterexamples=len(report['counterexamples']),counterexample_passes=sum(r['passed'] for r in report['counterexamples']))
(output/'Receipt.json').write_text(json.dumps(report,indent=2,sort_keys=True))
print(json.dumps(report['summary'],indent=2))
