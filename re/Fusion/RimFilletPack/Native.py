import adsk.core, adsk.fusion, json, traceback, hashlib

def measure(design):
 c=design.rootComponent
 bodies=[]
 for b in c.bRepBodies:
  p=b.physicalProperties
  bodies.append(dict(solid=b.isSolid,volume_cm3=p.volume,area_cm2=p.area,centroid_cm=p.centerOfMass.asArray(),min_cm=b.boundingBox.minPoint.asArray(),max_cm=b.boundingBox.maxPoint.asArray(),faces=b.faces.count,edges=b.edges.count,vertices=b.vertices.count))
 return dict(bodies=bodies,timeline=[dict(name=t.name,health=t.healthState,message=t.errorOrWarningMessage) for t in design.timeline],parameters=[dict(name=p.name,expression=p.expression,value=p.value,unit=p.unit) for p in design.allParameters])

def create(radius,height,fillet):
 doc=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
 owned.append(doc)
 design=adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
 design.designType=adsk.fusion.DesignTypes.ParametricDesignType
 c=design.rootComponent
 s=c.sketches.add(c.xYConstructionPlane)
 s.name='Disc sketch'
 s.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(0,0,0),radius/10)
 e=c.features.extrudeFeatures.addSimple(s.profiles.item(0),adsk.core.ValueInput.createByString(str(height)+' mm'),adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
 e.name='Disc extrude'
 if fillet:
  edges=adsk.core.ObjectCollection.create()
  for edge in e.bodies.item(0).edges:
   if abs(edge.boundingBox.minPoint.z-height/10)<1e-7 and abs(edge.boundingBox.maxPoint.z-height/10)<1e-7:edges.add(edge)
  if edges.count!=1:raise RuntimeError('top circular rim selection is not unique')
  inp=c.features.filletFeatures.createInput()
  inp.edgeSetInputs.addConstantRadiusEdgeSet(edges,adsk.core.ValueInput.createByString(str(fillet)+' mm'),True)
  c.features.filletFeatures.add(inp).name='Rim round'
 if not design.computeAll():raise RuntimeError('native build failed')
 return doc,design

owned=[]
original=app.activeDocument
result=dict(case=CASE,mode=MODE,version=app.version,documents_before=app.documents.count,status='started')
try:
 control,cd=create(10.3,21.7,0)
 result['control_before']=measure(cd)
 control.close(False)
 if MODE=='author':doc,design=create(CASE['radius_mm'],CASE['height_mm'],CASE['fillet_mm'])
 else:
  opts=app.importManager.createFusionArchiveImportOptions(str(work/'source.f3d'))
  doc=app.importManager.importToNewDocument(opts)
  if doc is None:raise RuntimeError('candidate native open failed')
  owned.append(doc)
  design=adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
  if not design.computeAll():raise RuntimeError('opened file rebuild failed')
 result['initial']=measure(design)
 c=design.rootComponent
 if c.features.filletFeatures.count!=1:raise RuntimeError('expected one editable fillet feature')
 parameter=c.features.filletFeatures.item(0).edgeSets.item(0).radius
 old=parameter.expression
 result['driving_expression']=old
 parameter.expression=str(CASE['fillet_mm']*0.8)+' mm'
 if not design.computeAll():raise RuntimeError('fillet driving edit failed')
 result['edited']=measure(design)
 parameter.expression=old
 if not design.computeAll():raise RuntimeError('fillet restore failed')
 result['restored']=measure(design)
 path=work/'Restored.f3d'
 if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(path))):raise RuntimeError('archive export failed')
 result['file']=path.name
 result['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
 doc.close(False)
 control,cd=create(10.3,21.7,0)
 result['control_after']=measure(cd)
 control.close(False)
 result['status']='measured'
except Exception:
 result['status']='failed'
 result['traceback']=traceback.format_exc()
finally:
 if 'control_after' not in result:
  try:
   control,cd=create(10.3,21.7,0)
   result['control_after']=measure(cd)
   control.close(False)
  except Exception:result['control_after_error']=traceback.format_exc()
 for doc in reversed(owned):
  if doc.isValid:doc.close(False)
 if original is not None and original.isValid:original.activate()
 result['documents_after']=app.documents.count
 (work/'Measurements.json').write_text(json.dumps(result,indent=2))
