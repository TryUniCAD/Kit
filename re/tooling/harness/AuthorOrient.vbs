Option Explicit
Dim SwApp, ModelDoc, View, Target, Orient, Suffix
If WScript.Arguments.length <> 2 Then WScript.Quit 64
Orient = WScript.Arguments(0)
Suffix = WScript.Arguments(1)
Set SwApp = CreateObject("SldWorks.Application")
Set ModelDoc = SwApp.NewDocument(SwApp.GetUserPreferenceStringValue(10), 0, 0, 0)
If ModelDoc Is Nothing Then
    WScript.Echo "DRAWING_ERROR=new drawing failed"
    WScript.Quit 2
End If
Set View = ModelDoc.CreateDrawViewFromModelView3("Z:\Documents\UniCAD\Kit-solidworks-native\.rescratch\polyline\poly5a.SLDPRT", Orient, 0.11, 0.23, 0.0)
If View Is Nothing Then
    WScript.Echo "VIEW=None"
    WScript.Quit 3
End If
WScript.Echo "VIEW=" & View.Name & " TYPE=" & View.Type
WScript.Echo "REBUILT=" & ModelDoc.ForceRebuild3(False)
Target = "Z:\Documents\UniCAD\Kit-solidworks-native\.rescratch\drawings\orient-" & Suffix & ".SLDDRW"
ModelDoc.SaveAs Target
WScript.Echo "SAVED=" & Target
SwApp.CloseDoc ModelDoc.GetTitle()
