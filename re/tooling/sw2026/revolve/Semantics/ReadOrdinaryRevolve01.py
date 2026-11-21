from collections import Counter
from dataclasses import dataclass, replace
from math import hypot, isclose, isfinite, tau

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Resolved.FindModelRoot import FindModelRoot
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismFrame import ReadPrismFrame
from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.CheckDimGroups import CheckDimGroups
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.LineAxisRule import LineAxisRule
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.ReadAxisDim import ReadAxisDim
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.ReadDimHandle import ReadDimHandle
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.ReadDimRows import ReadDimRows
from convert.adapters.solidworks.Core.TypedResolved.Lines.CheckLineEntity import CheckLineEntity
from convert.adapters.solidworks.Core.TypedResolved.Lines.CheckLineScope import CheckLineScope
from convert.adapters.solidworks.Core.TypedResolved.Lines.IsLineState import IsLineState
from convert.adapters.solidworks.Core.TypedResolved.Lines.LineEntity import LineEntity
from convert.adapters.solidworks.Core.TypedResolved.Lines.LineIndex import LineIndex
from convert.adapters.solidworks.Core.TypedResolved.Lines.LineLoop import LineLoop
from convert.adapters.solidworks.Core.TypedResolved.Lines.LineOrder import LineOrder
from convert.adapters.solidworks.Core.TypedResolved.Lines.LinePoint import LinePoint
from convert.adapters.solidworks.Core.TypedResolved.Lines.LineSegment import LineSegment
from convert.adapters.solidworks.Core.TypedResolved.Lines.ReadLinePoint import ReadLinePoint
from convert.adapters.solidworks.Core.TypedResolved.Lines.ReadLineSegment import ReadLineSegment
from convert.adapters.solidworks.Core.TypedResolved.Lines.ReadLiveLines import ReadLiveLines
from convert.adapters.solidworks.Core.TypedResolved.Lines.ReadLineRegions import ReadLineRegions
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from convert.adapters.solidworks.Core.TypedResolved.ReadParents import ReadParents
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from convert.adapters.solidworks.Core.TypedResolved.TypedProvenance import TypedProvenance
from interchange.Core.Common import FreezeMapping
from interchange.Enums.EnumValues import ValueKind
from interchange.Features.FeatureAngleRev import AngularRevolve
from interchange.Records.RecordParameter import Parameter, ParameterValue
from interchange.geometry.Models.Selection import SelectPathElem, Selection
from interchange.geometry.Models.Sketch import Sketch
from interchange.geometry.Models.VectorSpace import SpaceVector


@dataclass(frozen=True)
class RevolveProjection:
    Feature: ArchiveNode
    Profile: ArchiveNode
    AxisWrapper: ArchiveNode
    AxisHandle: ArchiveNode
    Display: ArchiveNode
    Dimension: ArchiveNode
    NativeParameter: ArchiveNode
    SketchValue: Sketch
    ParameterValue: Parameter
    SelectionValue: Selection
    Definition: AngularRevolve
    ReverseValue: bool
    RawAxisStartMetres: tuple[float, float, float]
    RawAxisEndMetres: tuple[float, float, float]
    RetiredPoints: tuple[LinePoint, ...]
    RetiredLines: tuple[object, ...]


def require(value, message):
    if not value:
        raise ValueError(message)


def number(value):
    require(type(value) in (int, float) and isfinite(value), 'finite native scalar required')
    return float(value)


def axis_point(row, index, axis_index):
    fields=row['point']
    CheckLineEntity(fields)
    require(row['kind']==0 and fields['pflags']==30 and fields['fe4']==0 and fields['fe8']==1
        and fields['f08']==0 and fields['fec']==0 and fields['has_jet']==0 and fields['ff0']==0
        and fields['f108']==-2 and fields['h2'] is None and type(fields['f0c']) is int
        and fields['f0c']>0, 'selected axis endpoint has unqualified native ownership')
    handle=RequireNative(fields['h1'],'sgLineHandle')
    require(ReadDimHandle(handle,'sgLineHandle')==axis_index,'selected axis endpoint adjacency differs')
    pos=fields['pos']
    return LinePoint(index,fields['f0c'],(number(pos['x'])*1000,number(pos['y'])*1000),
        (handle,),{k:v for k,v in fields.items() if k not in ('h1','h2')})


