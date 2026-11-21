from math import isclose

from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrText import ReadCmgrText
from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import DatumTime
from convert.adapters.solidworks.Archive.Construction.PlanarMates.ReadDatumFrame import ReadDatumFrame
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismLoop import ReadPrismLoop
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismPlan import ReadPrismPlan
from convert.adapters.solidworks.Core.TypedResolved.ReadExtrude import ReadExtrude
from convert.adapters.solidworks.Drawing.Construction.Indexes.ReadViewIndex import ReadViewIndex
from convert.adapters.solidworks.Drawing.Definition.Profiles.NeedProfileMap import NeedProfileMap
from convert.adapters.solidworks.Drawing.Definition.Profiles.NeedProfileNode import NeedProfileNode
from convert.Geometry.Extrude.Polygon.PolygonExtrude import BuildPrism


def require(value,message):
    if not value:raise ValueError(message)


def single(values,message):
    require(len(values)==1,message)
    return values[0]


def endpoint_key(value):
    return tuple(sorted(tuple(float(v) for v in point) for point in value))


def resolve_rail(group,entry,origin,document):
    require(sum(value is entry for value in group.RowsValue)==1,'entry is not in its actual retained detailing group')
    view=origin.DisplayValue.ViewValue
    index=ReadViewIndex(view)
    reference=view.FieldsValue['f5d8']
    file=reference.FieldsValue['f3b0']
    filename=ReadCmgrText(file.FieldsValue['shared']['h10'].FieldsValue['value'])
    require(group.ModelKey==filename+'$$'+str(index.ConfigId),'detailing model/configuration key does not match the actual view')
    link=origin.ChildValue.LinkValue
    features={node.FieldsValue['f08']:node for node in link.ResolvedValue.RootsValue if node and type(node.FieldsValue.get('f08')) is int}
    boss=single([node for node in features.values() if node.ClassValue.NameValue=='moExtrusion_c'],'one actual child boss is required')
    owner=ReadExtrude(link,boss,features)
    plan=ReadPrismPlan(link,features)
    loop=ReadPrismLoop(owner.ProfileValue,link)
    fields=NeedProfileNode(entry.RefValue,'moEdgeRef_c').FieldsValue
    require(fields['f08']==4 and len(fields['f10'])==4 and fields['f40'] is None,'only the four-surface ordinary untrimmed edge is in this research profile')
    require(fields['f28']==fields['f30']==1e100,'finite edge parameter ranges remain unqualified')
    representations=[]
    for row in fields['f10']:
        rep=row['f08']
        require(rep.ClassValue.NameValue in ('moFromSktEntSurfIdRep_c','moEndFaceSurfIdRep_c'),'unsupported surface representation')
        NeedProfileNode(rep,rep.ClassValue.NameValue)
        keeper=NeedProfileMap(rep.FieldsValue['f10'])
        require(keeper['f08'] is None,'retained cached-feature keeper is outside the cold identity witness')
        fr=NeedProfileNode(keeper['f10'],'moFR_c')
        key=NeedProfileMap(fr.FieldsValue['f10'])
        require(key=={'f00':boss.FieldsValue['f08'],'f08':DatumTime(link.ConfigValue.HeaderValue,boss.FieldsValue['f08'])},'surface feature id or creation epoch differs from the actual child boss')
        child_file=NeedProfileNode(fr.FieldsValue['f08'],'moExtObject_c')
        shared=child_file.FieldsValue['shared']
        require(shared['f20']==2 and all(shared[k] is file.FieldsValue['shared'][k] for k in ('h10','h18')),'surface reference has foreign child identity handles')
        selection=child_file.FieldsValue['refcfg']
        require(ReadCmgrText(selection['f08'])==index.ConfigName and selection['f10']==index.ConfigId,'surface reference configuration differs')
        representations.append(rep)
    left,right,start,end=representations
    require(all(rep.ClassValue.NameValue=='moFromSktEntSurfIdRep_c' for rep in (left,right)) and all(rep.ClassValue.NameValue=='moEndFaceSurfIdRep_c' for rep in (start,end)),'only a side-side rail with two cap boundaries is in this witness')
    require({start.FieldsValue['f38'],end.FieldsValue['f38']}=={0,1} and all(rep.FieldsValue['f3c']==0 for rep in (start,end)),'ordinary opposite-cap single-contour boundaries are required')
    selected=[]
    for rep in (left,right):
        marker=rep.FieldsValue['f38']
        selected.append(single([line for line in loop.LinesValue if line.PermanentId==marker],'surface marker does not select one actual sketch line'))
    common={selected[0].StartValue,selected[0].EndValue}&{selected[1].StartValue,selected[1].EndValue}
    require(len(common)==1,'the two side surfaces do not meet at one actual contour point')
    point=loop.PointsValue[common.pop()]
    source_position=NeedProfileMap(point.FieldsValue['pos'])
    support=owner.ProfileValue.FieldsValue['pd_f78']
    plane_id=support.FieldsValue['ff0']['f00']
    frame,axis=ReadDatumFrame(features[plane_id])
    require(axis==3,'this endpoint witness requires its actual Front support')
    depth_m=owner.RequireDepth().Parameter.FieldsValue['f58']
    require(isclose(depth_m*1000,plan.DepthValue,abs_tol=1e-12,rel_tol=0),'native depth units do not match the independently typed prism')
    native_points=endpoint_key([tuple(frame.OriginValue[i]+source_position['x']*frame.AxisU[i]+source_position['y']*frame.AxisV[i]+station*frame.NormalValue[i] for i in range(3)) for station in (0.,depth_m)])
    require(document.source.sha256==origin.ChildValue.Sha256Value and len(document.bodies)==1,'independently read child body identity differs')
    body=document.bodies[0]
    require(body.final_feature_id=='sldprt:feature:'+str(boss.FieldsValue['f08']),'public body has another actual final feature')
    model,volume,area,bounds=BuildPrism(body.id,plan.FrameValue,plan.LinesValue,0.,plan.DepthValue)
    require(not model.validate(frozenset({body.id})),'reconstructed SDK B-rep is invalid')
    vertices={value.id:value for value in model.vertices}
    matches=[]
    for edge in model.edges:
        coordinates=endpoint_key([tuple(getattr(vertices[key].point,c)/1000 for c in ('x','y','z')) for key in (edge.start_vertex_id,edge.end_vertex_id)])
        if all(isclose(a,b,abs_tol=1e-12,rel_tol=0) for x,y in zip(coordinates,native_points,strict=True) for a,b in zip(x,y,strict=True)):matches.append(edge)
    edge=single(matches,'endpoint set does not bind exactly one reconstructed SDK edge')
    return {'downstream_id':entry.DownstreamId,'component_key_retained':entry.ComponentKey,
            'role_classes':[rep.ClassValue.NameValue for rep in representations],
            'surface_selectors':[rep.FieldsValue['f38'] for rep in representations],
            'actual_child_boss_id':boss.FieldsValue['f08'],'actual_child_profile_id':owner.ProfileValue.FieldsValue['f08'],
            'actual_body_final_feature_id':body.final_feature_id,'side_permanent_markers':[line.PermanentId for line in selected],
            'shared_point_array_index':point.IndexValue,'shared_point_creation_id':point.CreationId,
            'endpoint_set_model_m':native_points,'ordered_native_endpoints_qualified':False,
            'reconstructed_sdk_edge_id':edge.id,'reconstructed_body_id':body.id,
            'reconstructed_counts':{'vertices':len(model.vertices),'edges':len(model.edges),'faces':len(model.faces),'bodies':len(model.bodies)},
            'reconstructed_volume_mm3':volume,'reconstructed_area_mm2':area,
            'native_kernel_node_id':None,'native_kernel_identity':False,
            'public_default_brep_admission':False,'inner_component_key_projection':False}
