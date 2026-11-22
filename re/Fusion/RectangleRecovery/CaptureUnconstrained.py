import adsk.core, adsk.fusion, json, hashlib
rows=[]
for label,plane_name,direction_value in [('control-before','xYConstructionPlane',1),('reverse-xy','xYConstructionPlane',-1),('datum-yz','yZConstructionPlane',1),('control-after','xYConstructionPlane',1)]:
 depth=11
 doc=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
 try:
  design=adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
  design.designType=adsk.fusion.DesignTypes.ParametricDesignType
  root=design.rootComponent
  sketch=root.sketches.add(getattr(root,plane_name))
  sketch.sketchCurves.sketchLines.addTwoPointRectangle(adsk.core.Point3D.create(0,0,0),adsk.core.Point3D.create(3.7,2.3,0))
  feature=root.features.extrudeFeatures.addSimple(sketch.profiles.item(0),adsk.core.ValueInput.createByReal(direction_value*depth/10),adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
  feature.name='ControlledBoss'
  if not design.computeAll():raise RuntimeError('rebuild failed')
  target=work/(label+'.f3d')
  if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(target))):raise RuntimeError('export failed')
  body=root.bRepBodies.item(0);mass=body.physicalProperties
  rows.append({'case':label,'parameters_mm':{'width':37,'height':23,'depth':depth},'body_count':root.bRepBodies.count,'volume_cm3':mass.volume,'area_cm2':mass.area,'centroid_cm':[mass.centerOfMass.x,mass.centerOfMass.y,mass.centerOfMass.z],'timeline_count':design.timeline.count,'sketch_constraint_count':sketch.geometricConstraints.count,'sketch_dimension_count':sketch.sketchDimensions.count,'plane_name':plane_name,'direction':direction_value,'sha256':hashlib.sha256(target.read_bytes()).hexdigest()})
 finally:doc.close(False)
result={'status':'completed','application':'fusion','cases':rows,'acceptance':'authoring_only; neutral semantic comparison pending'}
(work/'GroundTruth.json').write_text(json.dumps(result,indent=2))
