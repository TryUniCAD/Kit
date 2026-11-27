import hashlib
import json
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[4]
sys.path[:0] = [str(root / 'src'), str(root)]
from tests.Convert.Integration.Fusion.DualSide.ReadDualCases import ReadDualCases
from tests.Convert.Integration.Fusion.DualSide.ReadDualState import ReadDualState
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Graph.SelectExtrusion import SelectExtrusion
from convert.adapters.Fusion.Native.Circular.ReadCircle import ReadCircle
from convert.adapters.Fusion.Native.Circular.DualSnapshots.CheckDualSnaps import CheckDualSnaps

rows = []
for sample in ReadDualCases():
    row = {'source': str(sample.Source.relative_to(root)), 'sha256': sample.Digest, 'xy': sample.Frame.z_axis.z == 1.0, 'holdout': sample.Identity.startswith('holdout')}
    try:
        data = sample.Source.read_bytes()
        assert hashlib.sha256(data).hexdigest() == sample.Digest
        model = ReadDocument(data)
        graph = BuildGraph(model)
        context = SelectExtrusion(graph)
        shape = ReadCircle(graph, context)
        live = ReadDualState(model.Bodies[0].History, context.Extrude.Fields['endModelHS'])
        CheckDualSnaps(model, graph, context, shape, live)
        row.update(status='accepted', snapshot_entities=len(model.Snapshots[0].Snapshot.Entities))
    except Exception as error:
        row.update(status='refused', exception=type(error).__name__, message=str(error).replace(str(root), '<checkout>'))
    rows.append(row)
files = sorted((root / 'src/convert/adapters/Fusion/Native/Circular/DualSnapshots').glob('*.py'))
report = {'program_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'source_module_hashes': {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}, 'native_calls': 0, 'models': False, 'sources': rows, 'summary': {'xy': sum(r['xy'] for r in rows), 'xy_accepted': sum(r['xy'] and r['status'] == 'accepted' for r in rows), 'xz': sum(not r['xy'] for r in rows), 'xz_refused': sum(not r['xy'] and r['status'] == 'refused' for r in rows)}}
Path(sys.argv[1]).write_text(json.dumps(report,indent=2)+'\n')
print(report['summary'])
