import json,hashlib
import pythoncom
from win32com.client import VARIANT
import time,traceback
stages=[]
def mark(stage):
 stages.append({'stage':stage,'at':time.time()})
 (work/'Stages.json').write_text(json.dumps(stages,indent=2))
rows=[]
for label,width,height,depth in [('control-before',40,20,10),('variation',40,20,4),('control-after',40,20,10)]:
 mark("template:"+label)
 template=app.GetDocumentTemplate(1,"",0,0,0)
 if not template:raise RuntimeError("GetDocumentTemplate returned no installed part template")
 mark("new-document:"+label)
 doc=app.NewDocument(template,0,0,0)
 if doc is None:raise RuntimeError('default part template unavailable')
 try:
  mark("select-plane:"+label)
  if not doc.Extension.SelectByID2('Top Plane','PLANE',0,0,0,False,0,VARIANT(pythoncom.VT_DISPATCH,None),0):raise RuntimeError('front plane selection failed')
  doc.SketchManager.InsertSketch(True)
  mark("rectangle:"+label)
  doc.SketchManager.CreateCornerRectangle(0,0,0,width/1000,height/1000,0)
  doc.SketchManager.InsertSketch(True)
  mark("extrude:"+label)
  feature=doc.FeatureManager.FeatureExtrusion2(True,False,False,0,0,depth/1000,0,False,False,False,False,0,0,False,False,False,False,True,True,True,0,0,False)
  if feature is None:raise RuntimeError('extrusion failed')
  mark("rebuild:"+label)
  doc.EditRebuild3()
  target=work/(label+'.SLDPRT')
  errors=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_I4,0)
  warnings=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_I4,0)
  mark("save:"+label)
  if not doc.Extension.SaveAs(str(target),0,1,VARIANT(pythoncom.VT_DISPATCH,None),errors,warnings):raise RuntimeError(f'save failed: {errors.value}; warnings: {warnings.value}')
  mark("measure:"+label)
  mass=doc.Extension.CreateMassProperty();center=mass.CenterOfMass
  rows.append({'case':label,'parameters_mm':{'width':width,'height':height,'depth':depth},'volume_m3':mass.Volume,'area_m2':mass.SurfaceArea,'centroid_m':list(center),'sha256':hashlib.sha256(target.read_bytes()).hexdigest()})
 finally:
  mark("close-begin:"+label)
  title=doc.GetTitle
  mark("close:"+label)
  app.CloseDoc(title() if callable(title) else title)
result={'status':'completed','application':'solidworks','cases':rows,'acceptance':'authoring_only; neutral semantic comparison pending'}
(work/'GroundTruth.json').write_text(json.dumps(result,indent=2))
