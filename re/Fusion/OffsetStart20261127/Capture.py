import hashlib
import json
import math
import os
import sys
import traceback
import adsk.core
import adsk.fusion

BASE = dict(first=17, second=29, offset=7, draft_first=0, draft_second=0, radius=13, center=[7,-11], basis='XY')
CASES = [('baseline',{}),('first',dict(first=23)),('second',dict(second=19)),('negative_offset',dict(offset=-9)),('zero_offset',dict(offset=0)),('radius',dict(radius=17)),('placement',dict(center=[-14,21])),('frame',dict(basis='XZ')),('swapped',dict(first=29,second=17)),('holdout_a',dict(first=21,second=13,offset=-11,radius=16,center=[19,5],basis='XZ')),('holdout_b',dict(first=31,second=11,offset=19,radius=19,center=[-9,-17]))]
DRIVERS = ('first','second','offset')



def expected(spec, sketch):
    r=spec['radius']/10
    total=moment=area=0
    ends=[]
    for sign,depth,draft in [(1,spec['first'],spec['draft_first']),(-1,spec['second'],spec['draft_second'])]:
        h=depth/10
        k=math.tan(math.radians(draft))
        end=r+h*k
        if end<=0:
            raise ValueError('requested tapered end has nonpositive radius')
        total+=r*r*h+r*k*h*h+k*k*h*h*h/3
        moment+=sign*(r*r*h*h/2+2*r*k*h*h*h/3+k*k*h*h*h*h/4)
        area+=math.pi*(r+end)*h*math.sqrt(1+k*k)+math.pi*end*end
        ends.append(dict(station_cm=sign*h,radius_cm=end))
    local=adsk.core.Point3D.create(spec['center'][0]/10,spec['center'][1]/10,spec['offset']/10+moment/total)
    center=sketch.sketchToModelSpace(local).asArray()
    return dict(volume_cm3=math.pi*total,area_cm2=area,center_cm=center,end_sections=ends)


def measure(design,spec):
    root=design.rootComponent
    sketch=root.sketches.item(0)
    feature=root.features.extrudeFeatures.item(0)
    body=root.bRepBodies.item(0)
    properties=body.getPhysicalProperties(adsk.fusion.CalculationAccuracy.HighCalculationAccuracy)
    circle=sketch.sketchCurves.sketchCircles.item(0)
    target=expected(spec,sketch)
    reading=dict(body_count=root.bRepBodies.count,body_solid=body.isSolid,volume_cm3=properties.volume,area_cm2=properties.area,center_cm=properties.centerOfMass.asArray(),bounds_cm=[body.boundingBox.minPoint.asArray(),body.boundingBox.maxPoint.asArray()],health=int(feature.healthState),error=feature.errorOrWarningMessage,first=feature.extentOne.distance.value,second=feature.extentTwo.distance.value,draft_first=feature.taperAngleOne.value,draft_second=feature.taperAngleTwo.value,operation=int(feature.operation),solid=feature.isSolid,two_sides=feature.hasTwoExtents,extent_type=int(feature.extentType),start_type=feature.startExtent.objectType,offset=feature.startExtent.offset.value,profile=dict(radius_cm=circle.radius,center_world_cm=sketch.sketchToModelSpace(circle.centerSketchPoint.geometry).asArray(),transform=sketch.transform.asArray()),parameters=[dict(name=p.name,role=p.role,value=p.value,unit=p.unit,expression=p.expression) for p in root.modelParameters],timeline=[dict(name=design.timeline.item(i).name,type=design.timeline.item(i).entity.objectType) for i in range(design.timeline.count)],expected=target)
    reading['geometry_pass']=reading['body_count']==1 and reading['body_solid'] and reading['health']==0 and abs(reading['volume_cm3']-target['volume_cm3'])<1e-7 and abs(reading['area_cm2']-target['area_cm2'])<1e-7 and max(abs(a-b) for a,b in zip(reading['center_cm'],target['center_cm']))<1e-7
    reading['settings_pass']=abs(abs(reading['first'])-spec['first']/10)<1e-10 and abs(abs(reading['second'])-spec['second']/10)<1e-10 and abs(reading['draft_first']-math.radians(spec['draft_first']))<1e-10 and abs(reading['draft_second']-math.radians(spec['draft_second']))<1e-10 and abs(reading['offset']-spec['offset']/10)<1e-10 and reading['two_sides'] and reading['operation']==int(adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    return reading


def export(design,name):
    path=work/(name+'.f3d')
    if path.exists():
        raise RuntimeError('refusing archive overwrite')
    if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(path))):
        raise RuntimeError('archive export refused')
    return dict(file=path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),size=path.stat().st_size)


