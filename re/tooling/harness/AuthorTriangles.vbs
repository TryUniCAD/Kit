Option Explicit
Dim FileSystem, ResearchRoot, OutputRoot
If Not WScript.Arguments.Named.Exists("root") Then WScript.Quit 64
ResearchRoot = WScript.Arguments.Named("root")
Set FileSystem = CreateObject("Scripting.FileSystemObject")
If Not FileSystem.FolderExists(ResearchRoot) Then WScript.Quit 65
OutputRoot = ResearchRoot & "\triangle"
If Not FileSystem.FolderExists(OutputRoot) Then FileSystem.CreateFolder OutputRoot
Dim SwApp, PartTemplate, CaseIndex, RandomCount
Set SwApp = CreateObject("SldWorks.Application")
PartTemplate = SwApp.GetUserPreferenceStringValue(8)
WScript.Echo "SWREV=" & SwApp.RevisionNumber() & " TEMPLATE=" & PartTemplate
If WScript.Arguments.Named.Exists("precise") Then
    AuthorOne SwApp, PartTemplate, "tri3precise", Array(-7.123456789012345, -11.234567890123456, 39.34567890123456, -4.456789012345678, 17.567890123456787, 38.67890123456789), 13.375
    AuthorOne SwApp, PartTemplate, "tri3nearorigin", Array(0.0000000000008, 0.0, 42.0, 0.0, 12.0, 31.0), 9.0
    WScript.Echo "PRECISE_DONE=2"
    WScript.Quit 0
End If
If WScript.Arguments.Named.Exists("random") Then
    RandomCount = CInt(WScript.Arguments.Named("random"))
    If RandomCount < 1 Or RandomCount > 512 Then WScript.Quit 66
    Randomize 982711
    For CaseIndex = 1 To RandomCount
        AuthorOne SwApp, PartTemplate, "tri3r" & Right("000" & CaseIndex, 3), RandomPoints(), Round(3.0 + Rnd() * 47.0, 6)
    Next
    WScript.Echo "RANDOM_DONE=" & RandomCount
    WScript.Quit 0
End If
AuthorOne SwApp, PartTemplate, "tri3a", Array(0.0, 0.0, 42.0, 0.0, 12.0, 31.0), 9.0
AuthorOne SwApp, PartTemplate, "tri3b", Array(-7.0, -11.0, 39.0, -4.0, 17.0, 38.0), 17.0
AuthorOne SwApp, PartTemplate, "tri3deep", Array(0.0, 0.0, 42.0, 0.0, 12.0, 31.0), 21.0
AuthorOne SwApp, PartTemplate, "tri3reverse", Array(12.0, 31.0, 42.0, 0.0, 0.0, 0.0), 9.0
AuthorOne SwApp, PartTemplate, "tri3tie", Array(0.0, 0.0, 36.0, 0.0, 36.0, 24.0), 11.0
WScript.Echo "AUTHOR_DONE"

Function RandomPoints()
    Dim Points(5), Vertex, Angle, Radius, PiValue
    PiValue = 4.0 * Atn(1.0)
    For Vertex = 0 To 2
        Angle = -PiValue + Vertex * 2.0 * PiValue / 3.0 + (Rnd() - 0.5) * 0.5
        Radius = 19.0 + Rnd() * 41.0
        Points(Vertex * 2) = Round(Cos(Angle) * Radius, 6)
        Points(Vertex * 2 + 1) = Round(Sin(Angle) * Radius, 6)
    Next
    RandomPoints = Points
End Function

Sub ReportModel(ModelDoc, Label)
    Dim Bodies, BodyCount, Feature, FeatureName, FeatureType, Properties
    BodyCount = 0
    Bodies = ModelDoc.GetBodies2(0, True)
    If IsArray(Bodies) Then BodyCount = UBound(Bodies) + 1
    WScript.Echo "MODEL=" & Label & " BODIES=" & BodyCount & " REBUILT=" & ModelDoc.ForceRebuild3(False)
    Set Feature = ModelDoc.FirstFeature
    Do While Not Feature Is Nothing
        FeatureName = Feature.Name
        FeatureType = Feature.GetTypeName2()
        WScript.Echo "FEATURE=" & FeatureName & " TYPE=" & FeatureType
        Set Feature = Feature.GetNextFeature()
    Loop
    If BodyCount > 0 Then
        On Error Resume Next
        Set Properties = ModelDoc.Extension.CreateMassProperty()
        If Err.Number <> 0 Then
            WScript.Echo "MASS_EXCEPTION=" & Err.Number & " " & Err.Description
            Err.Clear
        Else
            WScript.Echo "VOLUME_MM3=" & CDbl(Properties.Volume) * 1000000000.0
            WScript.Echo "AREA_MM2=" & CDbl(Properties.SurfaceArea) * 1000000.0
        End If
        On Error GoTo 0
    End If
