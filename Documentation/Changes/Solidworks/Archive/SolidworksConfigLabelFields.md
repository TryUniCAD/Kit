# SOLIDWORKS configuration label fields

The internal version-19000 body reader has layouts for embedded label definitions in
the ordinary part detail profile. It preserves five concrete label types,
their shared base, text, character formats, and label widths.

The enclosing archive supplies the current condition flags. The reader
uses the signed label layer selector with those flags. An active layer
object requires separate ownership evidence, so this profile rejects
that case before consuming its tag.

The guarded process replay matched two complete tracked label bodies
and three independently authored condition cases. It verified nine
refusals, exact child boundaries, and stable map ownership.
[Field record](../../../../re/solidworks/records/ConfigLabelSlice2026.md)
[Reader measurement](../../../../re/solidworks/measurements/2026/ConfigLabelReader01.json)
