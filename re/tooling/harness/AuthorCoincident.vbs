Option Explicit
Dim SwApp, ModelDoc, View, Result, Target
Set SwApp = CreateObject("SldWorks.Application")
Set ModelDoc = SwApp.NewDocument(SwApp.GetUserPreferenceStringValue(10), 0, 0, 0)
Set View = ModelDoc.CreateDrawViewFromModelView3("Z:\Documents\UniCAD\Kit-solidworks-native\.rescratch\polyline\poly5a.SLDPRT", "*Front", 0.11, 0.23, 0.0)
WScript.Echo "SHEET1_VIEW=" & View.Name
Result = ModelDoc.NewSheet4("Sheet2", 0, 0, 1.0, 1.0, False, "", 0.2794, 0.2159, "", 0, 0, 0, 0, 0, 0)
WScript.Echo "NEW_SHEET=" & Result
Set View = ModelDoc.CreateDrawViewFromModelView3("Z:\Documents\UniCAD\Kit-solidworks-native\.rescratch\polyline\poly5a.SLDPRT", "*Top", 0.11, 0.23, 0.0)
WScript.Echo "SHEET2_VIEW=" & View.Name
WScript.Echo "REBUILT=" & ModelDoc.ForceRebuild3(False)
Target = "Z:\Documents\UniCAD\Kit-solidworks-native\.rescratch\drawings\coincident.SLDDRW"
ModelDoc.SaveAs Target
WScript.Echo "SAVED=" & Target
SwApp.CloseDoc ModelDoc.GetTitle()
