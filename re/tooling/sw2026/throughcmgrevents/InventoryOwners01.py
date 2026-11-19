import argparse
from base64 import b64decode
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import sys

parser=argparse.ArgumentParser();parser.add_argument('--sdk',type=Path,required=True);parser.add_argument('--source',type=Path,required=True);parser.add_argument('--sha256',required=True);parser.add_argument('--definition-build',type=Path,required=True);parser.add_argument('--member-build',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();sys.dont_write_bytecode=True;sys.path.insert(0,str(args.sdk/'src'))
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Archive.Definition.ReadModelDef import ReadModelDef
from convert.adapters.solidworks.Archive.Definition.WriteModelDef import WriteModelDef
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode

require=lambda value,message:None if value else (_ for _ in ()).throw(ValueError(message))
def digest(value):return sha256(value).hexdigest()
def summary(value,depth=0,seen=None):
 if seen is None:seen=set()
 if isinstance(value,ArchiveNode):
  if id(value) in seen:return {'class':value.ClassValue.NameValue,'alias':True,'native_id':value.FieldsValue.get('f08')}
  seen.add(id(value));return {'class':value.ClassValue.NameValue,'schema':value.ClassValue.SchemaValue,'native_id':value.FieldsValue.get('f08'),'fields':summary(value.FieldsValue,depth+1,seen)} if depth<3 else {'class':value.ClassValue.NameValue,'schema':value.ClassValue.SchemaValue,'native_id':value.FieldsValue.get('f08'),'field_keys':sorted(value.FieldsValue)}
 if isinstance(value,dict):return {k:summary(v,depth+1,seen) for k,v in value.items()} if depth<4 else {'keys':sorted(value),'scalar_fields':{k:v for k,v in value.items() if v is None or type(v) in (bool,int,float,str)}}
 if isinstance(value,(list,tuple)):return [summary(x,depth+1,seen) for x in value] if len(value)<=12 and depth<5 else {'count':len(value),'head':[summary(x,depth+1,seen) for x in value[:3]]}
 if hasattr(value,'TextValue'):return value.TextValue
 return value

def differences(left,right,path,seen=None):
 if seen is None:seen=set()
 composite=isinstance(left,(ArchiveNode,dict,list,tuple)) and isinstance(right,(ArchiveNode,dict,list,tuple))
 if composite:
  if (id(left),id(right)) in seen:return []
  seen.add((id(left),id(right)))
 if isinstance(left,ArchiveNode) and isinstance(right,ArchiveNode):
  if left.ClassValue!=right.ClassValue:return [{'path':path+'/@class','source':summary(left),'generated':summary(right)}]
  return differences(left.FieldsValue,right.FieldsValue,path,seen)
 if isinstance(left,dict) and isinstance(right,dict):
  result=[]
  for key in sorted(set(left)|set(right)):
   if key not in left or key not in right:result.append({'path':path+'/'+key,'source':summary(left.get(key)),'generated':summary(right.get(key)),'absent': 'source' if key not in left else 'generated'})
   else:result.extend(differences(left[key],right[key],path+'/'+key,seen))
  return result
 if isinstance(left,(list,tuple)) and isinstance(right,(list,tuple)):
  if len(left)!=len(right):return [{'path':path+'/@length','source':summary(left),'generated':summary(right),'source_count':len(left),'generated_count':len(right)}]
  return [row for i,(a,b) in enumerate(zip(left,right,strict=True)) for row in differences(a,b,path+'/'+str(i),seen)]
 return [] if left==right else [{'path':path,'source':summary(left),'generated':summary(right)}]

raw=args.source.read_bytes();require(digest(raw)==args.sha256,'disclosed source hash differs');archive=SldprtArchive.from_bytes(raw);original_def=archive.require('Contents/Definition');source_def=ReadModelDef(original_def,19000);original_mgr=archive.require('Contents/CMgr');source_mgr=ReadCmgrMut(original_mgr,19000);definition_json=json.loads(args.definition_build.read_text());member_json=json.loads(args.member_build.read_text());generated_def=b64decode(definition_json['definition_payload'],validate=True);generated_mgr=b64decode(member_json['payloads']['manager'],validate=True);built_def=ReadModelDef(generated_def,19000);built_mgr=ReadCmgrMut(generated_mgr,19000)
require(WriteModelDef(source_def.GraphValue).OutputValue==original_def,'source Definition round trip differs');require(WriteCmgrMut(source_mgr.RootValue,19000)==original_mgr,'source CMgr round trip differs');require(WriteModelDef(built_def.GraphValue).OutputValue==generated_def,'generated Definition round trip differs');require(WriteCmgrMut(built_mgr.RootValue,19000)==generated_mgr,'generated CMgr round trip differs')
rows=[]
for label,left,right in (('Definition',source_def.GraphValue.DocumentValue,built_def.GraphValue.DocumentValue),('CMgr',source_mgr.RootValue,built_mgr.RootValue)):
 changes=differences(left,right,label);grouped=Counter('/'.join(row['path'].split('/')[:3]) if row['path'].startswith('CMgr/f360/') else '/'.join(row['path'].split('/')[:2]) for row in changes);rows.append({'stream':label,'changed_frontier_paths':len(changes),'owner_counts':dict(grouped),'differences':changes})
output={'schema':'kit.sw2026.throughall-remaining-document-owners.v1','source_sha256':args.sha256,'four_stream_round_trips':True,'comparator':'encoded graphs; one unequal-length array marker; composite identity pairs deduplicated, scalar occurrences counted independently','rows':rows,'native_launches':0,'heldout_inputs_read':0};require(not args.output.exists(),'output must be absent');args.output.write_text(json.dumps(output,sort_keys=True,indent=2)+'\n');print(json.dumps({'passed':True,'sha256':digest(args.output.read_bytes()),'counts':[{k:v for k,v in row.items() if k!='differences'} for row in rows]}))
