Option Explicit
Dim SwApp, ModelDoc, SketchFeature, Sketch, Segments, BossFeature
If WScript.Arguments.Length <> 1 Then WScript.Quit 64
Set SwApp = CreateObject("SldWorks.Application")
On Error Resume Next
Set ModelDoc = SwApp.OpenDoc(WScript.Arguments(0), 1)
If Err.Number <> 0 Or ModelDoc Is Nothing Then
    WScript.Echo "OPEN_FAILED"
    WScript.Quit 2
End If
Set SketchFeature = ModelDoc.FeatureByName("Sketch1")
If SketchFeature Is Nothing Then
    WScript.Echo "SKETCH_UNAVAILABLE"
Else
    Set Sketch = SketchFeature.GetSpecificFeature2()
    Segments = Sketch.GetSketchSegments()
    WScript.Echo "SKETCH_NAME=" & SketchFeature.Name & " TYPE=" & SketchFeature.GetTypeName2() & " LINE_COUNT=" & UBound(Segments) + 1
End If
Set BossFeature = ModelDoc.FeatureByName("Boss-Extrude1")
If BossFeature Is Nothing Then
    WScript.Echo "BOSS_UNAVAILABLE"
Else
    WScript.Echo "BOSS_NAME=" & BossFeature.Name & " TYPE=" & BossFeature.GetTypeName2()
End If
If Err.Number <> 0 Then
    WScript.Echo "FEATURE_ERROR=" & Err.Description & " HRESULT=" & Hex(Err.Number)
End If
SwApp.CloseDoc ModelDoc.GetTitle()
