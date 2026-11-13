Option Explicit
Dim FileSystem, ResearchRoot, OutputRoot
Set FileSystem = CreateObject("Scripting.FileSystemObject")
ResearchRoot = "Z:\Documents\UniCAD\Kit-solidworks-native\.rescratch"
OutputRoot = ResearchRoot & "\polyline"
If Not FileSystem.FolderExists(ResearchRoot) Then
    FileSystem.CreateFolder ResearchRoot
End If
If Not FileSystem.FolderExists(OutputRoot) Then
    FileSystem.CreateFolder OutputRoot
End If
Dim SwApp, PartTemplate, PreviousDoc, CaseIndex, RandomCount
Set SwApp = CreateObject("SldWorks.Application")
PartTemplate = SwApp.GetUserPreferenceStringValue(8)
WScript.Echo "SWREV=" & SwApp.RevisionNumber() & " TEMPLATE=" & PartTemplate
If WScript.Arguments.Named.Exists("recover") Then
    Set PreviousDoc = SwApp.ActiveDoc
    If Not PreviousDoc Is Nothing Then
        WScript.Echo "RECOVERY_CLOSE=" & PreviousDoc.GetTitle()
        SwApp.CloseDoc PreviousDoc.GetTitle()
    End If
End If
If WScript.Arguments.Named.Exists("random") Then
    RandomCount = CInt(WScript.Arguments.Named("random"))
    If RandomCount < 1 Or RandomCount > 512 Then WScript.Quit 65
    Randomize 482711
    For CaseIndex = 1 To RandomCount
        AuthorOne SwApp, PartTemplate, "poly5r" & Right("00" & CaseIndex, 3), RandomPoints(), Round(3.0 + Rnd() * 47.0, 6)
    Next
    WScript.Echo "RANDOM_DONE=" & RandomCount
    WScript.Quit 0
End If
AuthorOne SwApp, PartTemplate, "poly5a", Array(0.0, 0.0, 35.0, 0.0, 42.0, 17.0, 19.0, 32.0, -5.0, 14.0), 9.0
AuthorOne SwApp, PartTemplate, "poly5b", Array(5.0, -10.0, 45.0, -5.0, 35.0, 25.0, 12.0, 37.0, -8.0, 12.0), 13.0
AuthorOne SwApp, PartTemplate, "poly5deep", Array(0.0, 0.0, 35.0, 0.0, 42.0, 17.0, 19.0, 32.0, -5.0, 14.0), 17.0
AuthorOne SwApp, PartTemplate, "poly5reverse", Array(-5.0, 14.0, 19.0, 32.0, 42.0, 17.0, 35.0, 0.0, 0.0, 0.0), 9.0
WScript.Echo "AUTHOR_DONE"

Function RandomPoints()
    Dim Points(9), Vertex, Angle, Radius, PiValue
    PiValue = 4.0 * Atn(1.0)
    For Vertex = 0 To 4
        Angle = -PiValue + Vertex * 2.0 * PiValue / 5.0 + (Rnd() - 0.5) * 0.5
        Radius = 24.0 + Rnd() * 31.0
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
    Else
        WScript.Echo "MASS=" & Label & " SKIPPED_NO_BODIES"
    End If
End Sub

