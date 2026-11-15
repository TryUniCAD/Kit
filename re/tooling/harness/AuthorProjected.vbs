Option Explicit
Dim SwApp, ModelDoc, BaseView, ProjectedView, Target
Set SwApp = CreateObject("SldWorks.Application")
Set ModelDoc = SwApp.NewDocument(SwApp.GetUserPreferenceStringValue(10), 0, 0, 0)
If ModelDoc Is Nothing Then
    WScript.Echo "DRAWING_ERROR=new drawing failed"
    WScript.Quit 2
End If
Set BaseView = ModelDoc.CreateDrawViewFromModelView3("Z:\Documents\UniCAD\Kit-solidworks-native\.rescratch\polyline\poly5a.SLDPRT", "*Front", 0.10, 0.15, 0.0)
If BaseView Is Nothing Then
    WScript.Echo "BASE_VIEW=None"
    WScript.Quit 3
End If
WScript.Echo "BASE_VIEW=" & BaseView.Name & " TYPE=" & BaseView.Type
Dim Selected
Selected = ModelDoc.Extension.SelectByID2(BaseView.Name, "DRAWINGVIEW", 0, 0, 0, False, 0, Nothing, 0)
WScript.Echo "SELECTED=" & Selected
Set ProjectedView = ModelDoc.CreateUnfoldedViewAt3(0.20, 0.15, 0.0, False)
If ProjectedView Is Nothing Then
    WScript.Echo "PROJECTED_VIEW=None"
Else
    WScript.Echo "PROJECTED_VIEW=" & ProjectedView.Name & " TYPE=" & ProjectedView.Type
End If
WScript.Echo "REBUILT=" & ModelDoc.ForceRebuild3(False)
Target = "Z:\Documents\UniCAD\Kit-solidworks-native\.rescratch\drawings\projected.SLDDRW"
ModelDoc.SaveAs Target
WScript.Echo "SAVED=" & Target
SwApp.CloseDoc ModelDoc.GetTitle()
