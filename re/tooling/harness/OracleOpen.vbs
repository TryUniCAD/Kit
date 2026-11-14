Option Explicit
Dim SwApp, ModelDoc, Rebuilt, Bodies, BodyCount
If WScript.Arguments.length <> 1 Then
    WScript.Echo "usage: OracleOpen.vbs existing.SLDPRT"
    WScript.Quit 64
End If
Set SwApp = CreateObject("SldWorks.Application")
Set ModelDoc = SwApp.OpenDoc(WScript.Arguments(0), 1)
If ModelDoc Is Nothing Then
    WScript.Echo "OPENED=False"
    WScript.Quit 2
End If
Rebuilt = ModelDoc.ForceRebuild3(False)
Bodies = ModelDoc.GetBodies2(0, True)
BodyCount = 0
If IsArray(Bodies) Then BodyCount = UBound(Bodies) + 1
WScript.Echo "OPENED=True REBUILT=" & Rebuilt & " BODIES=" & BodyCount & " TITLE=" & ModelDoc.GetTitle()
SwApp.CloseDoc ModelDoc.GetTitle()
