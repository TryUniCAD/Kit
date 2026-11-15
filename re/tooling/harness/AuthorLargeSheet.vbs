Option Explicit
Dim SwApp, ModelDoc, View, Result, Target
Set SwApp = CreateObject("SldWorks.Application")
Set ModelDoc = SwApp.NewDocument(SwApp.GetUserPreferenceStringValue(10), 0, 0, 0)
If ModelDoc Is Nothing Then
    WScript.Echo "DRAWING_ERROR=new drawing failed"
    WScript.Quit 2
End If
Result = ModelDoc.SetupSheet6("Sheet1", 12, 0, 1.0, 1.0, False, "", 1.189, 0.841, "", False, 0, 0, 0, 0, 0, 0)
WScript.Echo "SETUP_SHEET=" & Result
Set View = ModelDoc.CreateDrawViewFromModelView3("Z:\Documents\UniCAD\Kit-solidworks-native\.rescratch\polyline\poly5a.SLDPRT", "*Front", 1.10, 0.40, 0.0)
If View Is Nothing Then
    WScript.Echo "VIEW=None"
Else
    WScript.Echo "VIEW=" & View.Name & " TYPE=" & View.Type
End If
WScript.Echo "REBUILT=" & ModelDoc.ForceRebuild3(False)
Target = "Z:\Documents\UniCAD\Kit-solidworks-native\.rescratch\drawings\large.SLDDRW"
ModelDoc.SaveAs Target
WScript.Echo "SAVED=" & Target
SwApp.CloseDoc ModelDoc.GetTitle()
