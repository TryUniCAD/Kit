from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys


def encode_fault(roots, resolved):
    from convert.adapters.solidworks.Archive.Bodies.BodyWriter import BodyWriter
    from convert.adapters.solidworks.Archive.Bodies.WriteBodyMut import WriteBodyMut
    from convert.adapters.solidworks.Archive.Bodies.Writing.WriteNodeMut import WriteNodeMut
    from convert.adapters.solidworks.Archive.Counts.EncodeCount import EncodeCount
    from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
    from convert.adapters.solidworks.Archive.Mates.MakeMatesCtx import MakeMatesCtx
    from convert.adapters.solidworks.Archive.Scalars.EncodeScalar import EncodeScalar
    context = MakeMatesCtx(resolved, None)
    seed = resolved.MapValue
    writer = BodyWriter(ArchiveMaps(seed.CounterValue, seed), context, WriteBodyMut)
    writer.OutputValue.extend(EncodeScalar(seed.CounterValue, 'i32'))
    writer.OutputValue.extend(EncodeCount(len(roots)))
    for node in roots:
        WriteNodeMut(writer, node)
    return bytes(writer.OutputValue)


def main():
    parser = argparse.ArgumentParser()
    for name in ('root','packet','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    args = parser.parse_args()
    if args.output.exists() or args.packet.resolve().name != 'ConcentricMateSourcePacket02':
        raise ValueError('choose a new diagnostic root and the declared disclosed packet')
    sys.path.insert(0,str(args.root.resolve(strict=True)/'src'))
    from convert.adapters.solidworks.Archive.Mates.ReadMatesMut import ReadMatesMut
    from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
    cases = {
        'WrongOrdinal':'resolved wrapper ownership or order differs',
        'WrapperCollision':'registered wrapper identities collide',
        'StaleChildStamp':'child update is stale',
        'WrongConfiguration':'child configuration differs',
        'ForeignChainOwner':'different assembly',
        'WrongFeature':'stale or foreign feature owner',
        'WrongCreation':'stale or foreign feature owner',
        'WrongMarker':'selected arc permanent marker differs',
        'WrongCap':'adjacent cap identities differ',
        'WrongLocalAxis':'cylinder geometry or local axis differs',
        'WrongPoint':'cylinder geometry or local axis differs',
        'WrongAxis':'cylinder geometry or local axis differs',
        'WrongRadius':'cylinder geometry or local axis differs',
        'WrongFaceDomain':'faceted snapshot differs',
        'WrongBodyAtom':'faceted snapshot differs',
        'WrongFacetText':'faceted snapshot differs',
        'WrongParentStamp':'detached support owner or parent epoch differs',
        'UnsolvedMate':'ordinary solved position profile',
        'WrongAlignment':'solved coaxial alignment',
        'InvalidLock':'alignment or position is unqualified',
        'InvalidAlignment':'alignment or position is unqualified',
        'WrongNullSlot':'two null entries',
    }
    args.output.mkdir(parents=True)
    result = []
    custody = {}
    for label,message in cases.items():
        case = 'D03' if label == 'WrongLocalAxis' else 'D01'
        name = 'ConcentricD03AntiFree' if case == 'D03' else 'ConcentricD01AlignedFree'
        folder = args.packet/'Disclosed'/case
        lockraw = (folder/'lock.json').read_bytes()
        lock = json.loads(lockraw)
        if lock['source_locked'] is not True or lock['heldout_source_locked'] is not False:
            raise ValueError('diagnostics require the disclosed source lock')
        original = folder/'Native/Source'/(name+'.SLDASM')
        child = original.parent/('Concentric'+case+'Child.SLDPRT')
        raw,part = original.read_bytes(),child.read_bytes()
        if sha256(raw).hexdigest()!=lock['native_artifacts']['source']['parent']['sha256'] or sha256(part).hexdigest()!=lock['native_artifacts']['source']['child']['sha256']:
            raise ValueError('disclosed source changed')
        custody[case] = {'parent_sha256':sha256(raw).hexdigest(),'child_sha256':sha256(part).hexdigest(),'lock_sha256':sha256(lockraw).hexdigest()}
        archive = SldprtArchive.from_bytes(raw)
        link = ReadNativeLink(archive,0)
        graph = ReadMatesMut(archive.require('Contents/Config-0-MatesList'),link.ResolvedValue)
        mate, = graph.RootsValue
        active = mate.FieldsValue['f410'][0]['o']
        stored = mate.FieldsValue['f3c8'][0]['o']
        component = active.FieldsValue['f58']
        faceref = component.FieldsValue['fe8']
        side = faceref.FieldsValue['f10'][0]['f08']
        reference = side.FieldsValue['f10']['f10']
        support = stored.FieldsValue['f58']
        geometry = support.FieldsValue['ff8']
        facet = support.FieldsValue['fb0']
        if label=='WrongOrdinal':active.FieldsValue['f7c']=1
        elif label=='WrapperCollision':mate.FieldsValue['f410'][1]['o'].FieldsValue['f78']=active.FieldsValue['f78']
        elif label=='StaleChildStamp':active.FieldsValue['f08']+=1
        elif label=='WrongConfiguration':active.FieldsValue['f0c']=1
        elif label=='ForeignChainOwner':
            chain=component.FieldsValue['f58']
            chain.FieldsValue['owner']=chain.FieldsValue['f20'].FieldsValue['f08'].FieldsValue['f08'][0]['o'].FieldsValue['f50']
        elif label=='WrongFeature':reference.FieldsValue['f10']['f00']+=1
        elif label=='WrongCreation':reference.FieldsValue['f10']['f08']+=1
        elif label=='WrongMarker':side.FieldsValue['f38']+=1
        elif label=='WrongCap':faceref.FieldsValue['f10'][1]['f08'].FieldsValue['f38']=faceref.FieldsValue['f10'][3]['f08'].FieldsValue['f38']
        elif label=='WrongLocalAxis':active.FieldsValue['f108']=dict(active.FieldsValue['fe8'])
        elif label=='WrongPoint':
            for node,key in ((active,'fd0'),(stored,'fd0'),(geometry,'f6f8')):node.FieldsValue[key]['x']+=0.00137
        elif label=='WrongAxis':
            for node,key in ((active,'fe8'),(stored,'fe8'),(geometry,'f710')):node.FieldsValue[key]={'x':1.0,'y':0.0,'z':0.0}
        elif label=='WrongRadius':
            for node,key in ((active,'f100'),(stored,'f100'),(geometry,'f728')):node.FieldsValue[key]*=1.1
        elif label=='WrongFaceDomain':
            child_archive=SldprtArchive.from_bytes(part)
            from convert.adapters.solidworks.Core.TypedMates.Cylinders.ReadCylNodes import ReadCylNodes
            nodes=ReadCylNodes(child_archive)
            face,=(node for node in nodes.values() if node.KindValue==14 and nodes[node.Integer('surface')].KindValue==51)
            facet.FieldsValue['f40']=face.IndexValue
        elif label=='WrongBodyAtom':facet.FieldsValue['f50']+=1
        elif label=='WrongFacetText':facet.FieldsValue['f58']=facet.FieldsValue['f58'].replace(str(side.FieldsValue['f38'])+', \n','999999, \n')
        elif label=='WrongParentStamp':stored.FieldsValue['f08']+=1
        elif label=='UnsolvedMate':mate.FieldsValue['f3b8']=0
        elif label=='WrongAlignment':mate.FieldsValue['f3b4']=2
        elif label=='InvalidLock':mate.FieldsValue['f4b8']=2
        elif label=='InvalidAlignment':mate.FieldsValue['f3b4']=3
        elif label=='WrongNullSlot':faceref.FieldsValue['f10'][2]['f08']=faceref.FieldsValue['f10'][0]['f08']
        streams=dict(archive.streams)
        streams['Contents/Config-0-MatesList']=encode_fault(graph.RootsValue,link.ResolvedValue)
        encoded=BuildSldprt(streams,format_version=archive.format_version)
        output=args.output/label
        output.mkdir()
        target=output/original.name
        target.write_bytes(encoded)
        (output/child.name).write_bytes(part)
        result.append({'case':label,'source_case':case,'path':str(target),'sha256':sha256(encoded).hexdigest(),'child_sha256':sha256(part).hexdigest(),'expected_error':message})
    receipt={'schema':'kit.sw2026.concentric-public-diagnostics.v1','cases':result,'sources':custody,
        'writer_output_count':0,'diagnostic_output_count':len(result),'native_processes_started':0,'hidden_inputs_read':0,
        'tool_sha256':sha256(Path(__file__).read_bytes()).hexdigest()}
    (args.output/'Faults.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'passed':True,'diagnostic_output_count':len(result),'sha256':sha256((args.output/'Faults.json').read_bytes()).hexdigest()},sort_keys=True))


if __name__=='__main__':
    main()
