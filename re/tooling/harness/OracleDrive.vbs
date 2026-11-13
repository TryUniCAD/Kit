Option Explicit
Dim SwApp, ModelDoc, Dimension, Rebuilt, MassProperty, CenterOfMass
If WScript.Arguments.length <> 2 Then
    WScript.Echo "usage: OracleDrive.vbs existing.SLDPRT depth_mm"
    WScript.Quit 64
End If
Set SwApp = CreateObject("SldWorks.Application")
Set ModelDoc = SwApp.OpenDoc(WScript.Arguments(0), 1)
If ModelDoc Is Nothing Then
    WScript.Echo "OPENED=False"
    WScript.Quit 2
End If
On Error Resume Next
Set Dimension = ModelDoc.Parameter("D1@Boss-Extrude1")
If Dimension Is Nothing Then
    WScript.Echo "DIMENSION_UNAVAILABLE"
    SwApp.CloseDoc ModelDoc.GetTitle()
    WScript.Quit 2
End If
Dimension.SystemValue = CDbl(WScript.Arguments(1)) / 1000.0
If Err.Number <> 0 Then
    WScript.Echo "EDIT_ERROR=" & Err.Number & " " & Err.Description & " HRESULT=" & Hex(Err.Number)
    Err.Clear
    SwApp.CloseDoc ModelDoc.GetTitle()
    WScript.Quit 1
End If
Rebuilt = ModelDoc.ForceRebuild3(False)
WScript.Echo "EDITED_REBUILT=" & Rebuilt
WScript.Echo "EDITED_DEPTH_PARAMETER=" & Dimension.SystemValue * 1000.0
Set MassProperty = ModelDoc.Extension.CreateMassProperty()
WScript.Echo "EDITED_VOLUME_MM3=" & CDbl(MassProperty.Volume) * 1000000000.0
WScript.Echo "EDITED_AREA_MM2=" & CDbl(MassProperty.SurfaceArea) * 1000000.0
CenterOfMass = MassProperty.CenterOfMass()
Dim Shell, RawReadExit, MeasureCommand, Quote, OutputPath
Set Shell = CreateObject("WScript.Shell")
Quote = Chr(34)
OutputPath = "Z:\Documents\UniCAD\Kit-solidworks-native\.rescratch\polyline\drive-oracle.txt"
MeasureCommand = Quote & "Z:\Documents\UniCAD\Kit-solidworks-native\.rescratch\OracleMeasure.exe" & Quote
WScript.Echo "RAW_COMMAND=" & MeasureCommand
RawReadExit = Shell.Run(MeasureCommand, 1, True)
WScript.Echo "RAW_READ_EXIT=" & RawReadExit
WScript.Echo "CHANGES_SAVED=False"
SwApp.CloseDoc ModelDoc.GetTitle()
