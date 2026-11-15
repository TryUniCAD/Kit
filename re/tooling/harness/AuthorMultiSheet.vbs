Option Explicit
Dim SwApp, ModelDoc, View, Note, Target, Result
Set SwApp = CreateObject("SldWorks.Application")
Set ModelDoc = SwApp.NewDocument(SwApp.GetUserPreferenceStringValue(10), 0, 0, 0)
If ModelDoc Is Nothing Then
    WScript.Echo "DRAWING_ERROR=new drawing failed"
    WScript.Quit 2
End If
Set View = ModelDoc.CreateDrawViewFromModelView3("Z:\Documents\UniCAD\Kit-solidworks-native\.rescratch\polyline\poly5a.SLDPRT", "*Front", 0.11, 0.23, 0.0)
WScript.Echo "SHEET1_VIEW=" & View.Name
Result = ModelDoc.NewSheet4("Sheet2", 0, 0, 1.0, 1.0, False, "", 0.2794, 0.2159, "", 0, 0, 0, 0, 0, 0)
WScript.Echo "NEW_SHEET=" & Result
Set View = ModelDoc.CreateDrawViewFromModelView3("Z:\Documents\UniCAD\Kit-solidworks-native\.rescratch\polyline\poly5a.SLDPRT", "*Top", 0.16, 0.16, 0.0)
If View Is Nothing Then
    WScript.Echo "SHEET2_VIEW=None"
Else
    WScript.Echo "SHEET2_VIEW=" & View.Name & " SHEET=" & ModelDoc.GetCurrentSheet.GetName
End If
Set Note = ModelDoc.InsertNote("multi sheet note")
On Error Resume Next
If Not Note Is Nothing Then Note.SetPosition 0.05, 0.04, 0.0
If Err.Number <> 0 Then
    WScript.Echo "NOTE_POSITION_ERROR=" & Err.Description
    Err.Clear
End If
On Error GoTo 0
WScript.Echo "REBUILT=" & ModelDoc.ForceRebuild3(False)
Target = "Z:\Documents\UniCAD\Kit-solidworks-native\.rescratch\drawings\multisheet.SLDDRW"
ModelDoc.SaveAs Target
WScript.Echo "SAVED=" & Target
SwApp.CloseDoc ModelDoc.GetTitle()
