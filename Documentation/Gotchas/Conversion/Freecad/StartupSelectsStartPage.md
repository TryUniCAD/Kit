# Startup can select Start after the source document opens

Expected behavior: opening a native document and fitting its active 3D view
means a later whole-window screenshot shows that model.

Observed behavior: the first FreeCAD 1.1.4 public-source capture showed the
correct document tree but the startup welcome page covered the central area.
The source document and its native geometry existed. Startup selected the
separate Start view after the macro's initial view commands. The rejected image
has SHA-256 `f087b76758db7a6741afe6f2b15bb29807848d0bf46b59294a8abc56803dd185`.

Workaround: after startup settles, select the source document's existing
`QMdiSubWindow` by its observed title, fit that native view, allow a repaint,
and then capture the application window. Record the selected title and inspect
the actual image. Document-open and geometry observations alone do not verify
the visible state. Keep the rejected image as setup evidence, not acceptance.
