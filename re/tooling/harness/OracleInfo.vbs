Option Explicit
Dim SwApp
Set SwApp = CreateObject("SldWorks.Application")
WScript.Echo "SWREV=" & SwApp.RevisionNumber()
WScript.Echo "SWVISIBLE=" & SwApp.Visible
WScript.Echo "SWDOCS=" & SwApp.GetDocumentCount()
