from __future__ import annotations
import argparse
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import sys


def require(value, message):
    if not value:raise ValueError(message)


def main():
    parser=argparse.ArgumentParser()
    for name in ('root','packet','mate-graph','output'):parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--mate-graph-sha256',required=True)
    parser.add_argument('--mutation',choices=('transmit-index','cap-face','marker','atom','local-axis'))
    args=parser.parse_args()
    require(not args.output.exists(),'choose an unused kernel identity receipt')
    packet=args.packet.resolve(strict=True)
    require(packet.name=='ConcentricMateSourcePacket02','undeclared native source packet')
    graphraw=args.mate_graph.read_bytes()
    require(sha256(graphraw).hexdigest()==args.mate_graph_sha256,'disclosed parent graph changed')
    mategraphs=json.loads(graphraw)
    require(set(mategraphs)=={'D01','D02','D03'},'undeclared parent source cases')
    sys.path.insert(0,str(args.root.resolve(strict=True)/'src'))
    from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import DatumTime
    from convert.adapters.solidworks.Archive.Partition.CheckXmtGraph import CheckXmtGraph
    from convert.adapters.solidworks.Archive.Partition.ReadActiveNodes import ReadActiveNodes
    from convert.adapters.solidworks.Archive.Partition.ReadXmtHistory import ReadXmtHistory
    from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
    from convert.adapters.solidworks.Archive.Partition.WalkXmtChain import WalkXmtChain
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Container.Parasolid import DecodePartition
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
    def fields(graph,ref,name):
        row=graph[str(ref['index'])]
        require(ref['class']==row['class']==name,'parent reference concrete owner changed')
        return row['fields']
    def sole(values,message):
        require(len(values)==1,message)
        return values[0]
    def attrs(nodes,owner,name):
        chain=WalkXmtChain(nodes,owner.Integer('attributes_features'),81,'next','previous','owner',owner.IndexValue)
        result=[]
        for index in chain:
            item=RequireXmt(nodes,index,81);definition=RequireXmt(nodes,item.Integer('definition'),80)
            if RequireXmt(nodes,definition.Integer('identifier'),79).String('string')==name:result.append(item)
        return sole(result,'actual kernel owner has ambiguous '+name)
    def faceid(nodes,face):
        lanes=attrs(nodes,face,'FACE_ID_2001').Indexes('fields')
        require(len(lanes)==4 and lanes[:2]==(0,0),'native face pointer lane profile changed')
        return RequireXmt(nodes,lanes[2],82).Indexes('values')
    results=[];total=0
    for case in ('D01','D02','D03'):
        parent=packet/'Disclosed'/case;lockraw=(parent/'lock.json').read_bytes();lock=json.loads(lockraw)
        require(lock['source_locked'] is True and lock['heldout_source_locked'] is False,'source is not the declared disclosed lock')
        for phase in ('source','edited'):
            path=parent/'Native'/phase.title()/('Concentric'+case+'Child.SLDPRT')
            require(not path.is_symlink() and path.resolve(strict=True).is_relative_to(parent),'child escapes source custody')
            raw=path.read_bytes();wanted=lock['native_artifacts'][phase]['child']
            require(sha256(raw).hexdigest()==wanted['sha256'] and len(raw)==wanted['bytes'],'native child changed')
            archive=SldprtArchive.from_bytes(raw)
            payloads=DecodePartition(archive.require('Contents/Config-0-Partition'),'Contents/Config-0-Partition')
            require(tuple(v.kind for v in payloads)==('partition','deltas'),'native active/history pair changed')
            nodes=ReadActiveNodes(payloads[0].data);CheckXmtGraph(nodes);ReadXmtHistory(payloads[1].data,nodes);total+=len(nodes)
            faces=tuple(v for v in nodes.values() if v.KindValue==14)
            face=sole(tuple(v for v in faces if nodes[v.Integer('surface')].KindValue==51),'ambiguous cylinder face')
            require(len(faces)==3,'native face inventory changed')
            cylinder=RequireXmt(nodes,face.Integer('surface'),51)
            require(cylinder.Integer('owner')==face.IndexValue,'cylinder does not belong to the selected face')
            body=RequireXmt(nodes,RequireXmt(nodes,face.Integer('shell'),13).Integer('body'),12)
            lanes=attrs(nodes,body,'ATOM_ID_2001').Indexes('fields')
            require(len(lanes)==2 and lanes[0]==0,'native atom lane profile changed')
            atom_id,=RequireXmt(nodes,lanes[1],82).Indexes('values')
            link=ReadNativeLink(archive,0)
            boss=sole(tuple(v for v in link.ResolvedValue.RootsValue if v.ClassValue.NameValue=='moExtrusion_c'),'ambiguous extrusion')
            profile=sole(boss.FieldsValue['f60']['list']['items'],'ambiguous actual profile')['o']
            require(profile.ClassValue.NameValue=='moProfileFeature_c','actual profile class changed')
            arc=sole(profile.FieldsValue['pd_f80'].FieldsValue['arcs'],'ambiguous actual circle')['arc']
            feature_id=boss.FieldsValue['f08'];creation=DatumTime(link.ConfigValue.HeaderValue,feature_id)
            atom=sole(boss.FieldsValue['f528']['items'],'ambiguous actual atom')['o']
            require(atom.ClassValue.NameValue=='moAtom_c' and atom.FieldsValue['f140']==atom_id,'kernel atom does not match the actual child atom')
            primary=faceid(nodes,face)
            require(len(primary)==5 and primary[:3]==(74,feature_id,creation) and primary[4]==arc['f08'] and primary[3]&16==0,'cylinder id does not match actual extrusion and arc owners')
            caps=tuple(v for v in faces if v is not face);capids=tuple(faceid(nodes,v) for v in caps)
            require(all(len(v)==6 and v[:3]==(40,feature_id,creation) and v[3]&16==0 for v in capids),'cap identity owner changed')
            copied=deepcopy(mategraphs[case][phase]);graph=copied['graph']
            require(copied['archive_sha256']==lock['native_artifacts'][phase]['parent']['sha256'],'parent graph custody changed')
            mate=fields(graph,copied['root'],'moMateConcentric');ends=[]
            for ordinal,(ar,sr) in enumerate(zip(mate['f410'],mate['f3c8'],strict=True)):
                active=fields(graph,ar['o'],'moCylinderRef_w');comp=fields(graph,active['f58'],'moCompFace_c');ref=fields(graph,comp['fe8'],'moFaceRef_c')
                reps=[r['f08'] for r in ref['f10'] if r['f08'] is not None]
                surface=fields(graph,reps[0],'moFromSktEntSurfIdRep_c');fr=fields(graph,surface['f10']['f10'],'moFR_c')
                snapshot=fields(graph,sr['o'],'moCylinderRef_w');owner=fields(graph,snapshot['f58'],'moCompRefCylinder_c');facet=fields(graph,owner['fb0'],'moFacetedData_c')
                if ordinal==0 and (case,phase)==(('D03','source') if args.mutation=='local-axis' else ('D01','source')):
                    if args.mutation=='transmit-index':facet['f40']=face.IndexValue
                    elif args.mutation=='cap-face':facet['f40']=caps[0].Integer('node_id')
                    elif args.mutation=='marker':surface['f38']+=1
                    elif args.mutation=='atom':facet['f50']+=1
                    elif args.mutation=='local-axis':active['f108']=active['fe8']
                require(facet['f40']==face.Integer('node_id'),'snapshot face id differs from actual kernel face node id')
                require(facet['f50']==atom_id,'snapshot body id differs from actual body atom')
                require(primary[1:3]==(fr['f10']['f00'],fr['f10']['f08']) and primary[4]==surface['f38'],'active surface reference differs from actual cylinder id')
                require(tuple(active['f108'][key] for key in 'xyz')==cylinder.FieldsValue['axis'],'optional vector differs from actual child-local cylinder axis')
                activecaps=[]
                for rep in reps[1:]:
                    cap=fields(graph,rep,'moEndFaceSurfIdRep_c');cf=fields(graph,cap['f10']['f10'],'moFR_c')
                    activecaps.append((cf['f10']['f00'],cf['f10']['f08'],cap['f38'],cap['f3c']))
                require(sorted(activecaps)==sorted((v[1],v[2],v[4],v[5]) for v in capids),'adjacent cap identities differ from actual kernel caps')
                ends.append({'ordinal':ordinal,'face_node_id_matched':True,'body_atom_id_matched':True,'active_surface_id_matched':True,'adjacent_cap_ids_matched':True,'local_axis_matched':True})
            results.append({'case':case,'phase':phase,'child_sha256':wanted['sha256'],'parent_sha256':copied['archive_sha256'],'lock_sha256':sha256(lockraw).hexdigest(),'active_payload_sha256':payloads[0].sha256,'history_payload_sha256':payloads[1].sha256,'active_node_count':len(nodes),'faces':len(faces),'face_transmit_index':face.IndexValue,'face_node_id':face.Integer('node_id'),'body_atom_id':atom_id,'surface_id_words':list(primary),'cap_id_words':[list(v) for v in capids],'endpoints':ends})
    require(len(results)==6 and sum(len(v['endpoints']) for v in results)==12,'disclosed kernel endpoint inventory changed')
    result={'schema':'kit.sw2026.concentric-kernel-face-identities.v1','passed':True,'rows':results,'active_node_total':total,'saved_child_files':6,'endpoint_pairs':12,'complete_active_and_rollback_grammars':True,'native_processes_started':0,'hidden_inputs_read':0,'writer_outputs':0,'kernel_face_number_generation_qualified':False,'optional_axis_constructor_qualified':False,'mate_graph_sha256':args.mate_graph_sha256,'tool_sha256':sha256(Path(__file__).read_bytes()).hexdigest()}
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps({'passed':True,'sha256':sha256(args.output.read_bytes()).hexdigest(),'saved_children':6,'active_nodes':total,'endpoints':12},sort_keys=True))


if __name__=='__main__':
    try:main()
    except (ValueError,TypeError,KeyError) as error:
        print(json.dumps({'passed':False,'error':str(error)},sort_keys=True));raise SystemExit(3)
