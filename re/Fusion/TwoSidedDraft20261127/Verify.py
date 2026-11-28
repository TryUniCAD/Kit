import base64
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import traceback
import zlib
import adsk.core
import adsk.fusion

CONTROLS=None
SOURCE_HASH=None
SPEC=None
DRIVERS=('first','second','draft_first','draft_second')


def design_of(document):
    return adsk.fusion.Design.cast(document.products.itemByProductType('DesignProductType'))


def reading(document):
    design=design_of(document)
    root=design.rootComponent
    body=root.bRepBodies.item(0)
    p=body.getPhysicalProperties(adsk.fusion.CalculationAccuracy.HighCalculationAccuracy)
    f=root.features.extrudeFeatures.item(0)
    sketch=root.sketches.item(0)
    circle=sketch.sketchCurves.sketchCircles.item(0)
    return dict(body_count=root.bRepBodies.count,body_solid=body.isSolid,volume_cm3=p.volume,area_cm2=p.area,center_cm=p.centerOfMass.asArray(),bounds_cm=[body.boundingBox.minPoint.asArray(),body.boundingBox.maxPoint.asArray()],health=int(f.healthState),error=f.errorOrWarningMessage,first=f.extentOne.distance.value,second=f.extentTwo.distance.value,draft_first=f.taperAngleOne.value,draft_second=f.taperAngleTwo.value,operation=int(f.operation),solid=f.isSolid,two_sides=f.hasTwoExtents,extent_type=int(f.extentType),start_type=f.startExtent.objectType,profile=dict(radius_cm=circle.radius,center_world_cm=sketch.sketchToModelSpace(circle.centerSketchPoint.geometry).asArray(),transform=sketch.transform.asArray()),parameters=[dict(name=p.name,role=p.role,value=p.value,unit=p.unit,expression=p.expression) for p in root.modelParameters])


def driver(feature,role):
    if role=='first':
        return feature.extentOne.distance
    if role=='second':
        return feature.extentTwo.distance
    return feature.taperAngleOne if role=='draft_first' else feature.taperAngleTwo


def reopen(path):
    return app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(path)))


def export(design,name):
    path=work/(name+'.f3d')
    if path.exists():
        raise RuntimeError('refusing archive overwrite')
    if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(path))):
        raise RuntimeError('independent export refused')
    return path


report=dict(build=app.version,process_id=os.getpid(),initial_documents=app.documents.count,observations=[],errors=[])
source=work/'source.f3d'
if report['initial_documents'] or hashlib.sha256(source.read_bytes()).hexdigest()!=SOURCE_HASH:
    raise RuntimeError('initial inventory or source hash differs')
try:
    report['executable_sha256']=hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest()
except Exception as error:
    report['executable_hash_error']=type(error).__name__
doc=None
try:
    for name,encoded in CONTROLS.items():
        (work/(name+'.f3d')).write_bytes(zlib.decompress(base64.b64decode(encoded)))
    (work/'control_after.f3d').write_bytes((work/'control_before.f3d').read_bytes())
    report['control_source_sha256']=hashlib.sha256((work/'control_before.f3d').read_bytes()).hexdigest()
    control=reopen(work/'control_before.f3d')
    try:
        if not design_of(control).computeAll():
            raise RuntimeError('before control rebuild refused')
        report['control_before']=reading(control)
    finally:
        control.close(False)
    doc=reopen(source)
    report['observations'].append(dict(stage='initial_open',value=reading(doc)))
    design=design_of(doc)
    if not design.computeAll():
        raise RuntimeError('fresh source rebuild refused')
    report['observations'].append(dict(stage='rebuilt',value=reading(doc)))
    for role in DRIVERS:
        f=design.rootComponent.features.extrudeFeatures.item(0)
        p=driver(f,role)
        original=p.expression
        changed=SPEC[role]+(2 if role.startswith('draft') else 3)
        try:
            signed=-1 if not role.startswith('draft') and p.value<0 else 1
            p.expression=f"{signed*changed} {'deg' if role.startswith('draft') else 'mm'}"
            if not design.computeAll():
                raise RuntimeError('fresh independent edit rebuild refused')
            report['observations'].append(dict(stage='edit_'+role,value=reading(doc)))
            saved=export(design,'verified_edit_'+role)
        finally:
            p.expression=original
            if not design.computeAll():
                raise RuntimeError('fresh restoration rebuild refused')
            report['observations'].append(dict(stage='restore_'+role,value=reading(doc)))
        opened=reopen(saved)
        try:
            report['observations'].append(dict(stage='reopen_edit_'+role,value=reading(opened)))
        finally:
            opened.close(False)
    saved=export(design,'verified_restored')
    doc.close(False)
    doc=None
    doc=reopen(saved)
    report['observations'].append(dict(stage='reopen_restored',value=reading(doc)))
except Exception:
    report['errors'].append(traceback.format_exc())
finally:
    if doc is not None:
        doc.close(False)
    try:
        control=reopen(work/'control_after.f3d')
        try:
            if not design_of(control).computeAll():
                raise RuntimeError('after control rebuild refused')
            report['control_after']=reading(control)
        finally:
            control.close(False)
    except Exception:
        report['errors'].append(traceback.format_exc())
    report['final_documents']=app.documents.count
    report['source_sha256']=hashlib.sha256(source.read_bytes()).hexdigest()
    report['archives']=[dict(file=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in work.glob('verified_*.f3d')]
    (work/'Verification.json').write_text(json.dumps(report,indent=2))
result=report
