import hashlib
import json
from pathlib import Path
import subprocess
import sys
import traceback

from convert.adapters.Fusion.Native.Circular.DualFrames.ReadDualFrame import ReadDualFrame
from convert.adapters.Fusion.Native.Circular.DualFrames.LocalDualView import LocalDualView
from convert.adapters.Fusion.Native.Circular.DualSides.CheckDualLive import CheckDualLive
from convert.adapters.Fusion.Native.Circular.DualSides.ReadDualLive import ReadDualLive
from convert.adapters.Fusion.State.EncodeState import EncodeState
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from tests.Convert.Integration.Fusion.DualFrameLive.ChangeFrameDoc import ChangeFrameDoc
from tests.Convert.Integration.Fusion.DualSide.ReadDualCases import ReadDualCases
from tests.Convert.Integration.Fusion.DualSide.Tags.ReadTagSample import ReadTagSample
from dataclasses import replace

root=Path(sys.argv[1]).resolve(); output=Path(sys.argv[2]).resolve();output.mkdir(exist_ok=False)
(output/'Documents').mkdir();(output/'Candidates').mkdir()
folder=Path(__file__).parent
paths=list((root/'src/convert/adapters/Fusion/Native/Circular/DualFrames').glob('*.py'))+[root/'src/convert/adapters/Fusion/Native/Circular/DualSides'/(n+'.py') for n in ('CheckDualLive','CheckDualCover','CheckDualGeo')]+list((root/'tests/Convert/Integration/Fusion/DualFrameLive').glob('*.py'))+[Path(__file__)]
report=dict(base_revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),models=False,native_calls=0,rule_sha256=hashlib.sha256((folder/'Rules.md').read_bytes()).hexdigest(),sources={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},positive=[],negative=[])
for sample in ReadDualCases():
 if sample.Frame.z_axis.y!=1: continue
 row=dict(identity=sample.Identity,source=str(sample.Source.relative_to(root)),sha256=sample.Digest)
 try:
  model,graph,context,shape=ReadTagSample(sample);frame=ReadDualFrame(graph,context)
  state=CheckDualLive(graph,context,model,shape,sample.FirstMm,sample.SecondMm,sample.FirstTaper,sample.SecondTaper,frame)
  local=LocalDualView(state,frame)
  row.update(passed=frame==sample.Frame and state==ReadDualLive(model.Bodies[0].History,context.Extrude.Fields['endModelHS']) and len(state.Entities)==len(local.Entities)==48,world_entities=len(state.Entities),local_entities=len(local.Entities),frame={name:[getattr(frame,name).x,getattr(frame,name).y,getattr(frame,name).z] for name in ("origin","x_axis","y_axis","z_axis")})
  row['documents']={}
  for role,value in [('World',state),('Local',local)]:
   path=output/'Documents'/(sample.Identity+'_'+role+'.json');path.write_text(json.dumps(EncodeState(value),indent=2,sort_keys=True));row['documents'][str(path.relative_to(output))]=hashlib.sha256(path.read_bytes()).hexdigest()
 except Exception: row.update(passed=False,error=traceback.format_exc().replace(str(root),'<checkout>'))
 report['positive'].append(row)
sample=next(s for s in ReadDualCases() if s.Identity=='frame')
for mode in ('body_transform','ucs_matrix','definition_matrix','occurrence_matrix','datum_name','datum_origin','datum_owner','definition_owner','definition_active','definition_inferred','reference_scope','update_owner','update_health','instance_owner'):
 row=dict(mode=mode,source_sha256=sample.Digest)
 try:
  model,_,_,_=ReadTagSample(sample);raw=EmitParsed(ChangeFrameDoc(model,mode));path=output/'Candidates'/(mode+'.f3d');path.write_bytes(raw);row.update(candidate=str(path.relative_to(output)),sha256=hashlib.sha256(raw).hexdigest(),emitted=True)
  changed=replace(sample,Source=path,Digest=row['sha256']);model,graph,context,shape=ReadTagSample(changed);row['reparsed']=True
  try:
   frame=ReadDualFrame(graph,context);_=CheckDualLive(graph,context,model,shape,sample.FirstMm,sample.SecondMm,sample.FirstTaper,sample.SecondTaper,frame);row.update(passed=False,error='unexpected admission')
  except (ValueError,TypeError) as exc: row.update(passed=True,refusal=str(exc))
 except Exception: row.update(passed=False,error=traceback.format_exc().replace(str(root),'<checkout>'))
 report['negative'].append(row)
report['summary']=dict(positives=len(report['positive']),positive_passed=sum(x['passed'] for x in report['positive']),negatives=len(report['negative']),negative_passed=sum(x['passed'] for x in report['negative']),actual_archive_emissions=sum(x.get('emitted',False) for x in report['negative']),actual_archive_reparses=sum(x.get('reparsed',False) for x in report['negative']))
(output/'Receipt.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(report['summary']))
