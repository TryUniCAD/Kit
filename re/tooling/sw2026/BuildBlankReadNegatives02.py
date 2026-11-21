from __future__ import annotations

import argparse
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import struct
import sys
from xml.etree.ElementTree import SubElement

p=argparse.ArgumentParser()
p.add_argument('--code',type=Path,required=True)
p.add_argument('--request',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args()
sys.path[:0]=[str(a.code/'src'),str(Path(__file__).parent)]
from DrawingSdkInput import blank_input
from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyWriter import BodyWriter
from convert.adapters.solidworks.Archive.Bodies.FieldScope import FieldScope
from convert.adapters.solidworks.Archive.Bodies.WriteBodyMut import WriteBodyMut
from convert.adapters.solidworks.Archive.Bodies.WriteFrame import WriteFrame
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteFieldsMut import WriteFieldsMut
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteSchemaMut import WriteSchemaMut
from convert.adapters.solidworks.Archive.Construction.Metadata.FrameKeywords import FrameKeywords
from convert.adapters.solidworks.Archive.Definition.Fields.DefPrefixFields import KDefPrefixFields
from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
from convert.adapters.solidworks.Archive.History.ReadHistMut import ReadHistMut
from convert.adapters.solidworks.Archive.History.WriteHistMut import WriteHistMut
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Container.Container import build_sldprt
from convert.adapters.solidworks.Container.Format import KeywordsStream
from convert.adapters.solidworks.Core.Native import ParseXml
from convert.adapters.solidworks.Drawing.Construction.Portable.MakeBlankFile import MakeBlankFile
from convert.adapters.solidworks.Drawing.Definition.Emission.BlankSchemas import KBlankSchemas
from convert.adapters.solidworks.Drawing.Definition.Emission.BlankVirtuals import KBlankVirtuals
from convert.adapters.solidworks.Drawing.Definition.Emission.Layouts.BlankLayouts import KBlankLayouts
from convert.adapters.solidworks.Drawing.Definition.Emission.WriteDrawMut import WriteDrawMut
from convert.adapters.solidworks.Drawing.Definition.Emission.WriteBlankDef import WriteBlankDef
from convert.adapters.solidworks.Drawing.Identity.DrawingIdentity import KDrawClsid
from convert.adapters.solidworks.Drawing.Layout.ReadDrawLayout import KLayoutProperties
from convert.adapters.solidworks.Drawing.Metadata.ReadDrawProps import ReadDrawProps
from convert.adapters.solidworks.Drawing.Metadata.Writing.MakeInfoProps import MakeInfoProps

job=json.loads(a.request.read_bytes())
reports=[]

def fresh():
    result=MakeBlankFile(blank_input(deepcopy(job)))
    return result,dict(result.StreamsValue)


def emit_unadmitted(graph):
    context=BodyContext(19000,KBlankLayouts,KBlankVirtuals,KBlankSchemas)
    writer=BodyWriter(ArchiveMaps(1),context,WriteDrawMut)
    frame=WriteFrame(writer,FieldScope(graph.DocumentValue.FieldsValue),graph.DocumentValue,WriteSchemaMut,WriteFieldsMut)
    WriteFieldsMut(frame,KDefPrefixFields)
    writer.OutputValue.extend(KDrawClsid)
    WriteBodyMut(writer,graph.DocumentValue)
    return bytes(writer.OutputValue)


def save(name,streams,reason,tail=b''):
    payload=build_sldprt(streams)+tail
    path=a.output/(name+'.SLDDRW')
    with path.open('xb') as f:
        f.write(payload)
    reports.append({'name':name,'path':str(path),'sha256':sha256(payload).hexdigest(),'expected_strict_rejection':True,'scope':reason,'producer':'independently modeled SDK fixture; no native validity claim'})

x,s=fresh();s['docProps/ExtraUserData.xml']=b'<AuthoredText>must not disappear</AuthoredText>';save('ExtraSemanticStream',s,'unmodeled source stream')
x,s=fresh();s['ModelStamps']=struct.pack('<III',1,2,3);save('ConflictingStamps',s,'model stamps conflict with the actual header owners')
x,s=fresh();s['ModelStamps']+=b'\0';save('TrailingStampByte',s,'unconsumed scalar stream byte')
x,s=fresh();root=ParseXml(s[KeywordsStream]);SubElement(root,'Annotation',name='unmapped').text='independent source note metadata';s[KeywordsStream]=FrameKeywords(root,True);save('UnknownKeywordOwner',s,'keyword metadata not represented by the fresh sheet recipe')
x,s=fresh();props=ReadDrawProps(s['docProps/ISolidWorksInformation.xml'],KLayoutProperties);order=('SW-Current Sheet','SW-Total Sheets','SW-Sheet Name','SW-All Sheet Names','SW-Config-Model-View-Sheet-List','SW-All Sheet Format Data');s['docProps/ISolidWorksInformation.xml']=MakeInfoProps(tuple((k,props[k]) for k in order)+(('Authored reviewer note','must remain visible as source state'),));save('ExtraCustomProperty',s,'real additional text property with generated ID and dictionary')
x,s=fresh();header=deepcopy(x.HeaderValue);header.FieldsValue['f50']+=1;s['Header2']=WriteHeadGraph(header,19000);save('DifferentHeaderCopies',s,'independent Header2 and inline model header disagree')
x,s=fresh();x.HeaderValue.FieldsValue['f08']+=1;s['Header2']=WriteHeadGraph(x.HeaderValue,19000);s['Contents/Definition']=WriteBlankDef(x.UiGraph).OutputValue;save('ExtraPersistentCounter',s,'unrepresented noncanonical persistent counter')
x,s=fresh();history=ReadHistMut(s['_MO_VERSION_19000/History'],19000).RootValue;code=history.FieldsValue['states'][0]['st']['f38'];code.FieldsValue['states'].append({'st':{'f08':2026001}});code.FieldsValue['n']=2;s['_MO_VERSION_19000/History']=WriteHistMut(history,19000)[0];save('MultipleBuildHistory',s,'history authoring scope exceeds one originating build')
x,s=fresh();history=ReadHistMut(s['_MO_VERSION_19000/History'],19000).RootValue;history.FieldsValue['states'][0]['st']['f08']['f18']+=1;s['_MO_VERSION_19000/History']=WriteHistMut(history,19000)[0];save('DifferentCreationOwners',s,'history and header creation owners differ')
x,s=fresh();s['_MO_VERSION_19000/Biography']+=b'\0';save('TrailingBiographyByte',s,'unconsumed biography owner data')
x,s=fresh();x.UiGraph.DocumentValue.FieldsValue['f1000']=1;s['Contents/Definition']=WriteBlankDef(x.UiGraph).OutputValue;save('UnrepresentedUiState',s,'typed UI scalar outside the fresh settings profile')
x,s=fresh();detail=x.ModelGraph.SheetValue.DetailValue;detail.FieldsValue['has_fd98']=1;s['Contents/Definition']=emit_unadmitted(x.UiGraph);save('NonemptyAnnotationMarker',s,'structural annotation-bucket marker only; no claim of a vendor-authored annotation')
x,s=fresh();detail=x.ModelGraph.SheetValue.DetailValue;detail.FieldsValue['f358']['items']=[{'o':x.ModelGraph.ModelValue.FieldsValue['f18']}];s['Contents/Definition']=emit_unadmitted(x.UiGraph);save('NonemptyNoteCollection',s,'syntactically typed note-collection incidence with deliberately unsupported object; no native note validity claim')
x,s=fresh();save('TrailingContainerOwner',s,'unrepresented trailing container bytes',b'Unrepresented native owner')
x,s=fresh();del s['_MO_VERSION_19000/History'];save('MissingHistory',s,'missing load-critical chronology stream')
manifest={'schema':'kit.sw2026.blank-reader-negative-fixtures.v1','cases':reports,'vendor_saved_bytes_used':False,'native_acceptance':False,'original_heldout_reads':0}
with (a.output/'Manifest.json').open('x') as f:
    json.dump(manifest,f,indent=2)
print(json.dumps({'passed':True,'negative_cases':len(reports),'manifest_sha256':sha256((a.output/'Manifest.json').read_bytes()).hexdigest(),'native_validity_claim':False}))
