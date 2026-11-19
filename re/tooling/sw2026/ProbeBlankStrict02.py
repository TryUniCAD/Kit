from __future__ import annotations

import argparse
import codecs
from dataclasses import replace
from hashlib import sha256
import importlib
import io
import json
from pathlib import Path, PureWindowsPath
import sys

p=argparse.ArgumentParser()
p.add_argument('--code',type=Path,required=True)
p.add_argument('--file',type=Path,required=True)
p.add_argument('--sha256',required=True)
p.add_argument('--output',type=Path,required=True)
p.add_argument('--route',choices=('bytes','path'),default='bytes')
p.add_argument('--expect',choices=('accept','reject'),required=True)
p.add_argument('--options',choices=('default','no-brep','no-tess','minimal'),default='default')
p.add_argument('--request',type=Path)
a=p.parse_args()
sys.path.insert(0,str(a.code/'src'))
sys.dont_write_bytecode=True
from convert.api import open_document, write_document
from convert.adapters import AdapterNotFoundError
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.SldprtFormat import SldprtFormat
from interchange.document.Models.DocumentModel import CadDocument
from interchange.document.Behavior.DocumentIo import FromJson, ToJson
for name in ('DocumentFeatureValidate','DocumentReferenceValidate','DocumentAssemblyValidate'):
    importlib.import_module('interchange.document.Validation.'+name)
importlib.import_module('interchange.document.Models.DocumentProvenance')
importlib.import_module('convert.adapters.solidworks.Drawing.Definition.Projection.JoinConcept')
importlib.import_module('convert.adapters.solidworks.Drawing.Definition.ReadConcept')
try:
    module=importlib.import_module('convert.adapters.solidworks.Drawing.Reading.Blank.ReadBlankIntent')
    read_intent=module.ReadBlankIntent
    importlib.import_module('convert.adapters.solidworks.Drawing.Reading.ReadGeneratedBlank')
except ModuleNotFoundError:
    read_intent=None
if read_intent is not None:
    from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import SelfFileInput
    from convert.adapters.solidworks.Archive.Construction.Header.HeaderInput import HeaderInput
    from convert.adapters.solidworks.Archive.Construction.Metadata.HistoryInput import HistoryInput
    from convert.adapters.solidworks.Archive.Definition.Construction.ModelDefSettings import ModelDefSettings
    from convert.adapters.solidworks.Drawing.Construction.Portable.MakeBlankFile import MakeBlankFile
for name in ('utf-16-le','utf-8','latin-1'):
    codecs.lookup(name)
raw=a.file.read_bytes()
assert sha256(raw).hexdigest()==a.sha256
expected=None if a.request is None else json.loads(a.request.read_bytes())
source=a.file if a.route=='path' else raw
included={'include_brep':a.options not in ('no-brep','minimal'),'include_tessellation':a.options not in ('no-tess','minimal')}
active=False
reads=[]
denied=[]

def audit(event,args):
    if not active:
        return
    if event=='open':
        target=args[0]
        mode=args[1]
        if a.route=='path' and isinstance(target,(str,bytes)) and Path(target).resolve()==a.file.resolve() and isinstance(mode,str) and mode in ('r','rb'):
            reads.append(event)
            return
        denied.append({'event':event,'target':str(target),'mode':mode})
        raise RuntimeError('unexpected runtime file access')
    if event in ('os.scandir','os.listdir','subprocess.Popen','os.system','os.posix_spawn'):
        denied.append({'event':event})
        raise RuntimeError('unexpected runtime filesystem or process access')

