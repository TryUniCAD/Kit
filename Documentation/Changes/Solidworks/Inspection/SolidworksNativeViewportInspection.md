# Inspect native view rendering

`re/tooling/sw2026/InspectView.py` accepts a JSON job and report path. Each case
names a copied native part, a fresh BMP destination, a name and its control or
candidate role. The tool starts a visible SOLIDWORKS process, checks the exact
2026 executable, opens and rebuilds the file, selects an isometric view, zooms to
fit and asks the application to save its current viewport.

The report retains stages, native status, geometry, feature tree, image hash and
unchanged-input check. Use original controls around generated candidates.
Capture success does not prove that the viewport contains the expected model;
the images must be inspected separately. Native execution is pending.
