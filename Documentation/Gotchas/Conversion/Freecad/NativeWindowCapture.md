# Widget capture can omit the native OpenGL viewport

Expected behavior: capturing the visible FreeCAD main widget through
`QWidget.grab()` includes its 3D assembly viewport.

Observed behavior: FreeCAD 1.1.4 on macOS produced a valid image containing the
application chrome and document tree, with a blank OpenGL region. The separate
native `activeView().saveImage()` contained the model, so the document was loaded
and the viewport itself was healthy. The widget image was rejected.

Workaround: select and repaint the actual source document subwindow, then capture
the real application window with `window.screen().grabWindow(window.winId())`.
Record the native window id, selected view title and screenshot hash, and inspect
the unedited image. Do not composite a viewport render into a window capture.
The [actual source report](../../../../re/solidworks/measurements/2026/PublicAssembly/FreecadSource.json)
and screenshot record the successful application capture.
