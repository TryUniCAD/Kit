import argparse
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import sys


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--sdk',type=Path,required=True);parser.add_argument('--grammar',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();row=json.loads(sys.stdin.read())
    data=Path(row['path']).read_bytes();other=Path(row['other_path']).read_bytes()
    if sha256(data).hexdigest()!=row['sha256'] or sha256(other).hexdigest()!=row['other_sha256']:raise ValueError('disclosed fixture source differs')
    sys.path[:0]=[str(args.sdk/'src'),str(args.grammar)]
    from convert.adapters.solidworks.Container.Container import SldprtArchive,BuildSldprt
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
    from convert.adapters.solidworks.Archive.Partition.KernelShapes import KKernelShapes
    from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
    from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
    from para.Schema import SCHEMAS,Field,Schema
    import para.Partition as kernel
    for kind in (31,51):
        shape=KKernelShapes[kind]
        fields=lambda values:tuple(Field(value.NameValue,value.EncodingValue,value.PointerClass,value.CountValue) for value in values)
        SCHEMAS[kind]=Schema(shape.NameValue,fields(shape.BaseValue),fields(shape.FieldsValue))
        kernel.SCHEMA_HEADERS[kind]=kernel.schema_bytes(SCHEMAS[kind])
    archive=SldprtArchive.from_bytes(data);link=ReadNativeLink(archive,0);streams=archive.streams;original=dict(streams);partition_name=link.ConfigName+'-Partition';variant=row['variant']
    partition=kernel.read_partition(streams[partition_name])
    if kernel.frame_payloads(kernel.write_payloads(partition))!=streams[partition_name]:raise ValueError('complete source partition did not reemit exactly before fixture mutation')
    atom,=(entry['o'] for entry in link.ConfigValue.RootValue.FieldsValue['fd88']['atoms'])
    boss,=(node for node in link.ResolvedValue.RootsValue if node is not None and node.ClassValue.NameValue=='moRevolution_c')
    if variant in ('AtomIdMismatch','LastModifierMismatch','MissingOutput'):
        if variant=='AtomIdMismatch':atom.FieldsValue['f140']+=1
        elif variant=='LastModifierMismatch':atom.FieldsValue['f130']+=1
        else:boss.FieldsValue['has_f528']=0;boss.FieldsValue.pop('f528')
        config_bytes,config=WriteConfigMut(link.ConfigValue.RootValue,19000,link.ConfigValue.HeaderValue)
        resolved_bytes,_=WriteResolMut(link.ResolvedValue.RootsValue,link.ResolvedValue.ExtraFields,19000,config.MapValue,link.ResolvedValue.ContextValue)
        streams[link.ConfigName]=config_bytes;streams[link.StreamName]=resolved_bytes
    elif variant=='TruncatedCache':streams[partition_name]=streams[partition_name][:-9]
    elif variant=='OtherSelectedCache':streams[partition_name]=SldprtArchive.from_bytes(other).require(partition_name)
    else:
        nodes={node.index:node for node in partition.nodes};body,=(node for node in partition.nodes if node.kind==12)
        if variant in ('ImplicitSurrogate','ImplicitNull'):
            attributes={nodes[nodes[node.fields['definition']].fields['identifier']].fields['string']:node for node in partition.nodes if node.kind==81 and node.fields['owner']==body.index}
            implicit=nodes[attributes['SWIMPLICITBODYNAME_ID_U'].fields['fields'][0]];implicit.fields['values']=((0xD800 if variant=='ImplicitSurrogate' else 0),*implicit.fields['values'][1:])
        elif variant=='BodyOwner':body.fields['owner']=body.index
        elif variant=='FinMate':fin=next(node for node in partition.nodes if node.kind==17);fin.fields['other']=fin.index
        elif variant=='ExtraPlane':
            plane=next(node for node in partition.nodes if node.kind==50)
            index=max([node.index for node in partition.nodes]+[partition.root.index]+[entry.mark.index for entry in partition.history])+1
            partition=replace(partition,nodes=(*partition.nodes,kernel.Node(index,50,dict(plane.fields))))
        else:raise ValueError('unknown controlled fixture')
        streams[partition_name]=kernel.frame_payloads(kernel.write_payloads(partition))
    result=BuildSldprt(streams,Template=data);args.output.write_bytes(result)
    changed=sorted(name for name in original if original[name]!=SldprtArchive.from_bytes(result).require(name))
    print(json.dumps({'passed':True,'variant':variant,'sha256':sha256(result).hexdigest(),'changed_streams':changed,'source_sha256':row['sha256'],'full_partition_reemit_before_mutation':True,'research_fixture_only':True,'writer_output':False,'heldout_inputs_read':0,'source_immutable':sha256(Path(row['path']).read_bytes()).hexdigest()==row['sha256']}))


if __name__=='__main__':main()
