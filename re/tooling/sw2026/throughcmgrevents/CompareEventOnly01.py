import argparse
from base64 import b64decode
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path);parser.add_argument('--python',type=Path);parser.add_argument('--replay',type=Path);parser.add_argument('--output',type=Path);parser.add_argument('--sdk',type=Path);parser.add_argument('--worker',action='store_true');args=parser.parse_args();sys.dont_write_bytecode=True
def require(value,message):
 if not value:raise ValueError(message)
def digest(path):return sha256(path.read_bytes()).hexdigest()
def worker():
 from codecs import lookup
 sys.path.insert(0,str(args.sdk/'src'));sys.path.insert(0,str(args.sdk/'re/tooling/sw2026/throughowners'))
 from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
 from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
 from convert.adapters.solidworks.Archive.Construction.Configuration.Events.RequireCmgr import RequireCmgr
 from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
 from OwnerGuard import OwnerGuard
 for codec in ('utf-16-le','utf-8','ascii','latin-1'):lookup(codec)
 request=json.load(sys.stdin);guard=OwnerGuard();sys.addaudithook(guard.inspect);sys.setprofile(guard.profile);guard.active=True
 def changes(first,second,path,seen=None):
  if seen is None:seen=set()
  if isinstance(first,(ArchiveNode,dict,list,tuple)) and isinstance(second,(ArchiveNode,dict,list,tuple)):
   if (id(first),id(second)) in seen:return []
   seen.add((id(first),id(second)))
  if isinstance(first,ArchiveNode) and isinstance(second,ArchiveNode):
   require(first.ClassValue==second.ClassValue,'event composition changed a native class');return changes(first.FieldsValue,second.FieldsValue,path,seen)
  if isinstance(first,dict) and isinstance(second,dict):
   require(set(first)==set(second),'event composition added or removed native fields');return [row for key in sorted(first) for row in changes(first[key],second[key],path+'/'+key,seen)]
  if isinstance(first,(list,tuple)) and isinstance(second,(list,tuple)):
   require(len(first)==len(second),'event composition changed native collection cardinality');return [row for index,(a,b) in enumerate(zip(first,second,strict=True)) for row in changes(a,b,path+'/'+str(index),seen)]
  return [] if type(first) is type(second) and first==second else [path]
 def words(event):
  moment=event['MomentValue'];creator=event['CreatedBy'];ticks=(moment['SecondsValue']+11644473600)*10000000+moment['FractionTicks'];parts=(ticks&0xffffffff,ticks>>32);low,high=(part-(1<<32) if part&(1<<31) else part for part in parts);return {'f2a0':low,'f2a4':high,'f2b0':creator['FileVersion'],'f2b4':creator['DateCode'],'f2ac':creator['ParasolidVersion'],'f300':creator['ServicePack'],'f301':creator['SubservicePack']}
 try:
  graphs=[]
  for key in ('before','after'):
   wire=b64decode(request[key],validate=True);graph=ReadCmgrMut(wire,19000);require(graph.ReportValue['completed'] and not graph.ReportValue['missing_schemas'] and not graph.ReportValue['provisional_schemas'],'event comparison reached unqualified grammar');require(WriteCmgrMut(graph.RootValue,19000)==wire,'event comparison CMgr wire did not reemit');graphs.append(graph.RootValue)
  before,after=graphs;expected=[]
  for prefix,left,right,event in (('CMgr',before,after,request['events']['ManagerValue']),('CMgr/f360',RequireCmgr(before),RequireCmgr(after),request['events']['ActiveValue'])):
   for key,value in words(event).items():
    require(type(right.FieldsValue[key]) is int and right.FieldsValue[key]==value,'exact composed event operand differs')
    if left.FieldsValue[key]!=value:expected.append(prefix+'/'+key)
  actual=changes(before,after,'CMgr');require(sorted(actual)==sorted(expected),'manager event changed another native owner');result={'schema':'kit.sw2026.cmgr-event-only-graph-comparison.v1','passed':True,'changed_paths':sorted(actual),'other_native_fields_and_collection_classes_exact':True,'actual_selected_aliases_preserved':True,'manager_stream_round_trips':2,'guarded_input_reads':0,'denied_events':guard.denied,'native_processes':0,'heldout_inputs_read':0}
 except Exception as error:result={'passed':False,'error_type':type(error).__name__,'error':str(error),'denied_events':guard.denied}
 finally:guard.active=False;sys.setprofile(None)
 print(json.dumps(result,sort_keys=True));raise SystemExit(0 if result['passed'] else 3)
def parent():
 root=args.root;replay=args.replay;out=args.output;out.mkdir(exist_ok=False);report=json.loads((replay/'Replay.json').read_text());manifest=json.loads((root/'SourceManifest01.json').read_text());binding=json.loads((root/'ComparisonBinding01.json').read_text())
 def verify():
  require(digest(root/'SourceManifest01.json')==binding['source_manifest_sha256'] and digest(replay/'Replay.json')==binding['process_report_sha256'] and digest(Path(__file__))==binding['comparison_tool_sha256'],'event comparison freeze differs');require(report['passed'] and report['source_manifest_sha256']==binding['source_manifest_sha256'],'original event replay not qualified')
  actual={str(p.relative_to(root/'Code01')):digest(p) for p in sorted((root/'Code01').rglob('*')) if p.is_file() and not any(x in p.parts for x in ('__pycache__','.mypy_cache','.ruff_cache'))};require(actual==manifest['candidate'],'event SDK closure differs')
  for row in report['records']:require(digest(replay/(row['label']+'.json'))==row['record_sha256'],'main process record differs')
 verify();cases=[]
 for name in ('D01','D02'):
  source=json.loads((replay/name/'Source.json').read_text());cases.append((name,name,source['events']))
 for index,row in enumerate(report['positive_cases'][2:],1):cases.append(('Independent'+str(index),'D01',row['semantic_events']))
 records=[]
 for label,baseline,event in cases:
  before=json.loads((replay/baseline/'OldCallerBaseline.json').read_text());after=json.loads((replay/label/'BuildA.json').read_text());request={'before':before['payloads']['manager'],'after':after['payloads']['manager'],'events':event};proc=subprocess.run([str(args.python),'-B',str(Path(__file__).resolve()),'--worker','--sdk',str(root/'Code01')],input=json.dumps(request),capture_output=True,text=True,timeout=120);path=out/(label+'.json');path.write_text(proc.stdout);path.with_suffix('.stderr.txt').write_text(proc.stderr);require(proc.stdout and proc.returncode==0,'whole graph comparison failed '+label+' '+proc.stdout[-500:]+proc.stderr[-500:]);result=json.loads(proc.stdout);require(result['passed'] and not result['denied_events'],'graph comparison refused or used external files');records.append({'case':label,'record_sha256':digest(path),'changed_paths':result['changed_paths'],'all_other_fields_exact':True})
 verify();result={'schema':'kit.sw2026.cmgr-event-only-process-matrix.v1','passed':True,'binding_sha256':digest(root/'ComparisonBinding01.json'),'fresh_process_count':len(records),'manager_stream_round_trips':2*len(records),'runtime_input_reads':0,'heldout_inputs_read':0,'native_processes':0,'complete_source_preparation':False,'public_activation':False,'records':records};path=out/'Replay.json';path.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps({'passed':True,'fresh_process_count':len(records),'sha256':digest(path)}))
worker() if args.worker else parent()
