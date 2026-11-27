import hashlib
import json
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[4]
sys.path[:0] = [str(root / 'src'), str(root)]
from tests.Convert.Integration.Fusion.DualSide.ReadDualCases import ReadDualCases
from tests.Convert.Integration.Fusion.DualSnapshots.CheckSavedSnap import CheckSavedSnap
from tests.Convert.Integration.Fusion.DualSnapshots.MakeBadSnap import MakeBadSnap
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument

output = Path(sys.argv[1])
output.mkdir(exist_ok=False, parents=True)
sample = next(s for s in ReadDualCases() if s.Identity == 'baseline')
rows = []
for mode in ('identity', 'feature', 'sketch', 'body', 'geometry'):
    data = MakeBadSnap(sample.Source.read_bytes(), mode)
    path = output / (mode + '.f3d')
    path.write_bytes(data)
    model = ReadDocument(data)
    row = {'mode': mode, 'file': path.name, 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data), 'decoded_snapshot_type': type(model.Snapshots[0].Snapshot).__name__}
    try:
        CheckSavedSnap(data)
        row['status'] = 'unexpected_accept'
    except ValueError as error:
        row.update(status='refused', message=str(error))
    rows.append(row)
report = {'program_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'source':str(sample.Source.relative_to(root)), 'source_sha256':sample.Digest, 'native_calls':0, 'models':False, 'counterexamples':rows}
(output / 'Counterexamples.json').write_text(json.dumps(report,indent=2)+'\n')
print({'counterexamples':len(rows),'refused':sum(x['status']=='refused' for x in rows)})
