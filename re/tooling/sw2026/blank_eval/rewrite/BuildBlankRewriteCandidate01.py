from __future__ import annotations

import argparse
from codecs import lookup
from dataclasses import replace
from hashlib import sha256
import importlib
import json
from pathlib import Path
import sys
from uuid import UUID

p=argparse.ArgumentParser()
p.add_argument('--code',type=Path,required=True)
p.add_argument('--manifest',type=Path,required=True)
p.add_argument('--manifest-sha256',required=True)
p.add_argument('--source',type=Path,required=True)
p.add_argument('--source-sha256',required=True)
p.add_argument('--target',type=Path,required=True)
p.add_argument('--epoch',type=int,required=True)
p.add_argument('--report',type=Path,required=True)
a=p.parse_args()


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def verify():
    assert digest(a.manifest)==a.manifest_sha256
    manifest=json.loads(a.manifest.read_bytes())
    for row in manifest['files']:
        assert digest(a.code/row['path'])==row['sha256'],row['path']


verify()
assert a.target.is_absolute() and a.target.suffix=='.SLDDRW' and not a.target.exists() and not a.report.exists()
assert type(a.epoch) is int and 0<=a.epoch<2**32
assert digest(a.source)==a.source_sha256
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parent))
from BlankRewriteGuard import OutputGuard
sys.path.insert(0,str(a.code/'src'))
from convert.api import open_document,write_document
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.DrawingWriting.Rewrite.ReadBlankInput import ReadBlankInput
from interchange.document.Models.DocumentModel import CadDocument
from interchange.document.Behavior.DocumentIo import FromJson,ToJson
for name in ('DocumentFeatureValidate','DocumentReferenceValidate','DocumentAssemblyValidate'):
    importlib.import_module('interchange.document.Validation.'+name)
importlib.import_module('interchange.document.Models.DocumentProvenance')
for encoding in ('utf-8','utf-16le','utf-16be','latin-1','cp1252'):
    lookup(encoding)
raw=a.source.read_bytes()
document=open_document(raw,source_format='solidworks.slddrw',strict=True)
document=CadDocument.from_json(document.to_json(indent=None))
intent=ReadBlankInput(document.source.attributes['solidworks.blank.intent'])
assert len(document.drawing.Sheets)==1 and not document.drawing.ModelRefs
sheet=document.drawing.Sheets[0]
options=intent.OptionsValue
folders=options.FolderValue
names=options.SheetNames
assert folders.BinderName=='Design Binder'
expected_tree=[
    [folders.CommentsName,'CommentsFolder',None],
    [folders.BlocksName,'BlockFolder',None],
    ['Design Binder','DocsFolder',None],
    [folders.CabinetName,'DetailCabinet',None],
    [folders.InkName,'InkMarkupFolder',None],
    [folders.ReviewName,'MarkupCommentFolder',None],
    [sheet.EntityName,'DrSheet',None],
    [names.PlaneName,'RefPlane',sheet.EntityName],
    [names.ProfileName,'ProfileFeature',sheet.EntityName],
    [names.DetailName,'DetailFolder',sheet.EntityName],
]
expected={'sheet':sheet.EntityName,'sheet_properties':[0,13,*sheet.ScaleRatio,0,sheet.SheetWidth,sheet.SheetHeight,1],'view':None,'whats_wrong':0}
emitter=importlib.import_module('convert.adapters.solidworks.Core.DrawingWriting.EmitBlankDrawingMut')
emitter.ReadTime=lambda:a.epoch
emitter.AllocateBlockId=lambda:UUID('8e37440a-0096-4ee5-b14a-f05d97e62107')
a.target.parent.mkdir(parents=True,exist_ok=False)
guard=OutputGuard(a.target.parent)
sys.addaudithook(guard.event)
try:
    guard.active=True
    result=write_document(document,a.target,destination_format='solidworks.slddrw')
finally:
    guard.active=False
assert not guard.denied and not result.vendor_loadable and not result.application_usable
payload=a.target.read_bytes()
rewritten=open_document(payload,source_format='solidworks.slddrw',strict=True)
new_intent=ReadBlankInput(rewritten.source.attributes['solidworks.blank.intent'])
assert replace(new_intent,FileValue=intent.FileValue)==intent
assert new_intent.FileValue.SavedAt==a.epoch
assert rewritten.drawing==document.drawing
before=SldprtArchive.from_bytes(raw).streams
after=SldprtArchive.from_bytes(payload).streams
changed=[name for name in before if before[name]!=after[name]]
assert set(changed)=={'Header2','Contents/Definition'}
verify()
assert digest(a.source)==a.source_sha256
report={
    'schema':'kit.sw2026.blank-public-rewrite-native-candidate.v1','passed':True,
    'writer_manifest_sha256':a.manifest_sha256,
    'runner_sha256':digest(Path(__file__)),
    'guard_sha256':digest(Path(__file__).with_name('BlankRewriteGuard.py')),
    'source':{'path':str(a.source),'sha256':a.source_sha256},
    'target':{'path':str(a.target),'sha256':sha256(payload).hexdigest(),'bytes':len(payload)},
    'explicit_saved_at':a.epoch,'actual_self_path':new_intent.FileValue.PathName,
    'source_model_title':new_intent.OptionsValue.NameValue,
    'expected_initial':expected,'expected_tree':expected_tree,
    'edit_scale_ratio':[43.0,19.0],
    'source_intent':document.source.attributes['solidworks.blank.intent'],
    'changed_logical_streams':changed,
    'unchanged_layout':True,'source_owners_preserved':True,
    'runtime_input_reads':0,'native_launches':0,'private_slot_reads':0,
    'native_flags':[result.vendor_loadable,result.application_usable],
    'native_acceptance_claim':False,'output_operations':guard.operations,
}
a.report.parent.mkdir(parents=True,exist_ok=True)
with a.report.open('x') as f:
    json.dump(report,f,indent=2,allow_nan=False)
print(json.dumps({'passed':True,'output':report['target'],'report_sha256':digest(a.report)}))
