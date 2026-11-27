from dataclasses import replace
import math

from convert.adapters.Fusion.Native.Graph.GraphChecks import EmptyFields, LinkedNodes, RequireFields, ResolveField, SameNumbers
from convert.adapters.Fusion.Native.Graph.GraphValues import CheckIdentity, ObjectFields, PointCoords
from convert.adapters.Fusion.Native.Policy.CheckScopes import CheckScopes
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.ConeNode import ConeNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.EllipseNode import EllipseNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.PlaneNode import PlaneNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.PointNode import PointNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.TransformNode import TransformNode
from convert.Formats.Fusion.BrepCodec.Journal.Permutation.RemapEntity import RemapEntity
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.CheckGeometry import CheckGeometry
from convert.Formats.Fusion.EntityCodec.Model.MatrixValue import MatrixValue
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorSpace import SpaceVector


def read_frame(graph,context,model):
    checks=[]
    def require(condition,name):
        checks.append(dict(field=name,passed=bool(condition)))
        if not condition:raise ValueError('XZ selected frame '+name+' disagrees')
    matrix=ResolveField(graph,context.SketchFeature,'rSketchPlaneMatrix','DRMatrix')
    references=LinkedNodes(graph,matrix,'dataRefs');require(len(references)==1,'unique_reference')
    reference=references[0];recipe=ResolveField(graph,reference,'rRecipe','EntityRecipe');datum=graph.ResolveId(recipe.Fields['m_entityId'])
    origin=ResolveField(graph,context.Component,'m_rOriginWorkGeometry','OriginWorkGeometry')
    require(datum.ClassName=='WorkPlane' and datum in LinkedNodes(graph,origin,'children'),'selected_origin_member')
    require(graph.Resolve(datum.Fields['rParent'])==origin and graph.Resolve(origin.Fields['rParent'])==context.Component,'datum_component_parent')
    require(graph.Resolve(context.Plane.Fields['rParent'])==context.Component,'ucs_component_parent')
    require(graph.Resolve(context.Sketch.Fields['UCS'])==context.Plane,'sketch_ucs')
    require(graph.Resolve(context.Sketch.Fields['rDcNode'])==context.SketchFeature and graph.Resolve(context.SketchFeature.Fields['rSketch'])==context.Sketch,'reciprocal_sketch_feature')
    RequireFields(datum,{'originName':'XZ','isOrigin':True,'rDcNode':None});checks.append(dict(field='original_xz_datum',passed=True))
    plane=ObjectFields(datum.Fields['plane']);require(plane['normalReversed'] is False,'datum_normal_sense')
    for name,wanted in [('origin',(0.,0.,0.)),('uAxis',(0.,0.,1.)),('vAxis',(1.,0.,0.))]:
        SameNumbers(PointCoords(plane[name]),wanted);checks.append(dict(field='datum_'+name,passed=True))
    RequireFields(matrix,{'refType':2,'isZFlip':False,'isInferredXAxis':False,'isInferredZAxis':False,'rOrigin':None,'rXAxis':None,'rZAxis':None,'extraOffset':None,'globalReorientParam':None,'globalReorientParam1':None,'globalParamU':None,'globalParamV':None,'oldRotation':0.})
    EmptyFields(matrix,('rEdgeReferences','rPlaneReferences','values'));checks.append(dict(field='no_extra_frame_controls',passed=True))
    for owner in (matrix,reference):
        RequireFields(owner,{'isActive':True,'isEdited':False,'isEliminated':False})
        update=ResolveField(graph,owner,'rDynamicUpdateData','DynamicUpdateData')
        RequireFields(update,{'isBodyOK':True,'isPredecessorOK':True})
        require(graph.Resolve(owner.Fields['rParentFeature'])==context.SketchFeature and graph.Resolve(update.Fields['rOwnerNode'])==owner,owner.ClassName+'_owner')
    saved=context.Plane.Fields['transform'];require(isinstance(saved,MatrixValue) and saved.Entries is not None,'explicit_ucs_matrix')
    require(matrix.Fields['matrix3d']==saved,'ucs_matrix_agreement')
    values=saved.Entries
    xaxis=PointCoords(plane['vAxis']);yaxis=tuple(-v for v in PointCoords(plane['uAxis']));normal=(0.,1.,0.)
    expected=tuple(value for row in range(3) for value in (xaxis[row],yaxis[row],normal[row],0.))+(0.,0.,0.,1.)
    SameNumbers(values,expected);checks.append(dict(field='default_xz_principal_basis',passed=True))
    frame=Transform(SpaceVector(values[3]*10,values[7]*10,values[11]*10),SpaceVector(values[0],values[4],values[8]),SpaceVector(values[1],values[5],values[9]),SpaceVector(values[2],values[6],values[10]))
    SameNumbers(PointCoords(context.Extrude.Fields['profileNormal']),(frame.z_axis.x,frame.z_axis.y,frame.z_axis.z));checks.append(dict(field='extrusion_normal',passed=True))
    instance=graph.OneClass('ComponentInstance');require(graph.Resolve(instance.Fields['rTargetComponent'])==context.Component and instance.Fields['rParent'] is None,'root_instance_owner')
    CheckIdentity(instance.Fields['transform']);CheckIdentity(context.Sketch.Fields['occurrenceTransform'])
    if 'initialTransform' in instance.Fields:CheckIdentity(instance.Fields['initialTransform'])
    checks.append(dict(field='identity_occurrences',passed=True));CheckScopes(graph,context,model.Asset.AssetId);checks.append(dict(field='all_passive_scopes',passed=True))
    return frame,checks,values


