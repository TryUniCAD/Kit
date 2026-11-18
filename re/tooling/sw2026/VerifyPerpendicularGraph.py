import argparse
from hashlib import sha256
import json
from math import isclose
from pathlib import Path, PureWindowsPath
import sys


def require(value, message):
    if not value:
        raise ValueError(message)


def matches(actual, expected):
    return len(actual) == len(expected) and all(isclose(a,b,rel_tol=1e-10,abs_tol=1e-12) for a,b in zip(actual,expected,strict=True))


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,required=True)
    args=parser.parse_args()
    root=args.root.resolve()
    sys.path[:0]=[str(root),str(root/'src')]
    from convert import open_document
    from convert.adapters.solidworks.Assembly.Assembly import Configurations,Files,Models,XmlRoot
    from convert.adapters.solidworks.Archive.Mates.ReadMatesMut import ReadMatesMut
    from convert.adapters.solidworks.Archive.Mates.WriteMatesMut import WriteMatesMut
    from convert.adapters.solidworks.Assembly.PlanarMates.PlanarContext import PlanarChild,PlanarContext
    from convert.adapters.solidworks.Assembly.PlanarMates.ReadPlanarMate import ReadPlanarMate
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Container.Format import KComponentTreeStream
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
    from convert.adapters.solidworks.Core.TypedMates.CheckMateIds import CheckMateIds
    from convert.adapters.solidworks.Core.TypedMates.CheckMatePoint import CheckMatePoint
    from convert.adapters.solidworks.Core.TypedMates.CheckMateWrappers import CheckMateWrappers
    from convert.adapters.solidworks.Core.TypedMates.CheckPerpRefs import CheckPerpRefs
    from convert.adapters.solidworks.Core.TypedMates.CheckPerpEpoch import CheckPerpEpoch
    from convert.adapters.solidworks.Core.TypedMates.CheckPerpDatum import CheckPerpDatum
    from convert.adapters.solidworks.Core.TypedMates.ReadFixedFlags import ReadFixedFlags

    request=json.load(sys.stdin)
    parent,child=(Path(request[key]) for key in ('parent','child'))
    expected=request['prediction']['source']
    archive=SldprtArchive.from_bytes(parent.read_bytes())
    child_archive=SldprtArchive.from_bytes(child.read_bytes())
    link=ReadNativeLink(archive,0);child_link=ReadNativeLink(child_archive,0)
    graph=ReadMatesMut(archive.require('Contents/Config-0-MatesList'),link.ResolvedValue)
    encoded,_=WriteMatesMut(graph.RootsValue,link.ResolvedValue)
    require(encoded==archive.require('Contents/Config-0-MatesList') and len(graph.RootsValue)==1,'the complete generated mate stream does not retain typed bytes')
    xml=XmlRoot(archive.require(KComponentTreeStream))
    configuration,=Configurations(xml)
    definitions,all_items=Models(xml,{item.object_id:item for item in Files(xml)})
    items=tuple(item for item in all_items if item.owner_definition_id==configuration.model_id)
    datum_nodes={node.FieldsValue['f08']:node for node in child_link.ResolvedValue.RootsValue if node.ClassValue.NameValue=='moRefPlane_c'}
    child_data=PlanarChild(child_link.ConfigValue.HeaderValue,datum_nodes)
    context=PlanarContext(link.ConfigValue.RootValue,{item.feature_id:item for item in items},{item.object_id:item for item in definitions},
                          {(PureWindowsPath(item.source_path).name.casefold(),item.configuration_id):child_data for item in definitions if item.document_type=='PART'})
    node,=graph.RootsValue
    require(node.ClassValue.NameValue=='moMatePerpendicular' and tuple(node.FieldsValue[k] for k in ('f0c','f3b4','f3b8'))==(1,0,0),'the generated mate copied solved state instead of its native cold constructor state')
    CheckMateIds(graph.RootsValue,link);CheckMateWrappers(graph.RootsValue)
    CheckPerpRefs(node,context.ModelNode);CheckPerpEpoch(graph.RootsValue,link.ConfigValue.HeaderValue)
    plan=ReadPlanarMate(context,node,19000)
    require(plan.KindValue=='perpendicular' and plan.AlignmentCode==0 and plan.DistanceValue is None,'generated mate semantics differ')
    endpoints=[]
    for endpoint,target,row in zip(plan.Endpoints,expected['ordered_endpoints'],node.FieldsValue['f410'],strict=True):
        CheckMatePoint(endpoint,context);CheckPerpDatum(endpoint,row['o'],context)
        item=items[target['occurrence']]
        require(endpoint.OccurrenceFeatureId==item.feature_id and matches(endpoint.NormalValue,target['normal'])
                and matches(endpoint.OriginValue,target['point_m']),'generated reference geometry differs from independent neutral prediction')
        require(endpoint.DatumName=={'x':'Right Plane','y':'Top Plane','z':'Front Plane'}[target['axis']],'the generated actual child datum differs')
        require(row['o'].FieldsValue['f50']==0,'the generated wrapper copied solved rigid status')
        endpoints.append({'occurrence':target['occurrence'],'occurrence_feature_id':endpoint.OccurrenceFeatureId,
                          'datum_id':endpoint.DatumFeatureId,'datum_name':endpoint.DatumName,'normal':endpoint.NormalValue,'point_m':endpoint.OriginValue})
    flags=ReadFixedFlags(context)
    require([i for i,item in enumerate(flags) if item['fixed']]==[expected['fixed_occurrence']],'the generated fixed anchor differs')
    child_doc=open_document(child,include_brep=False,include_tessellation=False)
    child_doc.assert_valid()
    by_id={value.id:value for value in child_doc.parameters}
    sketch=child_doc.sketches[0]
    sketch_lengths=[by_id[key].value.value/1000 for key in sketch.parameter_ids]
    depth=[value.value.value/1000 for value in child_doc.parameters if value.id not in sketch.parameter_ids]
    require(matches([*sketch_lengths,*depth],expected['child_driver_values_m']),'generated child lost its real three driving dimensions')
    try:
        document=open_document(parent,include_brep=False,include_tessellation=False)
    except ValueError as error:
        source_status={'status':'rejected','diagnostic':str(error)}
    else:
        source_status=dict(document.metadata.get('solidworks.typed_mates_semantics',{}))
    require(source_status.get('status')!='admitted','the frozen solved-only source reader unexpectedly admitted cold generated state')
    print(json.dumps({'passed':True,'parent_sha256':sha256(parent.read_bytes()).hexdigest(),'child_sha256':sha256(child.read_bytes()).hexdigest(),
                      'complete_typed_mate_bytes':True,'actual_owned_endpoints':endpoints,'cold_alignment':0,'cold_solve_state':0,'fresh_wrapper_rigid_state':0,
                      'fixed_flags':flags,'child_driver_count':3,'independent_geometry_prediction_equal':True,
                      'map_base':graph.MapBase,'map_terminal':graph.MapValue.CounterValue,'frozen_source_reader_status':source_status,
                      'native_acceptance':False,'public_writer_qualified':False},sort_keys=True,allow_nan=False))


if __name__=='__main__':main()
