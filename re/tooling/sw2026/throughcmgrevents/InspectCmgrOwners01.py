import argparse
from datetime import datetime,timezone
from hashlib import sha256
import json
from pathlib import Path
import sys

parser=argparse.ArgumentParser();parser.add_argument('--sdk',type=Path,required=True);parser.add_argument('--source',type=Path,required=True);parser.add_argument('--sha256',required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();sys.dont_write_bytecode=True;sys.path.insert(0,str(args.sdk/'src'))
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Members.ReadMemberTime import ReadMemberTime
from dataclasses import asdict
raw=args.source.read_bytes();assert sha256(raw).hexdigest()==args.sha256;archive=SldprtArchive.from_bytes(raw);wire=archive.require('Contents/CMgr');g=ReadCmgrMut(wire,19000);assert WriteCmgrMut(g.RootValue,19000)==wire;root=g.RootValue;config=root.FieldsValue['f360'];rows=root.FieldsValue['f370']['items'];link=ReadNativeLink(archive,0)
def state(node):
 fields=node.FieldsValue;moment=ReadMemberTime(node);keys=('f08','f0c','f2c','f29c','f2a0','f2a4','f2ac','f2b0','f2b4','f2b8','f2bc','f300','f301','f658','f6f8','f85c','f860');name=fields.get('f18');return {'class':node.ClassValue.NameValue,'schema':node.ClassValue.SchemaValue,'map_index':node.IndexValue,'name':None if name is None else name.FieldsValue['f08'],'moment':asdict(moment),'moment_utc':datetime.fromtimestamp(moment.SecondsValue,timezone.utc).isoformat(),'fields':{key:fields[key] for key in keys if key in fields}}
out={'schema':'kit.sw2026.disclosed-cmgr-feature-owner-observation.v1','source_sha256':args.sha256,'manager':state(root),'config':state(config),'manager_is_config':root is config,'current_alias':root.FieldsValue['f368'] is config,'current_in_config_rows':len(rows)==1 and rows[0]['o'] is config,'linked_model_class':link.ConfigValue.RootValue.ClassValue.NameValue,'linked_model_native_id':link.ConfigValue.RootValue.FieldsValue['f08'],'native_processes':0,'heldout_inputs_read':0,'wire_reemit_exact':True};assert not args.output.exists();args.output.write_text(json.dumps(out,sort_keys=True,indent=2)+'\n');print(json.dumps(out,sort_keys=True))
