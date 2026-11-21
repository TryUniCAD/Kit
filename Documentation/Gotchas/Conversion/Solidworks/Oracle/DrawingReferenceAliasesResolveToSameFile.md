# Drawing reference aliases resolve to the same file

On SOLIDWORKS 2026 SP05.2 the drawing source authoring process reported the part's Parallels UNC path from `IView.GetReferencedModelName`. Fresh reopen reported the mapped drive spelling of the same part. Both front views rebuilt with the expected configuration, placement, outline and child mass properties.

Keep the raw API strings in the private observation record. Verify the loaded `IView.ReferencedDocument.GetPathName` against the canonical expected child path in each phase, then compare the canonical identities and configurations across phases. [First drawing discovery receipt](../../../../../re/solidworks/measurements/2026/DrawingArchiveDiscovery01.json), [Drawing source harness](../../../../../re/tooling/sw2026/AuthorDrawingSources.py)
