import adsk.core, adsk.fusion, json, hashlib
rows=[]
for label,width,height,depth in [('control-before',40,20,10),('variation',73.1,20,10),('control-after',40,20,10)]:
 doc=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
 try:
  design=adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
  design.designType=adsk.fusion.DesignTypes.ParametricDesignType
  root=design.rootComponent
  sketch=root.sketches.add(root.xYConstructionPlane)
  sketch.sketchCurves.sketchLines.addTwoPointRectangle(adsk.core.Point3D.create(0,0,0),adsk.core.Point3D.create(width/10,height/10,0))
  feature=root.features.extrudeFeatures.addSimple(sketch.profiles.item(0),adsk.core.ValueInput.createByReal(1*depth/10),adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
  feature.name='ControlledBoss'
  if not design.computeAll():raise RuntimeError('rebuild failed')
  target=work/(label+'.f3d')
  if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(target))):raise RuntimeError('export failed')
  body=root.bRepBodies.item(0);mass=body.physicalProperties
  rows.append({'case':label,'parameters_mm':{'width':width,'height':height,'depth':depth},'body_count':root.bRepBodies.count,'volume_cm3':mass.volume,'area_cm2':mass.area,'centroid_cm':[mass.centerOfMass.x,mass.centerOfMass.y,mass.centerOfMass.z],'timeline_count':design.timeline.count,'sha256':hashlib.sha256(target.read_bytes()).hexdigest()})
 finally:doc.close(False)
result={'status':'completed','application':'fusion','cases':rows,'acceptance':'authoring_only; neutral semantic comparison pending'}
(work/'GroundTruth.json').write_text(json.dumps(result,indent=2))
