import base64
import hashlib
import json
import sys
from pathlib import Path
import traceback
import adsk.core
import adsk.fusion

CONTROLS = None
SOURCE_HASH = None
SPEC = None


def native_design(document):
    return adsk.fusion.Design.cast(document.products.itemByProductType('DesignProductType'))


def reading(document):
    design = native_design(document)
    root = design.rootComponent
    body = root.bRepBodies.item(0)
    p = body.getPhysicalProperties(adsk.fusion.CalculationAccuracy.HighCalculationAccuracy)
    f = root.features.revolveFeatures.item(0)
    row = dict(body_count=root.bRepBodies.count, volume_cm3=p.volume, area_cm2=p.area, center_cm=p.centerOfMass.asArray(), bounds_cm=[body.boundingBox.minPoint.asArray(),body.boundingBox.maxPoint.asArray()], health=int(f.healthState), error=f.errorOrWarningMessage, first=f.extentDefinition.angleOne.value, second=f.extentDefinition.angleTwo.value, operation=int(f.operation), solid=f.isSolid, project_axis=f.isProjectAxis)
    f.timelineObject.rollTo(True)
    try:
        axis=f.axis
        row['axis']=dict(type=axis.objectType,name=axis.name,origin_cm=axis.geometry.origin.asArray(),direction=axis.geometry.direction.asArray())
    finally:
        design.timeline.moveToEnd()
    return row


def reopen(path):
    options = app.importManager.createFusionArchiveImportOptions(str(path))
    return app.importManager.importToNewDocument(options)


report = dict(build=app.version, process_id=__import__('os').getpid(), initial_documents=app.documents.count, observations=[], errors=[])
source = work/'source.f3d'
if report['initial_documents'] or hashlib.sha256(source.read_bytes()).hexdigest() != SOURCE_HASH:
    raise RuntimeError('initial inventory or source hash differs')
try:
    executable = Path(sys.executable)
    report['executable_sha256'] = hashlib.sha256(executable.read_bytes()).hexdigest()
except Exception as error:
    report['executable_hash_error'] = type(error).__name__
doc = None
try:
    for name, encoded in CONTROLS.items():
        path=work/(name+'.f3d')
        path.write_bytes(base64.b64decode(encoded))
    control=reopen(work/'control_before.f3d')
    try:
        report['control_before']=reading(control)
    finally:
        control.close(False)
    doc = reopen(source)
    report['observations'].append(dict(stage='initial_open', value=reading(doc)))
    design = native_design(doc)
    if not design.computeAll():
        raise RuntimeError('fresh rebuild refused')
    report['observations'].append(dict(stage='rebuilt', value=reading(doc)))
    for role in ('first','second'):
        f=design.rootComponent.features.revolveFeatures.item(0)
        parameter = f.extentDefinition.angleOne if role=='first' else f.extentDefinition.angleTwo
        original = parameter.expression
        try:
            parameter.expression = f"{SPEC[role]+7} deg"
            if not design.computeAll():
                raise RuntimeError('independent angle edit refused')
            report['observations'].append(dict(stage='edit_'+role,value=reading(doc)))
            saved=work/('verified_edit_'+role+'.f3d')
            if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(saved))):
                raise RuntimeError('independent edit save refused')
        finally:
            parameter.expression=original
            if not design.computeAll():
                raise RuntimeError('independent restoration refused')
            report['observations'].append(dict(stage='restore_'+role,value=reading(doc)))
        opened=reopen(saved)
        try:
            report['observations'].append(dict(stage='reopen_edit_'+role,value=reading(opened)))
        finally:
            opened.close(False)
    restored=work/'verified_restored.f3d'
    if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(restored))):
        raise RuntimeError('independent restoration save refused')
    doc.close(False)
    doc=None
    doc=reopen(restored)
    report['observations'].append(dict(stage='reopen_restored',value=reading(doc)))
except Exception:
    report['errors'].append(traceback.format_exc())
finally:
    if doc is not None:
        doc.close(False)
    try:
        control=reopen(work/'control_after.f3d')
        try:
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
