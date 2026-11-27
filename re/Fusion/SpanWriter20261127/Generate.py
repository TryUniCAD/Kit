from dataclasses import replace
from importlib import import_module
from pathlib import Path
import hashlib
import json
import math
import sys
import uuid

from convert.Formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.Formats.Fusion.DocumentCodec.Model.CreateAuthor import CreateAuthor
from convert.Formats.Fusion.DocumentCodec.Defaults.BaseDefaults import BaseDefaults
from convert.Formats.Fusion.DocumentCodec.Defaults.SketchDefaults import SketchDefaults
from convert.Formats.Fusion.DocumentCodec.Defaults.ExtrudeDefaults import ExtrudeDefaults
from convert.Formats.Fusion.DocumentCodec.Defaults.MakeNumeric import MakeNumeric
from convert.Formats.Fusion.DocumentCodec.Records.EmitDesign import EmitDesign
from convert.Formats.Fusion.DocumentCodec.BuildBodyPart import BuildBodyPart
from convert.Formats.Fusion.DocumentCodec.Materials.BuildMatPart import BuildMatPart
from convert.Formats.Fusion.DocumentCodec.PackDocument import PackDocument
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from SpanHistory import emit_span_history
from convert.Formats.Fusion.BrepCodec.Models.BodyIdentity import BodyIdentity
from convert.Formats.Fusion.BrepCodec.Models.FeatureTag import FeatureTag
from convert.Formats.Fusion.BrepCodec.Models.HistoryState import HistoryState
from convert.Formats.Fusion.BrepCodec.Models.SketchLink import SketchLink
from convert.Formats.Fusion.BrepCodec.Models.TopologyTags import TopologyTags
from convert.Formats.Fusion.GeometryCodec.CylinderBody import CylinderBody
from convert.Formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp
from convert import open_document

BUILDERS = [('Foundation', n) for n in ['AddRootsMut','AddCollectMut','AddComputeMut','AddGeometryMut','AddUnitsMut','LinkCompMut','LinkRootsMut']]
BUILDERS += [('Sketch',n) for n in ['AddCircleMut','LinkCircleMut']]
BUILDERS += [('Extrusion',n) for n in ['AddExtrudeMut','BindParamsMut','LinkProfileMut','LinkExtrudeMut','LinkBodyMut']]
BUILDERS += [('Materials','LinkMaterialMut')]
BUILDERS = [getattr(import_module('convert.Formats.Fusion.DocumentCodec.'+group+'.'+name),name) for group,name in BUILDERS]


