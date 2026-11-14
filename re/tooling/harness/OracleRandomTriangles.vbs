Option Explicit
Dim FileSystem, ResearchRoot, ExpectationPath, ExpectationFile, SwApp
Dim TotalCount, PassCount
If Not WScript.Arguments.Named.Exists("root") Then WScript.Quit 64
If Not WScript.Arguments.Named.Exists("expectations") Then WScript.Quit 64
ResearchRoot = WScript.Arguments.Named("root")
ExpectationPath = WScript.Arguments.Named("expectations")
Set FileSystem = CreateObject("Scripting.FileSystemObject")
If Not FileSystem.FolderExists(ResearchRoot) Then WScript.Quit 65
If Not FileSystem.FileExists(ExpectationPath) Then WScript.Quit 65
Set ExpectationFile = FileSystem.OpenTextFile(ExpectationPath, 1)
Set SwApp = CreateObject("SldWorks.Application")
TotalCount = 0
PassCount = 0

Do While Not ExpectationFile.AtEndOfStream
    Dim Fields, ModelDoc, InputPath, LoadErrors, LoadWarnings, Rebuilt, OpenFailed
    Dim Bodies, BodyCount, SketchFeature, Sketch, Segments, LineCount
    Dim BossFeature, SketchType, BossType, CasePass, ErrorText, ErrorNumber
    Fields = Split(ExpectationFile.ReadLine, vbTab)
    If UBound(Fields) <> 7 Then WScript.Quit 66
    TotalCount = TotalCount + 1
    InputPath = ResearchRoot & "\" & Fields(7)
    Err.Clear
    On Error Resume Next
    Set ModelDoc = SwApp.OpenDoc(InputPath, CLng(1))
    ErrorNumber = Err.Number
    ErrorText = Err.Description
    OpenFailed = ErrorNumber <> 0
    On Error GoTo 0
    If Not OpenFailed And Not IsObject(ModelDoc) Then OpenFailed = True
    If Not OpenFailed Then
        If ModelDoc Is Nothing Then OpenFailed = True
    End If
    If OpenFailed Then
        WScript.Echo "ORACLE_CASE=" & Fields(0) & " PASS=False OPEN_ERROR=" & ErrorNumber & " " & ErrorText
        WScript.Quit 2
    End If
    BodyCount = 0
    LineCount = 0
    CasePass = True
    Err.Clear
    On Error Resume Next
    Rebuilt = ModelDoc.ForceRebuild3(False)
    Bodies = ModelDoc.GetBodies2(0, True)
    If IsArray(Bodies) Then BodyCount = UBound(Bodies) + 1
    Set SketchFeature = ModelDoc.FeatureByName("Sketch1")
    Set Sketch = SketchFeature.GetSpecificFeature2()
    Segments = Sketch.GetSketchSegments()
    LineCount = UBound(Segments) + 1
    SketchType = SketchFeature.GetTypeName2()
    Set BossFeature = ModelDoc.FeatureByName("Boss-Extrude1")
    BossType = BossFeature.GetTypeName2()
    ErrorNumber = Err.Number
    ErrorText = Err.Description
    On Error GoTo 0
    If ErrorNumber <> 0 Then CasePass = False
    If Not Rebuilt Or BodyCount <> 1 Then CasePass = False
    If LineCount <> 3 Or SketchType <> "ProfileFeature" Then CasePass = False
    If BossType <> "Extrusion" Then CasePass = False
    WScript.Echo "ORACLE_CASE=" & Fields(0) & " PASS=" & CasePass & " OPEN_METHOD=OpenDoc REBUILT=" & Rebuilt & " BODIES=" & BodyCount & " LINES=" & LineCount & " SKETCH=" & SketchType & " BOSS=" & BossType & " ERROR_NUMBER=" & ErrorNumber & " ERROR_TEXT=" & ErrorText
    SwApp.CloseDoc ModelDoc.GetTitle()
    If Not CasePass Then WScript.Quit 3
    PassCount = PassCount + 1
Loop
ExpectationFile.Close()
WScript.Echo "ORACLE_TOTAL=" & TotalCount & " ORACLE_PASS=" & PassCount
If TotalCount <> 64 Or PassCount <> 64 Then WScript.Quit 4
