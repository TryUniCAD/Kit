import sys,pathlib,json,hashlib,traceback
root=pathlib.Path(sys.argv[1]);source=pathlib.Path(sys.argv[2]);folder=pathlib.Path(sys.argv[3]);folder.mkdir(parents=True,exist_ok=True);sys.path.insert(0,str(root/'src'))
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.adapters.Fusion.State.EncodeState import EncodeState
if any((folder/name).exists() for name in ('Receipt.json','TypedState.json','Reconstructed.f3d')):raise FileExistsError('read write evidence already exists')
result=dict(tool_sha256=hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),status='started',contract='typed same-document reconstruction, not neutral conversion')
try:
 model=ReadDocument(source.read_bytes())
 result['read']='passed'
 result['source_snapshot_widths']=[dict(member=v.Name,width=getattr(v.Snapshot.Header,'IntWidth',None)) for v in model.Snapshots if hasattr(v.Snapshot,'Header')]
 try:(folder/'TypedState.json').write_text(json.dumps(EncodeState(model),indent=2));result['typed_json']='passed'
 except Exception:result['typed_json_error']=traceback.format_exc()
 data=EmitParsed(model)
 reopened=ReadDocument(data)
 result['output_snapshot_widths']=[dict(member=v.Name,width=getattr(v.Snapshot.Header,'IntWidth',None)) for v in reopened.Snapshots if hasattr(v.Snapshot,'Header')]
 result.update(status='passed' if reopened==model else 'failed',model_equal=reopened==model,byte_equal=data==source.read_bytes(),output_sha256=hashlib.sha256(data).hexdigest())
 if reopened==model:(folder/'Reconstructed.f3d').write_bytes(data)
except Exception:result['status']='failed';result['traceback']=traceback.format_exc()
(folder/'Receipt.json').write_text(json.dumps(result,indent=2))
sys.exit(0 if result['status']=='passed' else 2)
