# Native FreeCAD research runs

The automatic input route recognizes a native FreeCAD document by its archive content, runs the existing strict reader and attempts partial reading after a refusal. The research report preserves the neutral document and its timeline when available, archive member structure and unassigned byte ranges. It compares recovered parameter IDs, owners, values, units and expression dependencies against the repository's saved-control expectations only for the same SHA-256.

Use `kit run --root . auto --input model.FCStd --directory /tmp/freecad-research`. Inspect Input-strict.json, Input-raw-structure.json and, for a recorded case, Input-saved-control.json. Recipe execution for native FreeCAD features and whole-file verification remain open.

The AliasEdited and AliasEqual single-input runs each returned four exact parameter matches, including separate expression targets for equal-valued depths. A stale inline extrusion edit can raise the adapter's own error. The CLI emits this refusal as a JSON diagnostic so the research runner can retain the unsupported field and continue its package inspection.
