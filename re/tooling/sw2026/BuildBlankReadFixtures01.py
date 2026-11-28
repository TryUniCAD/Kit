from __future__ import annotations

import argparse
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import sys
from uuid import UUID

p=argparse.ArgumentParser()
p.add_argument('--code',type=Path,required=True)
p.add_argument('--request',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args()
sys.path[:0]=[str(a.code/'src'),str(Path(__file__).parent)]
from DrawingSdkInput import blank_input
from convert.adapters.solidworks.Drawing.Construction.Portable.MakeBlankFile import MakeBlankFile

raw=a.request.read_bytes()
assert sha256(raw).hexdigest()=='2a4de479d71866c9b985797815875b54c57468684efcbafdff10b1978fb55b1c'
base=json.loads(raw)
recipes=[]
for index,name in enumerate(('Kappa','Lambda','Mu','Nu')):
    job=deepcopy(base)
    created=1795000000+index*173
    sheet='Independent '+name+(' Ω & “x”' if index==1 else '')
    model='ReadBlank'+name
    job['drawing']['ActiveSheetId']='neutral-'+name.lower()
    job['drawing']['Sheets'][0].update(EntityId='neutral-'+name.lower(),EntityName=sheet,ScaleRatio=([29,31],[37,11],[5,23],[41,17])[index])
    job['options'].update(name=model,property_view='Profile '+name,created_at=created,block_identity=str(UUID(bytes=sha256(('ordinary blank reader '+name).encode()).digest()[:16],version=4)),auto_dim_text_link=index%2==0)
    job['options']['sheet_names'].update(plane_name=name+' plane',profile_name=name+' profile',detail_name=name+' detail')
    for key in job['options']['folder_names']:
        job['options']['folder_names'][key]=name+' '+key.replace('_',' ')
    styles=job['options']['styles']
    styles.update(font_name=('Arial','Tahoma','Consolas','Calibri')[index],line_style_name=name+' line',language_id=1037 if index==2 else 1033,
                  print_widths_m=[(13+offset*3+index)*1e-6 for offset in range(8)],exclusion_names=[name+' A',name+' B'],task_labels=[name+' '+str(offset) for offset in range(5)],cutlist_expressions=[name+' '+str(offset) for offset in range(3)])
    job['options']['units'].update(length_unit=('mm','in','cm','m')[index],angle_unit=('degree','radian','arcminute','arcsecond')[index],unit_system=('mmgs','ips','cgs','mks')[index],decimal_places=(4,6,3,8)[index])
    job['provenance'].update(author='Author '+name,company='Company & '+name,comment='Source-owned '+name+' chronology',created_at=created,modified_at=created+23,updated_at=created+17,
                             originating_build_code=2026123+index,license_origin=(0,10,20,30)[index],language_id=1041 if index==3 else 1033,cjk_saved=index==3)
    job['ui'].update(drafting_standard=('moANSI_c','moISO_c','moDIN_c','moJIS_c')[index],detail_flags=([1,31],[7,32,63],[0,17,48],[3,16,62])[index],tessellation=[31+index,5+index,29-index,index%2==1],system_preference_7a=index%2==0,journal_name='Journal '+name)
    job['output'].update(path_name='C:\\IndependentBlankReader\\'+name+'.SLDDRW',saved_at=created+97)
    candidate=MakeBlankFile(blank_input(job))
    path=a.output/(name+'.SLDDRW')
    with path.open('xb') as f:
        f.write(candidate.BytesValue)
    request=a.output/(name+'.json')
    with request.open('x') as f:
        json.dump(job,f,indent=2,allow_nan=False)
    recipes.append({'name':name,'path':str(path),'sha256':sha256(candidate.BytesValue).hexdigest(),'request_path':str(request),'request_sha256':sha256(request.read_bytes()).hexdigest(),'stream_lengths':{k:len(v) for k,v in candidate.StreamsValue.items()},'producer':'Kit SDK construction, independent neutral read-control only'})
manifest={'schema':'kit.sw2026.blank-reader-generated-fixtures.v1','neutral_base_sha256':sha256(raw).hexdigest(),'cases':recipes,'native_source_files_read':0,'vendor_runtime_executed':False,'native_acceptance':False}
with (a.output/'Manifest.json').open('x') as f:
    json.dump(manifest,f,indent=2)
print(json.dumps({'passed':True,'cases':len(recipes),'manifest_sha256':sha256((a.output/'Manifest.json').read_bytes()).hexdigest(),'native_source_reads':0}))
