import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
parser=argparse.ArgumentParser();parser.add_argument('--sdk',type=Path,required=True);parser.add_argument('--source',type=Path,required=True);parser.add_argument('--sha256',required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();sys.dont_write_bytecode=True;sys.path.insert(0,str(args.sdk/'src'))
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Archive.Definition.ReadModelDef import ReadModelDef
from convert.adapters.solidworks.Archive.Definition.WriteModelDef import WriteModelDef
raw=args.source.read_bytes();assert sha256(raw).hexdigest()==args.sha256;archive=SldprtArchive.from_bytes(raw);data=archive.require('Contents/Definition');graph=ReadModelDef(data,19000).GraphValue;assert WriteModelDef(graph).OutputValue==data;fields=graph.DocumentValue.FieldsValue;styles=fields['f878']['styles'];fonts=fields['f870'].FieldsValue['f10']
def native_hash(text):
 units=[int.from_bytes(text.encode('utf-16-le')[i:i+2],'little') for i in range(0,len(text.encode('utf-16-le')),2)];value=0x811c9dc5;stride=(len(units)*0xcccccccd>>35)+1
 for unit in units[::stride]:value=((value*0x1000193)^unit)&0xffffffff
 return value
stylekeys=[row['o'].FieldsValue['f08'] for row in styles];rows=[{'key':row['key'],'font_key':row['cfg'].FieldsValue['f08'],'hash':native_hash(row['key']),'bucket':native_hash(row['key'])%17,'width':row['cfg'].FieldsValue['f10'],'end_cap':row['cfg'].FieldsValue['f18'],'map_index':row['cfg'].IndexValue} for row in fonts];ordered=[row['bucket'] for row in rows];out={'schema':'kit.sw2026.disclosed-line-owner-inspection.v1','source_sha256':args.sha256,'definition_round_trip':True,'font_count':len(fonts),'unique_font_objects':len({id(row['cfg']) for row in fonts}),'font_categories_unique':len({row['key'] for row in rows})==len(rows),'native_17_bucket_order':ordered==sorted(ordered),'style_count':len(styles),'style_keys':stylekeys,'style_distinct_objects':len({id(row['o']) for row in styles}),'standard_width_codes':sorted({row['width']['f06'] for row in rows}),'custom_width_values':sorted({row['width']['f00'] for row in rows}),'end_cap_codes':sorted({row['end_cap'] for row in rows}),'font_names_without_declared_style':sorted({row['font_key'] for row in rows}-set(stylekeys)),'starred_categories':[row['key'] for row in rows if '*' in row['key']],'rows':rows,'styles':[{'internal_name':row['o'].FieldsValue['f08'],'display_name':row['o'].FieldsValue['f10'],'segments':[item['seg'] for item in row['o'].FieldsValue['f18']],'thick_thin':row['o'].FieldsValue['f20']} for row in styles],'native_processes':0,'heldout_inputs_read':0};assert not args.output.exists();args.output.write_text(json.dumps(out,sort_keys=True,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ('rows','styles')}))