sys.addaudithook(audit)
result={'schema':'kit.sw2026.blank-strict-public-probe.v1','source_sha256':a.sha256,'route':a.route,'options':a.options,'expected':a.expect,'passed':False}
try:
    active=True
    try:
        partial=open_document(source,source_format='solidworks.slddrw',strict=False,**included)
        wire=partial.to_json(indent=None)
        result['partial']={'success':True,'sha256':sha256(wire.encode()).hexdigest(),'diagnostics':[d.code for d in partial.diagnostics]}
    except SldprtFormat as error:
        result['partial']={'success':False,'type':type(error).__name__,'message':str(error)}
    try:
        document=open_document(source,source_format='solidworks.slddrw',strict=True,**included)
    except SldprtFormat as error:
        result['strict']={'success':False,'type':type(error).__name__,'message':str(error)}
        assert a.expect=='reject'
    else:
        assert a.expect=='accept'
        assert document.drawing is not None and len(document.drawing.Sheets)==1 and not document.drawing.ModelRefs and not document.drawing.Sheets[0].Views
        assert not document.diagnostics and not document.bodies and not document.brep_payloads and document.brep is None and not document.meshes
        assert document.source.sha256==a.sha256 and document.source.attributes['solidworks.blank.complete_container_reconstruction'] is True
        text=document.to_json(indent=None)
        revived=CadDocument.from_json(text)
        assert revived.to_json(indent=None)==text
        assert revived.source.attributes==document.source.attributes
        assert read_intent is not None
        intent=read_intent(SldprtArchive.from_bytes(raw),raw).InputValue
        assert type(intent.HeaderValue) is HeaderInput and type(intent.HistoryValue) is HistoryInput and type(intent.FileValue) is SelfFileInput and type(intent.UiSettings) is ModelDefSettings
        assert MakeBlankFile(intent).BytesValue==raw
        assert intent.HeaderValue.CreatedAt==intent.HistoryValue.CreatedAt==intent.OptionsValue.CreatedAt
        if expected is not None:
            sheet=expected['drawing']['Sheets'][0]
            actual=document.drawing.Sheets[0]
            assert actual.EntityName==sheet['EntityName'] and actual.ScaleRatio==tuple(sheet['ScaleRatio'])
            assert actual.SheetWidth==sheet['SheetWidth'] and actual.SheetHeight==sheet['SheetHeight']
            owners=expected['provenance']
            assert intent.HeaderValue.AuthorName==owners['author'] and intent.HeaderValue.CompanyName==owners['company'] and intent.HeaderValue.CommentText==owners['comment']
            assert (intent.HeaderValue.CreatedAt,intent.HeaderValue.ModifiedAt,intent.HeaderValue.UpdatedAt,intent.FileValue.SavedAt)==tuple(owners[k] for k in ('created_at','modified_at','updated_at'))+(expected['output']['saved_at'],)
            assert intent.HistoryValue.LanguageId==owners['language_id'] and intent.HistoryValue.CjkSaved==owners['cjk_saved'] and intent.HistoryValue.LicenseOrigin==owners['license_origin']
            assert ((intent.OptionsValue.StyleValue.LanguageId&1023)==13)==((expected['options']['styles']['language_id']&1023)==13)
        newer_file=SelfFileInput(str(PureWindowsPath("C:/IndependentBlankRepeat")/(intent.OptionsValue.NameValue+"After.SLDDRW")),max(intent.FileValue.SavedAt,intent.HeaderValue.ModifiedAt)+409)
        newer_input=replace(intent,DrawingValue=document.drawing,FileValue=newer_file)
        newer=MakeBlankFile(newer_input)
        after=open_document(newer.BytesValue,source_format='solidworks.slddrw',strict=True,**included)
        after_intent=read_intent(SldprtArchive.from_bytes(newer.BytesValue),newer.BytesValue).InputValue
        assert after_intent.HeaderValue==intent.HeaderValue and after_intent.HistoryValue==intent.HistoryValue and after_intent.UiSettings==intent.UiSettings and after_intent.OptionsValue==intent.OptionsValue
        assert after_intent.FileValue==newer_file and after.drawing==document.drawing
        changed=[k for k in SldprtArchive.from_bytes(raw).streams if SldprtArchive.from_bytes(raw).require(k)!=newer.StreamsValue[k]]
        assert set(changed)=={'Header2','Contents/Definition'}
        target=a.output.parent/(intent.OptionsValue.NameValue+'.SLDDRW')
        try:
            write_document(document,target,destination_format='solidworks.slddrw')
        except AdapterNotFoundError:
            rewrite_refused=True
        else:
            raise AssertionError('public writer discarded source attributes')
        result['strict']={'success':True,'diagnostics':[],'document_sha256':sha256(text.encode()).hexdigest(),'complete_input_metadata':True,'json_roundtrip':True,'typed_input_factory_bytes_identical':True,'separate_destination_and_save_event_preserve_provenance':True,'repeat_changed_streams':changed,'repeat_sha256':sha256(newer.BytesValue).hexdigest(),'public_rewrite_preserving_attributes_refused':rewrite_refused,'style_language_selector_is_representative':True}
    assert not denied
    result['passed']=True
except Exception as error:
    result['error']={'type':type(error).__name__,'message':str(error)}
finally:
    active=False
result.update(allowed_source_opens=len(reads),denied_runtime_accesses=denied,private_slots_read=0,vendor_runtime_executed=False,native_acceptance=False)
with a.output.open('x') as f:
    json.dump(result,f,indent=2,allow_nan=False)
print(json.dumps({'passed':result['passed'],'output':str(a.output),'strict':result.get('strict'),'error':result.get('error'),'denied':len(denied),'allowed_source_opens':len(reads)}))
raise SystemExit(0 if result['passed'] else 3)
