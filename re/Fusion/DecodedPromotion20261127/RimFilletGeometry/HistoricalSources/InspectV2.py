from pathlib import Path
import json,hashlib,subprocess
from collections import Counter
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.State.EncodeState import EncodeState
from convert.adapters.Fusion.Native.Circular.DualSides.ReadDualLive import ReadDualLive
from convert.Formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel

root=Path.cwd();output=Path(__file__).parent/'Discovery';output.mkdir(exist_ok=True)
rows=[]
for index in range(1,7):
 name=f'discovery-{index:02}';path=root/'re/Fusion/RimFilletPack/Sources'/name/'Native.f3d';raw=path.read_bytes();model=ReadDocument(raw);graph=BuildGraph(model)
 nodes=[n for n in graph.Nodes.values() if any(s in n.ClassName for s in ('Fillet','Radius','Blend','Progenitor')) or n.ClassName in ('DcExtrudeFeature','DcBody','Body','Parameter','DcDoubleParameter','ModelDataRef','BrepRef','ASMRecipe')]
 packet={'source':str(path.relative_to(root)),'sha256':hashlib.sha256(raw).hexdigest(),'nodes':[{ 'id':n.ObjectId,'class':n.ClassName,'fields':EncodeState(n.Fields)} for n in nodes], 'body_type':type(model.Bodies[0].History).__name__,'snapshot_types':[type(s.Snapshot).__name__ for s in model.Snapshots]}
 history=model.Bodies[0].History
 if isinstance(history,JournalModel):
  packet['stream']=EncodeState(history.Stream);packet['states']={}
  for feature in graph.ByClass('DcExtrudeFeature')+graph.ByClass('DcFilletFeature'):
   for field in ('startModelHS','endModelHS'):
    stateid=feature.Fields[field]
    state=ReadDualLive(history,stateid);packet['states'][str(stateid)]=EncodeState(state)
 (output/(name+'.json')).write_text(json.dumps(packet,indent=2,sort_keys=True))
 rows.append({k:v for k,v in packet.items() if k not in ('nodes','states')})
 print(name,packet['body_type'],[(n.ClassName,n.ObjectId) for n in nodes if 'Fillet' in n.ClassName],packet['snapshot_types'])
report=dict(revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),models=False,native_calls=0,rows=rows)
(output/'Receipt.json').write_text(json.dumps(report,indent=2,sort_keys=True))
