# Annotation visibility does not override document display masks

Expectation: a note that enumerates with `IAnnotation.Visible=1` and valid display data must appear in the drawing bitmap.

Actual: the disclosed diagnostic has those object-level properties while the document's `swDisplayAnnotations` and `swDisplayAllAnnotations` switches are false. The exact ordinary native getters resolve those switches to separate bit indices zero and 29 in `fad8_0`. The grid switch is independently `fad4` bit zero. Initial blank constructor flags can therefore enable a grid while both annotation display settings remain disabled.

Bind all three actual document settings independently, preserve other preference bits, and keep a real rendered-pixel check. Correct switch readback is itself insufficient to prove wrapper/render registration or that a note was drawn. Do not hide a remaining empty-image failure by reporting COM visibility alone. See [the source and measured state evidence](../../../../../../../re/solidworks/records/DrawingDocumentDisplayFlags2026.md).
