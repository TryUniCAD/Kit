import hashlib
import json
import math
import platform
import traceback
import adsk.core
import adsk.fusion

BASE = dict(first=61, second=23, origin=[1.1, -0.7, 0], direction=[0, 1, 0], radial=0.8, axial=0.6)
CASES = [("baseline", {}), ("first", dict(first=79)), ("second", dict(second=37)), ("swapped", dict(first=23, second=61)), ("origin", dict(origin=[-1.7, 2.3, 0])), ("direction", dict(direction=[0.6, 0.8, 0])), ("reversed", dict(direction=[0, -1, 0])), ("radial", dict(radial=1.3)), ("axial", dict(axial=-0.9)), ("holdout_a", dict(first=47, second=31, origin=[2.1, -1.3, 0], direction=[-0.8, 0.6, 0], radial=1.1, axial=-0.4)), ("holdout_b", dict(first=103, second=19, origin=[-0.3, -2.7, 0], direction=[0.8, -0.6, 0], radial=0.7, axial=1.2))]


def expected(spec):
    a, b = math.radians(spec['first']), math.radians(spec['second'])
    ri, ro, height = spec['radial'], spec['radial'] + 0.7, 1.9
    scale = 2 * (ro**3-ri**3)/(3*(a+b)*(ro**2-ri**2))
    radial = [-spec['direction'][1], spec['direction'][0], 0]
    center = [o+(spec['axial']+height/2)*d+scale*(math.sin(a)+math.sin(b))*n for o,d,n in zip(spec['origin'],spec['direction'],radial)]
    center[2] += scale*(math.cos(b)-math.cos(a))
    return dict(volume_cm3=(a+b)*(ro**2-ri**2)*height/2, center_cm=center)


def measure(design, spec):
    root = design.rootComponent
    f = root.features.revolveFeatures.item(0)
    physical = root.bRepBodies.item(0).getPhysicalProperties(adsk.fusion.CalculationAccuracy.HighCalculationAccuracy)
    reading = dict(body_count=root.bRepBodies.count, volume_cm3=physical.volume, area_cm2=physical.area, center_cm=physical.centerOfMass.asArray(), bounds_cm=[root.bRepBodies.item(0).boundingBox.minPoint.asArray(), root.bRepBodies.item(0).boundingBox.maxPoint.asArray()], health=int(f.healthState), error=f.errorOrWarningMessage, first=f.extentDefinition.angleOne.value, second=f.extentDefinition.angleTwo.value, operation=int(f.operation), solid=f.isSolid, project_axis=f.isProjectAxis, timeline=[dict(name=design.timeline.item(i).name, type=design.timeline.item(i).entity.objectType) for i in range(design.timeline.count)], parameters=[dict(name=p.name, role=p.role, expression=p.expression, value=p.value, unit=p.unit) for p in root.modelParameters])
    f.timelineObject.rollTo(True)
    try:
        axis = f.axis
        reading['axis'] = dict(type=axis.objectType, name=axis.name, origin_cm=axis.geometry.origin.asArray(), direction=axis.geometry.direction.asArray())
    finally:
        design.timeline.moveToEnd()
    target = expected(spec)
    reading['expected'] = target
    reading['geometry_pass'] = reading['body_count'] == 1 and reading['health'] == 0 and abs(reading['volume_cm3']-target['volume_cm3']) < 1e-7 and max(abs(a-b) for a,b in zip(reading['center_cm'],target['center_cm'])) < 1e-7
    reading['angles_pass'] = abs(reading['first']-math.radians(spec['first'])) < 1e-10 and abs(reading['second']-math.radians(spec['second'])) < 1e-10
    return reading


def export(design, name):
    path = work / (name+'.f3d')
    if path.exists():
        raise RuntimeError('refusing archive overwrite')
    if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(path))):
        raise RuntimeError('native export refused')
    return dict(file=path.name, sha256=hashlib.sha256(path.read_bytes()).hexdigest(), size=path.stat().st_size)


