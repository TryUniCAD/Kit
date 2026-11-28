import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import sys


def require(value,message):
    if not value:raise ValueError(message)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();root=args.root.resolve(strict=True)
    require(not args.output.exists(),'trace output must be unused')
    inputs=json.loads((root/'Inputs01.json').read_bytes())
    sys.path.insert(0,str(root/'Baseline01'/'src'))
    from convert import open_document
    from convert.Geometry.Parasolid import DecodePartData,ParaHeaderData
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Archive.Partition.KernelShapes import KKernelShapes
    from convert.adapters.solidworks.Archive.Partition.XmtCursor import XmtCursor
    from convert.adapters.solidworks.Archive.Partition.ReadXmtNodeMut import ReadXmtNodeMut
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
    records=[]
    for row in inputs['sources']:
        data=Path(row['path']).read_bytes();require(sha256(data).hexdigest()==row['sha256'],'source differs')
        archive=SldprtArchive.from_bytes(data);link=ReadNativeLink(archive,0)
        payloads=DecodePartData(archive.require(link.ConfigName+'-Partition'))
        payload=payloads[0];header=ParaHeaderData(payload.data);require(header is not None,'partition lacks exact header')
        cursor=XmtCursor(payload.data[header.body_offset:]);nodes=[];unmapped=None
        while (kind:=cursor.ReadKind())!=1:
            if kind not in KKernelShapes:
                unmapped={'kind':kind,'payload_body_offset':cursor.OffsetValue-2,'next_schema_marker':cursor.DataValue[cursor.OffsetValue],'already_decoded_nodes':len(nodes)};break
            nodes.append(ReadXmtNodeMut(cursor,kind))
        manager=link.ConfigValue.RootValue.FieldsValue['fd88'];atoms=[item['o'] for item in manager['atoms']]
        bosses=[node for node in link.ResolvedValue.RootsValue if node is not None and node.ClassValue.NameValue=='moRevolution_c']
        document=open_document(data,source_format='solidworks.sldprt',strict=True)
        records.append({'name':row['name'],'source_sha256':row['sha256'],'payload_schema':payload.schema,'first_unmapped':unmapped,'decoded_kind_counts':dict(Counter(node.KindValue for node in nodes)),'atom_manager_n6c':manager['n6c'],'atoms':[{'class':atom.ClassValue.NameValue,'fields':{key:atom.FieldsValue.get(key) for key in ('f08','f140','f12c','f130','f180','f1b0','f18c','body_kind')},'name':atom.FieldsValue['f18'].FieldsValue['f08'] if atom.FieldsValue.get('f18') else None} for atom in atoms],'bosses':[{'id':boss.FieldsValue['f08'],'name':boss.FieldsValue['f18'].FieldsValue['f08'],'output_atom_alias':[item['o'] is atoms[0] for item in boss.FieldsValue['f528']['items']] if boss.FieldsValue.get('f528') else []} for boss in bosses],'public_bodies':[{'id':body.id,'name':body.name,'final_feature_id':body.final_feature_id} for body in document.bodies],'brep_counts':{key:len(getattr(document.brep,key)) for key in ('bodies','faces','loops','coedges','edges','vertices','surfaces','curves')},'input_immutable':sha256(Path(row['path']).read_bytes()).hexdigest()==row['sha256']})
    output={'schema':'kit.sw2026.revolve-body-first-class-trace.v1','sdk_manifest_sha256':sha256((root/'Baseline01Source.json').read_bytes()).hexdigest(),'tool_sha256':sha256(Path(__file__).read_bytes()).hexdigest(),'inputs_manifest_sha256':sha256((root/'Inputs01.json').read_bytes()).hexdigest(),'sources':records,'heldout_inputs_read':0,'native_processes':0}
    args.output.write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps(output))


if __name__=='__main__':main()