def vector(value,frame,inverse):
    axes=[(a.x,a.y,a.z) for a in (frame.x_axis,frame.y_axis,frame.z_axis)]
    return tuple(sum(value[j]*axes[i][j] for j in range(3)) for i in range(3)) if inverse else tuple(sum(value[j]*axes[j][i] for j in range(3)) for i in range(3))


def point(value,frame,inverse):
    origin=(frame.origin.x/10,frame.origin.y/10,frame.origin.z/10)
    if inverse:return vector(tuple(v-o for v,o in zip(value,origin,strict=True)),frame,True)
    return tuple(v+o for v,o in zip(vector(value,frame,False),origin,strict=True))


def map_entity(entity,frame,inverse):
    if isinstance(entity,ConeNode):return replace(entity,OriginCm=point(entity.OriginCm,frame,inverse),AxisVector=vector(entity.AxisVector,frame,inverse),MajorAxisCm=vector(entity.MajorAxisCm,frame,inverse))
    if isinstance(entity,EllipseNode):return replace(entity,OriginCm=point(entity.OriginCm,frame,inverse),Normal=vector(entity.Normal,frame,inverse),MajorAxisCm=vector(entity.MajorAxisCm,frame,inverse))
    if isinstance(entity,PlaneNode):return replace(entity,OriginCm=point(entity.OriginCm,frame,inverse),Normal=vector(entity.Normal,frame,inverse),ReferenceAxis=vector(entity.ReferenceAxis,frame,inverse))
    if isinstance(entity,PointNode):return replace(entity,PositionCm=point(entity.PositionCm,frame,inverse))
    return entity


def local_view(state,frame):
    bodies=[(i,e) for i,e in enumerate(state.Entities) if isinstance(e,BodyNode)]
    if len(bodies)!=1:raise ValueError('one live BODY required')
    body_index,body=bodies[0];slot=body.TransformRef
    if slot<0:raise ValueError('XZ corpus requires explicit body identity node')
    identity=state.Entities[slot]
    if identity!=TransformNode(-1,-1,(1.,0.,0.),(0.,1.,0.),(0.,0.,1.),(0.,0.,0.),1.,False,False,False):raise ValueError('body transform must be complete identity')
    order=tuple(i for i in range(len(state.Entities)) if i!=slot);mapping=tuple(order.index(i) if i in order else -1 for i in range(len(state.Entities)))
    entities=[]
    for index in order:
        entity=map_entity(state.Entities[index],frame,True)
        if index==body_index:entity=replace(entity,TransformRef=-1)
        entities.append(RemapEntity(entity,mapping))
    result=replace(state,Entities=tuple(entities));CheckGeometry(result)
    return result,dict(order=order,slot=slot,body_index=body_index,identity=identity)


def restore_view(local,frame,metadata):
    entities={metadata['slot']:metadata['identity']}
    for index,entity in enumerate(local.Entities):
        old=metadata['order'][index];value=RemapEntity(entity,metadata['order'])
        if old==metadata['body_index']:value=replace(value,TransformRef=metadata['slot'])
        entities[old]=map_entity(value,frame,False)
    result=replace(local,Entities=tuple(entities[i] for i in range(len(entities))));CheckGeometry(result);return result