def generate(radius, first, second, offset):
    if not all(math.isfinite(v) for v in (radius, first, second, offset)) or min(radius,first,second)<=0:
        raise ValueError('finite positive radius and side distances required')
    spec=DocumentSpec('Generated circular span','firstDistance',first,RadiusMm=radius)
    author=CreateAuthor(spec,str(uuid.uuid4()))
    author.Defaults.update(BaseDefaults());author.Defaults.update(SketchDefaults());author.Defaults.update(ExtrudeDefaults())
    for build in BUILDERS: build(author)
    children=author.FindEntity('dc_extrude').FieldValues['childNodes']
    names=author.FindEntity('parameter_names').FieldValues['parameterMap']
    entries=[('against','AgainstDistance',second,'mm'),('second_taper','Side2TaperAngle',0.,'deg')]
    entries.append(('offset','ProfileOffset',offset,'mm'))
    for number,(role,native,value,unit) in enumerate(entries,3):
        name='d'+str(number+1)
        author.Allocate(role+'_parameter','Parameter',ParentRole='parameters')
        author.Allocate(role+'_binding','DcDoubleParameter',ParentRole='nodes',Subjects=['dc_extrude'])
        author.Allocate(role+'_dynamic','DynamicUpdateData')
        parameter=MakeNumeric(name,value,'',author.Policy.ParamBirthday)
        parameter.update(creationIndex=number+1,dcParameter=author.Reference(role+'_binding'),isUserDefined=False,name=native,unit=unit,expression=str(value)+(' deg' if unit=='deg' else ' mm'),value=value if unit=='deg' else value/10)
        author.Change(role+'_parameter',**parameter)
        author.Change(role+'_binding',value=parameter['value'],parameter=author.Reference(role+'_parameter'),rparamId=number,rrOwnerFeature=author.Reference('dc_extrude'),rParentFeature=author.Reference('dc_extrude'),rDynamicUpdateData=author.Reference(role+'_dynamic'))
        author.Change(role+'_dynamic',rOwnerNode=author.Reference(role+'_binding'),timeStamp=author.Policy.TimeStamp)
        children.append(author.Reference(role+'_binding'))
        names.append({'key':name,'value':author.Reference(role+'_parameter')})
        author.FindEntity('parameter_names').Subjects.append(role+'_parameter')
    author.Change('parameters',highWaterMark=len(entries)+3)
    author.Change('fragment',nextParamId=len(entries)+2)
    author.Change('dc_extrude',directionType=2,extendFaceOption=1,side2ExtentType=1,side2ExtendFaceOption=1,rAgainstDistance=author.Reference('against_binding'),side2TaperAngle=author.Reference('second_taper_binding'))
    author.Change('dc_extrude',profileLocaltionType=1,profileOffset=author.Reference('offset_binding'))
    lower=offset-second;upper=offset+first;height=first+second
    r=radius/10;h=height/10;center=(lower+upper)/20;volume=math.pi*r*r*h
    cache=author.FindEntity('body').FieldValues['cache'][0]['fields']
    cache.update(area=2*math.pi*r*(r+h),volume=volume,cog={'x':0.,'y':0.,'z':center},moi={'x':volume*(r*r/4+h*h/12+center*center),'y':volume*(r*r/4+h*h/12+center*center),'z':volume*r*r/2})
    design=EmitDesign(author)
    policy=author.Policy;operations=(policy.FirstOperationId+1,);sketch=policy.FirstSketchTag+2
    tags=TopologyTags(FeatureTag(policy.SideFaceLabel,operations),FeatureTag(policy.TopFaceLabel,operations),FeatureTag(policy.BottomFaceLabel,operations),FeatureTag(policy.TopEdgeLabel,operations),FeatureTag('-'+str(sketch),operations),SketchLink(sketch,0,0,1,1))
    identity=BodyIdentity(policy.BodyKey,operations[0],policy.BodyProgenitorTag,0)
    history=HistoryState(policy.HistoryCurrentId,policy.HistoryInitialId,policy.HistoryCurrentStateId,policy.HistoryNextEntityTag,policy.HistoryBoardStatus,policy.HistoryMaxStateId)
    body=emit_span_history(CylinderBody(radius,height,(0.,0.,lower)),identity,tags,history,GeometryStamp('Kit','Research generated two sided span','2026-11-27'))
    part=replace(BuildBodyPart(spec,design)[0],Payload=body)
    return PackDocument(design,spec.Title,(part,*BuildMatPart(design)))


if __name__=='__main__':
    output=Path(sys.argv[1]);output.mkdir(exist_ok=False)
    results=[]
    for name,values in [('baseline',(13.,17.,29.,7.)),('negative',(7.1,31.7,14.3,-11.)),('holdout',(19.7,9.3,43.1,2.7))]:
        row={'case':name,'values_mm':values,'models':False,'vendor_loadable':False,'application_usable':False}
        try:
            payload=generate(*values);path=output/(name+'.f3d');path.write_bytes(payload)
            row.update(sha256=hashlib.sha256(payload).hexdigest(),size=len(payload))
            model=ReadDocument(payload);row['typed_roundtrip']=ReadDocument(EmitParsed(model))==model
            try: row['document']=json.loads(open_document(path).to_json());row['strict']='decoded'
            except Exception as error:row['strict']='rejected';row['reason']=str(error)
        except Exception as error:row['generation_error']=repr(error)
        results.append(row)
    (output/'Results.json').write_text(json.dumps(results,indent=2))
    print(json.dumps([{k:v for k,v in row.items() if k!='document'} for row in results],indent=2))
