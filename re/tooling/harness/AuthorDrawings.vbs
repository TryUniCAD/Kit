Option Explicit
Dim FileSystem, ResearchRoot, OutputRoot, SwApp, DrawingTemplate, PartTemplate
Set FileSystem = CreateObject("Scripting.FileSystemObject")
ResearchRoot = "Z:\Documents\UniCAD\Kit-solidworks-native\.rescratch"
OutputRoot = ResearchRoot & "\drawings"
If Not FileSystem.FolderExists(OutputRoot) Then
    FileSystem.CreateFolder OutputRoot
End If
Set SwApp = CreateObject("SldWorks.Application")
DrawingTemplate = SwApp.GetUserPreferenceStringValue(10)
PartTemplate = ResearchRoot & "\polyline"
WScript.Echo "REVISION=" & SwApp.RevisionNumber() & " DRAWING_TEMPLATE=" & DrawingTemplate
AuthorDrawing "standard", PartTemplate & "\poly5a.SLDPRT", Array("*Front", "*Top", "*Right", "*Isometric"), Array(0.11, 0.23, 0.22, 0.11, 0.11, 0.23, 0.22, 0.23), "Kit five-line pad / standard views"
AuthorDrawing "minimal", PartTemplate & "\poly5deep.SLDPRT", Array("*Front", "*Top"), Array(0.16, 0.16, 0.16, 0.25), "Kit five-line pad / 17 mm"
AuthorDrawing "angled", PartTemplate & "\poly5b.SLDPRT", Array("*Front", "*Left", "*Isometric"), Array(0.12, 0.23, 0.24, 0.23, 0.12, 0.12), "Kit five-line pad / shifted profile"
WScript.Echo "DRAWING_DONE"

Sub AuthorDrawing(Label, PartPath, ViewNames, Locations, NoteText)
    Dim ModelDoc, View, Index, Note, ViewCount, Target
    Set ModelDoc = SwApp.NewDocument(DrawingTemplate, CLng(0), CLng(0), CLng(0))
    If ModelDoc Is Nothing Then
        WScript.Echo "DRAWING_ERROR=" & Label & " new drawing failed"
        Exit Sub
    End If
    Note = Null
    For Index = 0 To UBound(ViewNames)
        Set View = ModelDoc.CreateDrawViewFromModelView3(PartPath, ViewNames(Index), CDbl(Locations(Index * 2)), CDbl(Locations(Index * 2 + 1)), 0.0)
        If View Is Nothing Then
            WScript.Echo "VIEW_ERROR=" & Label & " " & ViewNames(Index)
        Else
            WScript.Echo "VIEW=" & Label & " " & View.Name & " TYPE=" & View.Type & " X=" & Locations(Index * 2) & " Y=" & Locations(Index * 2 + 1)
        End If
    Next
    On Error Resume Next
    Set Note = ModelDoc.InsertNote(NoteText)
    If Err.Number <> 0 Then
        WScript.Echo "NOTE_ERROR=" & Label & " " & Err.Description
        Err.Clear
    ElseIf Not Note Is Nothing Then
        Note.SetPosition 0.06, 0.05, 0.0
    End If
    On Error GoTo 0
    WScript.Echo "REBUILT=" & ModelDoc.ForceRebuild3(False)
    Set View = ModelDoc.GetFirstView
    ViewCount = 0
    Do While Not View Is Nothing
        ViewCount = ViewCount + 1
        WScript.Echo "READ_VIEW=" & Label & " " & View.Name & " TYPE=" & View.Type
        Set View = View.GetNextView
    Loop
    Target = OutputRoot & "\" & Label & ".SLDDRW"
    On Error Resume Next
    Call ModelDoc.SaveAs(Target)
    If Err.Number <> 0 Then
        WScript.Echo "DRAWING_SAVE_ERROR=" & Label & " " & Err.Description
        Err.Clear
    End If
    On Error GoTo 0
    WScript.Echo "DRAWING_SAVED=" & Target & " EXISTS=" & FileSystem.FileExists(Target) & " READ_VIEWS=" & ViewCount
    SwApp.CloseDoc ModelDoc.GetTitle()
End Sub
