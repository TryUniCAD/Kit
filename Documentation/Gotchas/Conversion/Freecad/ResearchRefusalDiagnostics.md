# Stale inline edits can raise the FreeCAD adapter exception

On ForwardFrontEdited.FCStd, native LengthFwd differs from the inline manifest. The CLI formerly let the adapter exception escape, so the research runner received a traceback and failed while parsing JSON. The CLI error handler now serializes the adapter exception. Preserve that refusal and inspect the archive or recorded native control for further evidence.