End Sub

Sub AuthorOne(AppRef, Template, Label, Points, DepthMm)
    If WScript.Arguments.Named.Exists("only") And StrComp(WScript.Arguments.Named("only"), Label, 1) <> 0 Then Exit Sub
    Dim ModelDoc, SketchMgr, Segment, Feature, Index, NextIndex, Selected
    Dim ActiveSketch, SketchSegments, Target, Dimension
    WScript.Echo "AUTHOR_BEGIN=" & Label
    Set ModelDoc = AppRef.NewDocument(Template, CLng(0), CLng(0), CLng(0))
    If ModelDoc Is Nothing Then WScript.Quit 67
    ModelDoc.ClearSelection2 True
    Selected = ModelDoc.Extension.SelectByID2("Front Plane", "PLANE", 0.0, 0.0, 0.0, False, 0, Nothing, 0)
    If Not Selected Then WScript.Quit 68
    ModelDoc.InsertSketch2 True
    Set SketchMgr = ModelDoc.SketchManager
    SketchMgr.AddToDB = True
    SketchMgr.DisplayWhenAdded = False
    For Index = 0 To UBound(Points) - 1 Step 2
        NextIndex = (Index + 2) Mod (UBound(Points) + 1)
        Set Segment = SketchMgr.CreateLine(CDbl(Points(Index)) / 1000.0, CDbl(Points(Index + 1)) / 1000.0, 0.0, CDbl(Points(NextIndex)) / 1000.0, CDbl(Points(NextIndex + 1)) / 1000.0, 0.0)
        If Segment Is Nothing Then WScript.Quit 69
    Next
    Set ActiveSketch = SketchMgr.ActiveSketch
    SketchSegments = ActiveSketch.GetSketchSegments()
    WScript.Echo "SKETCH=" & ActiveSketch.Name & " SEGMENTS=" & UBound(SketchSegments) + 1
    SketchMgr.AddToDB = False
    SketchMgr.DisplayWhenAdded = True
    ModelDoc.InsertSketch2 True
    ModelDoc.ClearSelection2 True
    Selected = ModelDoc.Extension.SelectByID2("Sketch1", "SKETCH", 0.0, 0.0, 0.0, False, CLng(0), Nothing, CLng(0))
    WScript.Echo "SKETCH_SELECTION=" & Selected
    On Error Resume Next
    Set Feature = ModelDoc.FeatureManager.FeatureExtrusion2(True, False, False, CLng(0), CLng(0), CDbl(DepthMm) / 1000.0, 0.0, False, False, False, False, 0.0, 0.0, False, False, False, False, True, True, True, CLng(0), 0.0, False)
    If Err.Number <> 0 Then WScript.Quit 70
    On Error GoTo 0
    If Not IsObject(Feature) Then WScript.Quit 71
    WScript.Echo "EXTRUSION=" & Feature.Name & " TYPE=" & Feature.GetTypeName2()
    ReportModel ModelDoc, Label
    Target = OutputRoot & "\" & Label & ".SLDPRT"
    If FileSystem.FileExists(Target) Then
        WScript.Echo "PREEXISTING_SKIP=" & Target
    Else
        On Error Resume Next
        Call ModelDoc.SaveAs(Target)
        If Err.Number <> 0 Then WScript.Quit 72
        On Error GoTo 0
        WScript.Echo "SAVED=" & Target & " EXISTS=" & FileSystem.FileExists(Target)
    End If
    Set Dimension = ModelDoc.Parameter("D1@Boss-Extrude1")
    WScript.Echo "DEPTH_PARAMETER=" & CDbl(Dimension.SystemValue) * 1000.0
    AppRef.CloseDoc ModelDoc.GetTitle()
    WScript.Echo "AUTHOR_END=" & Label
End Sub
