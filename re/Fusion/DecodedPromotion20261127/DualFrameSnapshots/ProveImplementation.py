from pathlib import Path
import json,hashlib,sys
root=Path(__file__).resolve().parents[4]
sys.path[:0]=[str(root/'src'),str(root)]
from tests.Convert.Integration.Fusion.DualFrameSnapshots.CheckFramedSnap import CheckFramedSnap
from tests.Convert.Integration.Fusion.DualSide.ReadDualCases import ReadDualCases
from interchange.geometry.Models.Transform import Transform
rows=[]
for sample in ReadDualCases():
    data=sample.Source.read_bytes();assert hashlib.sha256(data).hexdigest()==sample.Digest
    row={'source':str(sample.Source.relative_to(root)),'sha256':sample.Digest,'identity_frame':sample.Frame==Transform()}
    try:
        CheckFramedSnap(data,sample.Frame);row['qualified_status']='passed'
    except Exception as error:row.update(qualified_status='failed',qualified_error=type(error).__name__+': '+str(error))
    try:
        CheckFramedSnap(data);row['default_status']='passed'
    except Exception as error:row.update(default_status='refused',default_error=type(error).__name__+': '+str(error))
    rows.append(row)
files=[*sorted((root/'src/convert/adapters/Fusion/Native/Circular/DualSnapshots').glob('*.py')),*sorted((root/'src/convert/adapters/Fusion/Native/Circular/DualFrames').glob('*.py')),*sorted((root/'tests/Convert/Integration/Fusion/DualFrameSnapshots').glob('*.py'))]
report={'program_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'producer_source_hashes':{str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files},'native_calls':0,'models':False,'sources':rows,'summary':{'qualified_passes':sum(r['qualified_status']=='passed' for r in rows),'default_xy_passes':sum(r['identity_frame'] and r['default_status']=='passed' for r in rows),'default_xz_refusals':sum(not r['identity_frame'] and r['default_status']=='refused' for r in rows)}}
counterdir=Path(__file__).parent/'Counterexamples';counterreport=json.loads((counterdir/'Counterexamples.json').read_text());sample=next(s for s in ReadDualCases() if s.Identity=='frame');counterrows=[]
for counter in counterreport['counterexamples']:
    data=(counterdir/counter['file']).read_bytes();assert hashlib.sha256(data).hexdigest()==counter['sha256'];row={'mode':counter['mode'],'file':counter['file'],'sha256':counter['sha256']}
    try:CheckFramedSnap(data,sample.Frame);row['status']='unexpected_accept'
    except ValueError as error:row.update(status='refused',message=str(error))
    counterrows.append(row)
report['counterexamples']=counterrows;report['summary']['encoded_counterexample_refusals']=sum(r['status']=='refused' for r in counterrows)
Path(sys.argv[1]).write_text(json.dumps(report,indent=2)+'\n');print(report['summary'])