def build(doc,spec):
    design=adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
    design.designType=adsk.fusion.DesignTypes.ParametricDesignType
    root=design.rootComponent
    sketch=root.sketches.add(root.xYConstructionPlane if spec['basis']=='XY' else root.xZConstructionPlane)
    sketch.name='CircularProfile'
    sketch.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(spec['center'][0]/10,spec['center'][1]/10,0),spec['radius']/10)
    inputs=root.features.extrudeFeatures.createInput(sketch.profiles.item(0),adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    value=adsk.core.ValueInput.createByString
    if not inputs.setTwoSidesExtent(adsk.fusion.DistanceExtentDefinition.create(value(f"{spec['first']} mm")),adsk.fusion.DistanceExtentDefinition.create(value(f"{spec['second']} mm")),value(f"{spec['draft_first']} deg"),value(f"{spec['draft_second']} deg")):
        raise RuntimeError('independent two-side extents refused')
    inputs.startExtent=adsk.fusion.OffsetStartDefinition.create(value(f"{spec['offset']} mm"))
    root.features.extrudeFeatures.add(inputs).name='OffsetTwoSides'
    return design


def driver(feature,role):
    if role=='offset':
        return feature.startExtent.offset
    if role=='first':
        return feature.extentOne.distance
    if role=='second':
        return feature.extentTwo.distance
    return feature.taperAngleOne if role=='draft_first' else feature.taperAngleTwo


report=dict(application=app.version,process_id=os.getpid(),initial_documents=app.documents.count,cases=[],errors=[])
if report['initial_documents']:
    raise RuntimeError('native session is not empty')
try:
    report['executable_sha256']=hashlib.sha256(__import__('pathlib').Path(sys.executable).read_bytes()).hexdigest()
except Exception as error:
    report['executable_hash_error']=type(error).__name__
for name,overrides in [('control_before',dict(offset=0)),*CASES,('control_after',dict(offset=0))]:
    doc=None
    case=dict(id=name,spec={**BASE,**overrides},observations=[],archives=[])
    report['cases'].append(case)
    try:
        doc=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        design=build(doc,case['spec'])
        if not design.computeAll():
            raise RuntimeError('native rebuild refused')
        case['observations'].append(dict(stage='baseline',value=measure(design,case['spec'])))
        case['archives'].append(export(design,name))
        if not name.startswith('control'):
            for role in DRIVERS:
                feature=design.rootComponent.features.extrudeFeatures.item(0)
                parameter=driver(feature,role)
                original=parameter.expression
                changed={**case['spec'],role:case['spec'][role]+(2 if role.startswith('draft') else 3)}
                try:
                    signed=-1 if role in ('first','second') and parameter.value<0 else 1
                    parameter.expression=f"{signed*changed[role]} {'deg' if role.startswith('draft') else 'mm'}"
                    if not design.computeAll():
                        raise RuntimeError('independent edit rebuild refused')
                    case['observations'].append(dict(stage='edit_'+role,value=measure(design,changed)))
                    case['archives'].append(export(design,name+'_edit_'+role))
                finally:
                    parameter.expression=original
                    if not design.computeAll():
                        raise RuntimeError('restoration rebuild refused')
                    case['observations'].append(dict(stage='restore_'+role,value=measure(design,case['spec'])))
            case['archives'].append(export(design,name+'_restored'))
    except Exception:
        case['error']=traceback.format_exc()
        report['errors'].append(dict(id=name,error=case['error']))
    finally:
        if doc is not None:
            doc.close(False)
        (work/'Capture.json').write_text(json.dumps(report,indent=2))
report['final_documents']=app.documents.count
result=report
