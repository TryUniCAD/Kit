import argparse,dataclasses,json,pathlib,sys
parser=argparse.ArgumentParser()
parser.add_argument('--root',type=pathlib.Path,required=True)
parser.add_argument('--source',type=pathlib.Path,required=True)
parser.add_argument('--target',type=pathlib.Path,required=True)
parser.add_argument('--field',choices=['IntWidth','Scale','Flags','RootCount','AbsoluteTolerance','NormalTolerance'],required=True)
args=parser.parse_args();sys.path.insert(0,str(args.root/'src'))
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.Formats.Fusion.BrepCodec.Models.SnapshotModel import SnapshotModel
model=ReadDocument(args.source.read_bytes());updates=[];changed=False
for item in model.Snapshots:
 if not changed and isinstance(item.Snapshot,SnapshotModel):
  value={'IntWidth':16,'Scale':1.0,'Flags':3,'RootCount':3,'AbsoluteTolerance':1e-5,'NormalTolerance':1e-8}[args.field]
  item=dataclasses.replace(item,Snapshot=dataclasses.replace(item.Snapshot,Header=dataclasses.replace(item.Snapshot.Header,**{args.field:value})));changed=True
 updates.append(item)
if not changed:raise ValueError('source has no specialized cylinder snapshot')
try:
 payload=EmitParsed(dataclasses.replace(model,Snapshots=tuple(updates)))
except ValueError as error:
 print(json.dumps(dict(status='refused',message=str(error),field=args.field)));sys.exit(0)
args.target.write_bytes(payload)
raise RuntimeError('unsupported header unexpectedly emitted')
