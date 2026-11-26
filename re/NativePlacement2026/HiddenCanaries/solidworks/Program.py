app.UserControlBackground=True
app.Visible=False
import json,hashlib
import pythoncom
from win32com.client import VARIANT
rows=[]
for label,width,height,depth in [('control-before',17.3,11.7,5.1),('variation',19.7,11.7,5.1),('control-after',17.3,11.7,5.1)]:
 template=app.GetDocumentTemplate(1,"",0,0,0)
 if not template:raise RuntimeError("GetDocumentTemplate returned no installed part template")
 doc=app.NewDocument(template,0,0,0)
 if doc is None:raise RuntimeError('default part template unavailable')
 try:
  if not doc.Extension.SelectByID2('Front Plane','PLANE',0,0,0,False,0,VARIANT(pythoncom.VT_DISPATCH,None),0):raise RuntimeError('front plane selection failed')
  doc.SketchManager.InsertSketch(True)
  doc.SketchManager.CreateCornerRectangle(0,0,0,width/1000,height/1000,0)
  doc.SketchManager.InsertSketch(True)
  feature=doc.FeatureManager.FeatureExtrusion2(True,False,False,0,0,depth/1000,0,False,False,False,False,0,0,False,False,False,False,True,True,True,0,0,False)
  if feature is None:raise RuntimeError('extrusion failed')
  doc.EditRebuild3()
  target=work/(label+'.SLDPRT')
  errors=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_I4,0)
  warnings=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_I4,0)
  if not doc.Extension.SaveAs(str(target),0,1,VARIANT(pythoncom.VT_DISPATCH,None),errors,warnings):raise RuntimeError(f'save failed: {errors.value}; warnings: {warnings.value}')
  mass=doc.Extension.CreateMassProperty();center=mass.CenterOfMass
  rows.append({'case':label,'parameters_mm':{'width':width,'height':height,'depth':depth},'volume_m3':mass.Volume,'area_m2':mass.SurfaceArea,'centroid_m':list(center),'sha256':hashlib.sha256(target.read_bytes()).hexdigest()})
 finally:
  title=doc.GetTitle
  app.CloseDoc(title() if callable(title) else title)
result={'status':'completed','application':'solidworks','cases':rows,'acceptance':'authoring_only; neutral semantic comparison pending'}
(work/'GroundTruth.json').write_text(json.dumps(result,indent=2))

import ctypes,os,time
from ctypes import wintypes
owner=app.GetProcessID
owner=owner() if callable(owner) else owner
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