def world(frame, xy):
    return tuple(getattr(frame.origin,k)+getattr(frame.x_axis,k)*xy[0]+getattr(frame.y_axis,k)*xy[1]
        for k in ('x','y','z'))


def read_revolve(link, feature):
    features=IndexFeatures(link)
    feature=RequireNative(feature,'moRevolution_c')
    feature_id=NativeNodeId(feature)
    require(features.get(feature_id) is feature,'revolve feature does not alias its actual resolved root')
    root=RequireNative(FindModelRoot(link.ConfigValue.MapValue),'moPart_c')
    parents=ReadParents(feature)
    require(len(parents)==1 and parents[0].ClassValue.NameValue=='moProfileFeature_c'
        and features.get(NativeNodeId(parents[0])) is parents[0],'ordinary revolve requires its actual sole profile parent')
    profile=parents[0]
    profile_id=NativeNodeId(profile)
    fields=feature.FieldsValue
    require(fields['f820']==0 and type(fields['f824']) is int and fields['f824'] in (0,1)
        and fields['f808'] is None and fields['f810'] is None,
        'revolve legacy, two-sided or invalid direction mode is outside this profile')
    require(fields['f828']==3 and fields['f870']==1 and fields['f8e8']==0
        and IsLineState(fields['f818']), 'another ordinary revolve state or converted-sketch dimension would be lost')
    end=RequireNative(fields['f8d8'],'moRevEndSpec_c').FieldsValue
    require(end['f08']==1 and all(end[k]==0 for k in ('f138','f13c','f0c','f10','f140','f144'))
        and all(end[k] is None for k in ('f118','f120','f128','f130','f20','f28','f30')),
        'revolve requires the single active blind angular owner')
    display=RequireNative(end['f18'],'moDisplayAngularDim_c')
    handles=NativeRows(display.FieldsValue['f850'])
    require(display.FieldsValue['n850']==1 and len(handles)==1,'angular display is not singly owned')
    dim_handle=RequireNative(handles[0]['o'],'moFeatureDimHandle_c')
    require(dim_handle.FieldsValue['fe8'] is None and dim_handle.FieldsValue['f100'] is None,
        'angular handle is not the local feature-dimension branch')
    dimension=RequireNative(dim_handle.FieldsValue['ff0'],'AngleDim_c')
    param=RequireNative(dimension.FieldsValue['f28'],'moAngleParameter_c')
    require(param.FieldsValue['f68']==0 and param.FieldsValue['f20']=='' and param.FieldsValue['f48'] is None,
        'alternate angular parameter state or expression is unqualified')
    require(dimension.FieldsValue['f48'] is None and dimension.FieldsValue['f54']==0
        and dimension.FieldsValue['f30']==0 and dimension.FieldsValue['f60'] is None,
        'angular tolerance, driving mode or extra owner is unqualified')
    angle=number(param.FieldsValue['f58'])
    require(0<angle<=tau,'ordinary revolve angle must be positive and at most one turn')
    require(type(dimension.FieldsValue['f50']) is int and dimension.FieldsValue['f50']>=0,
        'angular dimension lacks its native persistent identity')
    wrapper=RequireNative(fields['f830'],'moLineRef_w')
    selected=RequireNative(wrapper.FieldsValue['f58'],'moCompSketchEntHandle_c')
    component=RequireNative(selected.FieldsValue['f58'],'moUnitComponent_c')
    require(component.FieldsValue['owner'] is root and component.FieldsValue['has_ext']==0
        and selected.FieldsValue['ff0']['f00']==profile_id
        and wrapper.FieldsValue['f60'] is None and wrapper.FieldsValue['has_f10']==0
        and wrapper.FieldsValue['has_f18']==0
        and all(selected.FieldsValue[k]==0 for k in ('has_fb0','has_fb8','has_fc0','has_fc8','has_fd0')),
        'axis is not the retained same-profile self-component selection')
    axis_handle=RequireNative(selected.FieldsValue['f0f8'],'sgLineHandle')
    axis_index=ReadDimHandle(axis_handle,'sgLineHandle')
    sketch=RequireNative(profile.FieldsValue['pd_f80'],'sgSketch')
    sf=sketch.FieldsValue
    CheckLineScope(sf,True,True)
    CheckDimGroups(sf['dims'])
    require(not ReadDimRows(sf['dims'],'ng2','val_g2') and IsLineState(sf['dims']['f118']),
        'ordinary revolve profile contains a sketch value driver or display')
    unary=tuple(ReadAxisDim(row,i,sketch,link) for i,row in enumerate(ReadDimRows(sf['dims'],'nlog1','log_g1')))
    require(len(unary)==4,'ordinary rectangular revolve requires its four actual unary relations')
    references=Counter(item.LineValue for item in unary)
    points=NativeRows(sf['points'])
    lines=NativeRows(sf['lines'])
    require(sf['npoints']==len(points) and sf['nlines']==len(lines) and 0<=axis_index<len(lines),
        'axis or sketch array counts are inconsistent')
    axis_row=lines[axis_index]
    af=axis_row['line']
    CheckLineEntity(af,0,12)
    require(axis_row['flags']==2 and af['fd0']==0 and af['fd4']==0 and af['fe8']==0
        and type(af['f08']) is int and af['f08']>0 and type(af['f0c']) is int and af['f0c']>0
        and selected.FieldsValue['f100']==af['f08'] and not references[axis_index],
        'selected construction line identity or unanchored relation state differs')
    axis=LineSegment(axis_index,af['f08'],af['f0c'],LineIndex(af,'fc8_s','fc8',65535),
        LineIndex(af,'fcc_s','fcc',65535),af)
    require(axis.StartValue!=axis.EndValue and all(0<=i<len(points) for i in (axis.StartValue,axis.EndValue)),
        'selected axis endpoints are missing or collapsed')
    axis_points={i:axis_point(points[i],i,axis_index) for i in (axis.StartValue,axis.EndValue)}
    live_lines=[]
    retired_lines=[]
    for i,row in enumerate(lines):
        if i==axis_index:continue
        if row['line']['f54']&1:
            require(i==0,'unqualified retired line history')
            empty,retired=ReadLiveLines((row,),{})
            require(not empty,'retired line unexpectedly projects live geometry')
            retired_lines.extend(retired)
        else:
            live_lines.append(ReadLineSegment(row,i,references[i]))
    require(len(live_lines)==4 and set(references)=={line.IndexValue for line in live_lines}
        and set(references.values())=={1},'selected axis or other geometry entered the perimeter constraint graph')
    regions=ReadLineRegions(sketch,tuple(live_lines),link)
    CheckLineScope(sf,True,bool(regions))
    contour_indices={i for line in live_lines for i in (line.StartValue,line.EndValue)}
    require(len(contour_indices)==4 and not contour_indices.intersection(axis_points),
        'selected axis endpoints overlap the independent body contour')
    live_points={}
    retired_points=[]
    for i,row in enumerate(points):
        if i in axis_points:continue
        point=ReadLinePoint(row,i)
        if point.CreationId<0:retired_points.append(point)
        else:live_points[i]=point
    require(set(live_points)==contour_indices,'another live sketch point would be lost')
    require(len({p.CreationId for p in (*live_points.values(),*axis_points.values())})==6,
        'actual point creation identities are duplicated')
    loop=LineLoop(live_points,tuple(live_lines),LineOrder(live_points,tuple(live_lines)),
        NativeNodeSpan(link,sketch),RetiredRows=tuple(retired_lines),RegionValues=regions,RetiredPointRows=tuple(
            {'array_index':p.IndexValue,'native_fields':p.FieldsValue} for p in retired_points))
    all_points={**live_points,**axis_points}
    axis_loop=LineLoop(all_points,(axis,),(),NativeNodeSpan(link,sketch))
    entity_values=tuple(LineEntity(profile_id,loop,line) for line in live_lines)
    axis_entity=replace(LineEntity(profile_id,axis_loop,axis),construction=True)
    start,end_point=(axis_points[i].PositionValue for i in (axis.StartValue,axis.EndValue))
    require(isclose(start[0],end_point[0],abs_tol=1e-10) and end_point[1]>start[1],
        'only disclosed upward planar construction axes are qualified')
    require(min(p.PositionValue[0] for p in live_points.values())>start[0],
        'this ordinary rectangular profile crosses its selected axis')
    x_values={p.PositionValue[0] for p in live_points.values()}
    y_values={p.PositionValue[1] for p in live_points.values()}
    require(len(x_values)==len(y_values)==2 and set(p.PositionValue for p in live_points.values())
        =={(x,y) for x in x_values for y in y_values},'nonrectangular revolve profile is unqualified')
    require(all(isclose(
        live_points[line.StartValue].PositionValue[1 if rel.CodeValue==4 else 0],
        live_points[line.EndValue].PositionValue[1 if rel.CodeValue==4 else 0],abs_tol=1e-10)
        for rel in unary for line in live_lines if line.IndexValue==rel.LineValue),
        'actual unary solver direction and line coordinates disagree')
    frame=ReadPrismFrame(profile,root,features)
    ws,we=world(frame,start),world(frame,end_point)
    length=hypot(*(b-a for a,b in zip(ws,we,strict=True)))
    require(length>=1e-5,'selected axis is below native endpoint tolerance')
    raw_direction=tuple((b-a)/length for a,b in zip(ws,we,strict=True))
    reverse=bool(fields['f824'])
    effective_direction=tuple(v*(-1 if reverse else 1) for v in raw_direction)
    parameter_id=f'sldprt:parameter:{feature_id}:{ReadNativeName(param)}'
    feature_key=f'sldprt:feature:{feature_id}'
    parameter=Parameter(parameter_id,ReadNativeName(param),ParameterValue(angle,ValueKind.KAngle,'rad'),
        owner_id=feature_key,provenance=TypedProvenance(NativeNodeSpan(link,param),str(dimension.FieldsValue['f50'])),
        attributes=FreezeMapping({'native_dimension_id':dimension.FieldsValue['f50'],
            'native_display_index':display.IndexValue,'native_handle_index':dim_handle.IndexValue,
            'native_parameter_fields':param.FieldsValue,'native_value_field':'f58','native_end_slot':'f8d8.f18'}))
    selection=Selection(f'sldprt:selection:{feature_id}:axis','Revolve axis',
        (SelectPathElem('sketch',f'sldprt:sketch:{profile_id}'),SelectPathElem('sketch_entity',axis_entity.id)),
        provenance=TypedProvenance(NativeNodeSpan(link,wrapper),str(axis.PermanentId)),
        attributes=FreezeMapping({'native_axis_array_index':axis_index,'native_permanent_mark':axis.PermanentId,
            'native_line_creation_id':axis.CreationId,'native_selected_handle_index':axis_handle.IndexValue,
            'native_ordered_endpoints_m':(tuple(v*.001 for v in ws),tuple(v*.001 for v in we)),
            'native_reverse_direction':reverse}))
    definition=AngularRevolve(selection.id,parameter.id,SpaceVector(*ws),SpaceVector(*effective_direction))
    rules=tuple(LineAxisRule(profile_id,relation,tuple(v.id for v in entity_values),
        tuple(line.IndexValue for line in live_lines)) for relation in unary)
    support_id=RequireNative(profile.FieldsValue['pd_f78'],'moCompRefPlane_c').FieldsValue['ff0']['f00']
    sketch_value=Sketch(f'sldprt:sketch:{profile_id}',ReadNativeName(profile),
        support_plane_id=f'sldprt:plane:{support_id}',entities=entity_values+(axis_entity,),constraints=rules,
        closed_profile_entity_ids=(tuple(entity_values[i].id for i in loop.OrderValue),),
        attributes=FreezeMapping({'native_point_indices':tuple(all_points),
            'native_retired_point_indices':tuple(p.IndexValue for p in retired_points),
            'native_retired_line_rows':tuple(retired_lines),'native_line_regions':regions,'axis_has_no_solver_relation':True,
            'native_sketch_solver_status_unmeasured':True,
            'native_point_rows':tuple({'array_index':point.IndexValue,'native_creation_id':point.CreationId,
                'native_fields':point.FieldsValue,'line_handles':tuple({'class':handle.ClassValue.NameValue,
                    'object_index':handle.IndexValue,'fields':dict(handle.FieldsValue)}
                    for handle in point.HandlesValue)} for point in (*all_points.values(),*retired_points))}))
    return RevolveProjection(feature,profile,wrapper,axis_handle,display,dimension,param,
        sketch_value,parameter,selection,definition,reverse,tuple(v*.001 for v in ws),
        tuple(v*.001 for v in we),tuple(retired_points),tuple(retired_lines))