Sub AuthorOne(AppRef, Template, Label, Points, DepthMm)
    If WScript.Arguments.Named.Exists("only") And StrComp(WScript.Arguments.Named("only"), Label, 1) <> 0 Then
        Exit Sub
    End If
    Dim ModelDoc, SketchMgr, Segment, Feature, Index, NextIndex, Selected
    Dim ActiveSketch, SketchSegments
    Dim Target, Saved, Dimension
    WScript.Echo "AUTHOR_BEGIN=" & Label
    Set ModelDoc = AppRef.NewDocument(Template, CLng(0), CLng(0), CLng(0))
    If ModelDoc Is Nothing Then
        WScript.Echo "AUTHOR_ERROR=" & Label & " new document failed"
        Exit Sub
    End If
    ModelDoc.ClearSelection2 True
    Selected = ModelDoc.Extension.SelectByID2("Front Plane", "PLANE", 0.0, 0.0, 0.0, False, 0, Nothing, 0)
    If Not Selected Then
        WScript.Echo "AUTHOR_ERROR=" & Label & " front plane selection failed"
        AppRef.CloseDoc ModelDoc.GetTitle()
        Exit Sub
    End If
    ModelDoc.InsertSketch2 True
    Set SketchMgr = ModelDoc.SketchManager
    SketchMgr.AddToDB = True
    SketchMgr.DisplayWhenAdded = False
    For Index = 0 To UBound(Points) - 1 Step 2
        NextIndex = (Index + 2) Mod (UBound(Points) + 1)
        Set Segment = SketchMgr.CreateLine(CDbl(Points(Index)) / 1000.0, CDbl(Points(Index + 1)) / 1000.0, 0.0, CDbl(Points(NextIndex)) / 1000.0, CDbl(Points(NextIndex + 1)) / 1000.0, 0.0)
        If Segment Is Nothing Then
            WScript.Echo "AUTHOR_ERROR=" & Label & " line failed at index " & Index
        End If
    Next
    Set ActiveSketch = SketchMgr.ActiveSketch
    If ActiveSketch Is Nothing Then
        WScript.Echo "SKETCH_DIAGNOSTIC=NO_ACTIVE_SKETCH"
    Else
        WScript.Echo "SKETCH_DIAGNOSTIC=ACTIVE " & ActiveSketch.Name
        SketchSegments = ActiveSketch.GetSketchSegments()
        If IsArray(SketchSegments) Then
            WScript.Echo "SKETCH_SEGMENTS=" & UBound(SketchSegments) + 1
        Else
            WScript.Echo "SKETCH_SEGMENTS=UNAVAILABLE"
        End If
    End If
    SketchMgr.AddToDB = False
    SketchMgr.DisplayWhenAdded = True
    ModelDoc.InsertSketch2 True
    ModelDoc.ClearSelection2 True
    Selected = ModelDoc.Extension.SelectByID2("Sketch1", "SKETCH", 0.0, 0.0, 0.0, False, CLng(0), Nothing, CLng(0))
    WScript.Echo "SKETCH_SELECTION=" & Selected
    On Error Resume Next
    Set Feature = Nothing
    Set Feature = ModelDoc.FeatureManager.FeatureExtrusion2(True, False, False, CLng(0), CLng(0), CDbl(DepthMm) / 1000.0, 0.0, False, False, False, False, 0.0, 0.0, False, False, False, False, True, True, True, CLng(0), 0.0, False)
    If Err.Number <> 0 Then
        WScript.Echo "EXTRUSION_EXCEPTION=" & Err.Number & " " & Err.Description
        Err.Clear
    End If
    On Error GoTo 0
    If Not IsObject(Feature) Then
        WScript.Echo "AUTHOR_ERROR=" & Label & " extrusion returned no feature"
    ElseIf Feature Is Nothing Then
        WScript.Echo "AUTHOR_ERROR=" & Label & " extrusion failed"
    Else
        WScript.Echo "EXTRUSION=" & Feature.Name & " TYPE=" & Feature.GetTypeName2()
    End If
    ReportModel ModelDoc, Label
    Target = OutputRoot & "\" & Label & ".SLDPRT"
    On Error Resume Next
    Call ModelDoc.SaveAs(Target)
    If Err.Number <> 0 Then
        WScript.Echo "SAVEAS_EXCEPTION=" & Err.Number & " " & Err.Description
        Err.Clear
    End If
    Saved = FileSystem.FileExists(Target)
    On Error GoTo 0
    WScript.Echo "SAVED=" & Target & " RESULT=" & Saved & " EXISTS=" & FileSystem.FileExists(Target)
    On Error Resume Next
    Set Dimension = ModelDoc.Parameter("D1@Boss-Extrude1")
    If Dimension Is Nothing Then
        WScript.Echo "DEPTH_PARAMETER=UNAVAILABLE"
    Else
        WScript.Echo "DEPTH_PARAMETER=" & CDbl(Dimension.SystemValue) * 1000.0
    End If
    On Error GoTo 0
    AppRef.CloseDoc ModelDoc.GetTitle()
    WScript.Echo "AUTHOR_END=" & Label
End Sub
