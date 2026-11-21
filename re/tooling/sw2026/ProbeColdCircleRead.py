from __future__ import annotations

import argparse
from codecs import lookup
from dataclasses import replace
from hashlib import sha256
from importlib import import_module
from io import BytesIO
import json
from math import isclose,pi,sqrt
from pathlib import Path,PureWindowsPath
import sys


def require(value,message):
    if not value:raise ValueError(message)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('root',type=Path)
    parser.add_argument('phase',choices=('input','read'))
    parser.add_argument('--variant',choices=('front','top'),default='front')
    parser.add_argument('--edited',action='store_true')
    args=parser.parse_args()
    root=args.root.resolve(strict=True)
    sys.path[:0]=[str(root/'src'),str(root)]
    from interchange.serialization.EncodeData import ToData
    from interchange.serialization.Deserialize import FromData
    if args.phase=='input':
        from tests.Convert.Solidworks.Research.AdapterBridge.Circles.MakeWriteCircle import MakeWriteCircle
        document=MakeWriteCircle('ColdCircleFront' if args.variant=='front' else 'ColdCircleTop',args.variant=='top')
        if args.edited:
            sketch=document.sketches[0]
            entity=sketch.entities[0]
            sketch=replace(sketch,entities=(replace(entity,geometry=replace(entity.geometry,radius=entity.geometry.radius*1.173)),))
            feature=document.feature_timeline[0]
            feature=replace(feature,definition=replace(feature.definition,length=replace(feature.definition.length,value=feature.definition.length.value*1.417)))
            parameters=tuple(replace(value,value=replace(value.value,value=value.value.value*(1.417 if value.owner_id==feature.id else 1.173))) for value in document.parameters)
            document=replace(document,sketches=(sketch,),feature_timeline=(feature,),parameters=parameters)
        print(json.dumps({'document':ToData(document),'created_at':1765500071,'variant':args.variant,'mutation':None},sort_keys=True))
        return 0
    from convert import open_document,write_document
    from convert.api.ApiContext import GetRegistry
    from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
    from convert.adapters.solidworks.Archive.Config.MakeLinkContext import MakeLinkContext
    from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
    from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
    from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
    from convert.adapters.solidworks.Container.Container import SldprtArchive,BuildSldprt
    from convert.adapters.solidworks.Core.Adapter import NativePartModel
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
    ReadCircleGeom=None
    if (root/"src/convert/adapters/solidworks/Core/TypedResolved/Geometry/Circles/ReadCircleGeom.py").is_file():
        from convert.adapters.solidworks.Core.TypedResolved.Geometry.Circles.ReadCircleGeom import ReadCircleGeom
    from interchange.brep.Surfaces.BrepSurfaces import CylinderSurface,PlaneSurface
    from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit
    request=json.load(sys.stdin)
    document=FromData(request['document'])
    GetRegistry()
    emit=import_module('convert.adapters.solidworks.Core.Writing.EmitNativeMut')
    def clock():return request['created_at']
    emit.ReadTime=clock
    stream=BytesIO()
    output=write_document(document,stream,destination_format='solidworks.sldprt',allow_carrier=False,values={'require_native_transfers':True,'final_destination':str(PureWindowsPath('C:/KitSdkCandidates')/(document.metadata['name']+'.SLDPRT'))})
    original=stream.getvalue()
    archive=SldprtArchive.from_bytes(original)
    require(not any('Partition' in row.name for row in archive.records),'the actual public circle writer emitted a geometry cache')
    mutation=request.get('mutation')
    if mutation:
        link=ReadNativeLink(archive,0)
        boss=link.ResolvedValue.RootsValue[-1]
        profile=link.ResolvedValue.RootsValue[-2]
        end=boss.FieldsValue['f818']
        def parameter(field):return end.FieldsValue[field].FieldsValue['f850'][0]['o'].FieldsValue['ff0'].FieldsValue['f28']
        if mutation=='draft':parameter('fc8').FieldsValue['f58']=0.013
        elif mutation=='inactive-length':parameter('f20').FieldsValue['f58']+=0.00237
        elif mutation=='scope':boss.FieldsValue['f544']=1
        elif mutation=='radius':profile.FieldsValue['pd_f80'].FieldsValue['points'][1]['point']['pos']['x']+=0.000731
        elif mutation=='support':profile.FieldsValue['pd_f78'].FieldsValue['ff0']['f00']=next(row.FieldsValue['f08'] for row in link.ResolvedValue.RootsValue if row.ClassValue.NameValue=='moRefPlane_c' and row.FieldsValue['f08']!=profile.FieldsValue['pd_f78'].FieldsValue['ff0']['f00'])
        elif mutation=='extra-parent':
            parents=boss.FieldsValue['f60']['list'];parents['items']=[*parents['items'],{'o':link.ResolvedValue.RootsValue[0]}];parents['n']=len(parents['items'])
        else:raise ValueError('unknown declared negative')
        header=ReadHeaderGraph(archive.require('Contents/Config-0-ModelHeader'),19000)
        cmgr=ReadCmgrMut(archive.require('Contents/CMgr'),19000)
        config_bytes,config=WriteConfigMut(link.ConfigValue.RootValue,19000,header)
        resolved_bytes,_=WriteResolMut(link.ResolvedValue.RootsValue,link.ResolvedValue.ExtraFields,19000,config.MapValue,MakeLinkContext(config,cmgr))
        streams={row.name:row.data for row in archive.records}
        streams.update({'Contents/Config-0':config_bytes,'Contents/Config-0-ResolvedFeatures':resolved_bytes})
        payload=BuildSldprt(streams,FormatVersion=4)
    else:payload=original
    for name in ('utf-16-le','utf-8','latin-1','utf-16'):lookup(name)
    audit=BuildAudit(root/'re/tooling/sw2026/serial/defs')
    sys.addaudithook(audit.InspectEvent)
    result={'schema':'kit.sw2026.public-cold-circle-read-probe.v1','variant':request['variant'],'mutation':mutation,'input_document_sha256':sha256(json.dumps(request['document'],sort_keys=True,separators=(',',':')).encode()).hexdigest(),'public_writer_payload_sha256':sha256(original).hexdigest(),'public_writer_payload_bytes':len(original),'observed_payload_sha256':sha256(payload).hexdigest(),'public_writer_format':output.adapter,'native_face_identity':False,'native_processes_started':0,'hidden_inputs_read':0}
    try:
        actual=open_document(payload,source_format='solidworks.sldprt')
    except ValueError as error:
        result.update(passed=False,error=str(error))
        if not mutation:
            try:
                if ReadCircleGeom is None:raise ValueError("cold circle route absent in baseline")
                archive=SldprtArchive.from_bytes(payload)
                model=NativePartModel(archive,None)
                from convert.adapters.solidworks.Core.TypedResolved.Geometry.Circles.CircleClasses import KCircleClasses
                from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
                detail_link=ReadNativeLink(archive,0)
                detail_mgr=ReadCmgrMut(archive.require('Contents/CMgr'),19000)
                result['unlisted_circle_owners']=sorted({entry.EntryValue.ClassValue.NameValue for entry in (*detail_link.ResolvedValue.MapValue.EntriesValue,*detail_mgr.MapValue.EntriesValue) if isinstance(entry.EntryValue,ArchiveNode) and entry.EntryValue.ClassValue.NameValue not in KCircleClasses})
                ReadCircleGeom(ReadNativeLink(archive,0),ReadCmgrMut(archive.require('Contents/CMgr'),19000),model,'sldprt:body:1')
            except (ValueError,TypeError,KeyError) as detail:result['typed_guard_failure']=str(detail)
        print(json.dumps({**result,'runtime_data_file_reads':len(audit.DeniedReads)},sort_keys=True))
        return 3
    require(not mutation,'a malformed circle archive was accepted')
    brep=actual.brep
    require(brep is not None and len(actual.bodies)==1 and len(brep.faces)==3 and len(brep.bodies)==1 and not actual.brep_payloads,'normal strict read lost the complete cold cylinder')
    cylinder=[row for row in brep.surfaces if type(row) is CylinderSurface]
    require(len(cylinder)==1,'strict read lacks a unique analytic cylinder')
    surface=cylinder[0]
    faces=[row for row in brep.faces if row.surface_id==surface.id]
    require(len(faces)==1 and brep.bodies[0].design_body_id==actual.bodies[0].id,'cylinder face lost its actual returned body ownership')
    circle=document.sketches[0].entities[0].geometry
    depth=document.feature_timeline[0].definition.length.value
    topology=actual.bodies[0].topology
    require(topology is not None and isclose(topology.volume,pi*circle.radius**2*depth,rel_tol=1e-12) and isclose(topology.surface_area,2*pi*circle.radius*(circle.radius+depth),rel_tol=1e-12),'strict read disagrees with independent cylinder measures')
    frame=document.support_planes[0].transform
    lower,upper=(-depth,0.0) if document.feature_timeline[0].definition.reversed else (0.0,depth)
    center=[getattr(frame.origin,name)+circle.center.x*getattr(frame.x_axis,name)+circle.center.y*getattr(frame.y_axis,name) for name in 'xyz']
    caps=[[center[index]+station*getattr(frame.z_axis,name) for index,name in enumerate('xyz')] for station in (lower,upper)]
    require(all(isclose(getattr(surface.origin,name),caps[0][index],abs_tol=1e-9) and isclose(getattr(surface.axis,name),getattr(frame.z_axis,name),abs_tol=1e-12) for index,name in enumerate('xyz')) and isclose(surface.radius,circle.radius,abs_tol=1e-10),'strict cylinder carrier differs from the authored support and signed stations')
    planes=[row for row in brep.surfaces if type(row) is PlaneSurface]
    require(len(planes)==2 and all(any(all(isclose(getattr(plane.origin,name),point[index],abs_tol=1e-9) for index,name in enumerate('xyz')) for plane in planes) for point in caps),'strict cylinder caps differ from independent endpoints')
    require(topology.bounding_box is not None,'strict cylinder bounds are absent')
    for index,name in enumerate('xyz'):
        radial=circle.radius*sqrt(getattr(frame.x_axis,name)**2+getattr(frame.y_axis,name)**2)
        low=min(caps[0][index],caps[1][index])-radial
        high=max(caps[0][index],caps[1][index])+radial
        require(isclose(getattr(topology.bounding_box.minimum,name),low,abs_tol=1e-9) and isclose(getattr(topology.bounding_box.maximum,name),high,abs_tol=1e-9),'strict cylinder bounds differ from independent axis extents')
    require(not brep.validate(frozenset(row.id for row in actual.bodies)) and not audit.DeniedReads,'strict cold cylinder topology or runtime read guard failed')
    diagnostics=[{'code':row.code,'message':row.message,'attributes':dict(row.attributes)} for row in actual.diagnostics if row.code=='sldprt.brep_reconstructed']
    require(len(diagnostics)==1 and diagnostics[0]['attributes']['method']=='typed_parametric_circular_boss','normal result lost exact reconstruction provenance')
    result.update(passed=True,solid_count=topology.solid_count,faces=len(brep.faces),edges=len(brep.edges),vertices=len(brep.vertices),volume_mm3=topology.volume,area_mm2=topology.surface_area,face_id=faces[0].id,surface_id=surface.id,axis_origin_mm=[getattr(surface.origin,name) for name in 'xyz'],axis_direction=[getattr(surface.axis,name) for name in 'xyz'],radius_mm=surface.radius,sketches=len(actual.sketches),features=len(actual.feature_timeline),parameters=len(actual.parameters),diagnostics=diagnostics,runtime_data_file_reads=0,source_module_reads=len(audit.ModuleReads))
    print(json.dumps(result,sort_keys=True,allow_nan=False))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
