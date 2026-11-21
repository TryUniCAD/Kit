# FreeCAD fallback body IDs are local to each source

Two independently saved baked parts and one live `Part::Box` decoded with the same local `freecad:feature:Specimen`, `freecad:body:default` and typed B-rep body IDs. Each archive had a different physical document UUID, source digest and Shape digest. The reader derives the fallback design body because a standalone feature has no native `PartDesign::Body` record.

Bind an imported solid to its full source identity and the actual feature-to-Shape chain. Preserve the document's source digest, physical element owner and local body binding together during verification. [Disclosed owner evidence](../../../Changes/Freecad/FreeCadBakedSourceOwnerAudit.md) · [Neutral body construction](../../../../src/convert/adapters/freecad/Native.py)
