import adsk.core, adsk.fusion, json, hashlib
rows=[]
for label,width,height,depth in [('control-before',17.3,11.7,5.1),('variation',19.7,11.7,5.1),('control-after',17.3,11.7,5.1)]:
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

import ctypes,os,time
from ctypes import wintypes
owner=os.getpid()
user32=ctypes.WinDLL('user32',use_last_error=True)
user32.GetWindowThreadProcessId.argtypes=[wintypes.HWND,ctypes.POINTER(wintypes.DWORD)]
user32.IsWindowVisible.argtypes=[wintypes.HWND]
callback_type=ctypes.WINFUNCTYPE(wintypes.BOOL,wintypes.HWND,wintypes.LPARAM)
visible=[]
def check_window(window,parameter):
 pid=wintypes.DWORD();user32.GetWindowThreadProcessId(window,ctypes.byref(pid))
 if pid.value==owner and user32.IsWindowVisible(window):visible.append(int(window))
 return True
callback=callback_type(check_window)
user32.EnumWindows.argtypes=[callback_type,wintypes.LPARAM]
time.sleep(0.4);user32.EnumWindows(callback,0)
result['hidden_window_probe']={'owned_pid':owner,'visible_owned_windows':len(visible),'geometry_controls_retained':True}
(work/'HiddenCanary.json').write_text(json.dumps(result,indent=2))
if visible:raise RuntimeError('automation-owned windows remained visible')
