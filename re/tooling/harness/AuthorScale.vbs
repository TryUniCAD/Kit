Option Explicit
Dim SwApp, ModelDoc, View, Target
Set SwApp = CreateObject("SldWorks.Application")
Set ModelDoc = SwApp.NewDocument(SwApp.GetUserPreferenceStringValue(10), 0, 0, 0)
Set View = ModelDoc.CreateDrawViewFromModelView3("Z:\Documents\UniCAD\Kit-solidworks-native\.rescratch\polyline\poly5a.SLDPRT", "*Front", 0.11, 0.23, 0.0)
WScript.Echo "VIEW=" & View.Name
WScript.Echo "USE_SHEET=" & View.UseSheetScale
View.ScaleDecimal = 3.0
WScript.Echo "DECIMAL=" & View.ScaleDecimal
WScript.Echo "REBUILT=" & ModelDoc.ForceRebuild3(False)
Target = "Z:\Documents\UniCAD\Kit-solidworks-native\.rescratch\drawings\scale3.SLDDRW"
ModelDoc.SaveAs Target
WScript.Echo "SAVED=" & Target
SwApp.CloseDoc ModelDoc.GetTitle()
