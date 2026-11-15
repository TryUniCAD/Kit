# Inspect native view rendering

`re/tooling/sw2026/InspectView.py` accepts a JSON job and report path. Each case
names a copied native part, a fresh BMP destination, a name and its control or
candidate role. The tool starts a visible SOLIDWORKS process, checks the exact
2026 executable, opens and rebuilds the file and records its initial viewport
before changing the view. It then selects an isometric view, zooms to fit and
captures that view separately. Existing destinations are rejected and native
geometry/feature status must be clean before capture.

The report retains stages, native status, geometry, feature tree, image hash and
unchanged-input check. Use original controls around generated candidates.
Capture success does not prove that the viewport contains the expected model;
the images must be inspected separately. Native execution is pending.
