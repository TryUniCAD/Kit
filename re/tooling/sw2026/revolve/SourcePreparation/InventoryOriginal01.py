import argparse
from collections import Counter
from dataclasses import fields,is_dataclass
from hashlib import sha256
import json
from pathlib import Path
import sys


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    root=args.root.resolve(strict=True)
    assert not args.output.exists()
    inputs=json.loads((root/'Inputs01.json').read_bytes())
    sys.path.insert(0,str(root/'Baseline01/src'))
    from convert import open_document
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
    from convert.adapters.solidworks.Core.TypedResolved.Revolves.ReadRevOwners import ReadRevOwners
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
    from convert.adapters.solidworks.Archive.Definition.ReadModelDef import ReadModelDef
    from convert.adapters.solidworks.Archive.History.ReadHistMut import ReadHistMut
    from convert.adapters.solidworks.Archive.History.WriteHistMut import WriteHistMut
    from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
    from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
    from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
    from interchange.document.Behavior.DocumentIo import ToJson
    args.output.mkdir(parents=True)
    summaries=[]
    for source in inputs['controls']:
        data=Path(source['path']).read_bytes()
        assert sha256(data).hexdigest()==source['sha256']
        archive=SldprtArchive.from_bytes(data)
        link=ReadNativeLink(archive,0)
        owner,=ReadRevOwners(link)
        doc=open_document(data,source_format='solidworks.sldprt',strict=True)
        doc.assert_valid()
        encoded=ToJson(doc)
        manager=ReadCmgrMut(archive.require('Contents/CMgr'),19000).RootValue
        definition=ReadModelDef(archive.require('Contents/Definition'),19000).GraphValue
        biography=ReadHistMut(archive.require('_MO_VERSION_19000/Biography'),19000)
        history=ReadHistMut(archive.require('_MO_VERSION_19000/History'),19000)
        for name,value in [('Biography',biography),('History',history)]:
            assert WriteHistMut(value.RootValue,19000)[0]==archive.require('_MO_VERSION_19000/'+name)
        objects=[];ids={};records=[]
        def value(item):
            if isinstance(item,ArchiveNode):
                if id(item) not in ids:
                    ids[id(item)]='n'+str(len(objects));objects.append(item)
                return {'node':ids[id(item)]}
            if item is None or type(item) in (bool,int,float,str):return item
            if isinstance(item,bytes):return {'bytes':len(item),'sha256':sha256(item).hexdigest()}
            if isinstance(item,dict):return {str(key):value(val) for key,val in item.items()}
            if isinstance(item,(tuple,list)):return [value(val) for val in item]
            if is_dataclass(item):return {'type':type(item).__name__,'fields':{key.name:value(getattr(item,key.name)) for key in fields(item)}}
            raise ValueError('unqualified inventory value '+type(item).__name__)
        roots={name:value(item) for name,item in [('configuration',link.ConfigValue.RootValue),('manager',manager),('definition',definition.DocumentValue),('header',ReadHeaderGraph(archive.require('Header2'),19000)),('model_header',link.ConfigValue.HeaderValue),('biography',biography.RootValue),('history',history.RootValue)]}
        roots['resolved']=[value(node) for node in link.ResolvedValue.RootsValue]
        for node in objects:
            records.append({'node':ids[id(node)],'class':node.ClassValue.NameValue,'schema':node.ClassValue.SchemaValue,'fields':value(node.FieldsValue)})
        stem=source['name'].removeprefix('control-')
        target=args.output/stem;target.mkdir()
        (target/'Document.json').write_text(encoded+'\n')
        graph={'roots':roots,'nodes':records,'heldout_inputs_read':0}
        (target/'Graph.json').write_text(json.dumps(graph,indent=2,allow_nan=False)+'\n')
        summary={'name':stem,'source_sha256':source['sha256'],'streams':sorted(archive.streams),'classes':dict(Counter(row['class'] for row in records)),'source_document_sha256':sha256(encoded.encode()).hexdigest(),'model_root':roots['configuration'],'feature_id':owner.NodeValue.FieldsValue['f08'],'feature_name':ReadNativeName(owner.NodeValue),'profile_id':owner.ProfileValue.FieldsValue['f08'],'profile_name':ReadNativeName(owner.ProfileValue),'axis':value(owner.AxisValue),'frame':value(owner.FrameValue),'angle':value(owner.AngleValue),'reverse':owner.IsReverse,'header_fields':roots['header'],'history':roots['history'],'biography':roots['biography'],'definition':roots['definition']}
        summaries.append(summary)
    result={'schema':'kit.sw2026.disclosed-revolve-original-inventory.v1','heldout_inputs_read':0,'sources':summaries}
    (args.output/'Inventory.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'passed':True,'sources':len(summaries),'inventory_sha256':sha256((args.output/'Inventory.json').read_bytes()).hexdigest()}))


if __name__=='__main__':main()