def build(doc, spec):
    design = adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
    design.designType = adsk.fusion.DesignTypes.ParametricDesignType
    root = design.rootComponent
    p = adsk.core.Point3D.create
    support = root.sketches.add(root.xYConstructionPlane)
    support.name = 'AxisSupport'
    first = support.sketchPoints.add(p(*spec['origin']))
    second = support.sketchPoints.add(p(*[o+4*d for o,d in zip(spec['origin'],spec['direction'])]))
    inputs = root.constructionAxes.createInput()
    if not inputs.setByTwoPoints(first, second):
        raise RuntimeError('construction axis refused')
    axis = root.constructionAxes.add(inputs)
    axis.name = 'ExplicitAxis'
    profile = root.sketches.add(root.xYConstructionPlane)
    profile.name = 'RevolveProfile'
    n = [-spec['direction'][1], spec['direction'][0], 0]
    corners = [p(*[o+t*d+r*v for o,d,v in zip(spec['origin'],spec['direction'],n)]) for t,r in [(spec['axial'],spec['radial']), (spec['axial']+1.9,spec['radial']), (spec['axial']+1.9,spec['radial']+0.7), (spec['axial'],spec['radial']+0.7)]]
    for i in range(4):
        profile.sketchCurves.sketchLines.addByTwoPoints(corners[i],corners[(i+1)%4])
    inputs = root.features.revolveFeatures.createInput(profile.profiles.item(0), axis, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    inputs.isSolid = True
    inputs.isProjectAxis = False
    if not inputs.setTwoSideAngleExtent(adsk.core.ValueInput.createByString(f"{spec['first']} deg"), adsk.core.ValueInput.createByString(f"{spec['second']} deg")):
        raise RuntimeError('two-sided extent refused')
    feature = root.features.revolveFeatures.add(inputs)
    feature.name = 'UnequalRevolve'
    return doc, design


report = dict(version=1, application=app.version, platform=platform.platform(), initial_documents=app.documents.count, cases=[], errors=[])
if report['initial_documents']:
    raise RuntimeError('initial native session is not empty')
for name, overrides in [('control_before', {}), *CASES, ('control_after', {})]:
    doc = None
    entry = dict(id=name, spec={**BASE, **overrides}, observations=[], archives=[])
    report['cases'].append(entry)
    try:
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        doc, design = build(doc, entry['spec'])
        if not design.computeAll():
            raise RuntimeError('native rebuild refused')
        entry['observations'].append(dict(stage='baseline', value=measure(design,entry['spec'])))
        entry['archives'].append(export(design,name))
        if not name.startswith('control'):
            for role in ('first','second'):
                feature = design.rootComponent.features.revolveFeatures.item(0)
                parameter = feature.extentDefinition.angleOne if role == 'first' else feature.extentDefinition.angleTwo
                original = parameter.expression
                changed = {**entry['spec'], role:entry['spec'][role]+7}
                try:
                    parameter.expression = f"{changed[role]} deg"
                    if not design.computeAll():
                        raise RuntimeError('edited rebuild refused')
                    entry['observations'].append(dict(stage='edit_'+role, value=measure(design,changed)))
                    entry['archives'].append(export(design,name+'_edit_'+role))
                finally:
                    parameter.expression = original
                    if not design.computeAll():
                        raise RuntimeError('restored rebuild refused')
                    entry['observations'].append(dict(stage='restore_'+role, value=measure(design,entry['spec'])))
            entry['archives'].append(export(design,name+'_restored'))
    except Exception:
        error = traceback.format_exc()
        entry['error'] = error
        report['errors'].append(dict(id=name,error=error))
    finally:
        if doc is not None:
            doc.close(False)
        (work/'Capture.json').write_text(json.dumps(report,indent=2))
report['final_documents'] = app.documents.count
result = report
