# Optional sheet fields can change reconstructed intent

The strict blank drawing reader serializes nested typed source intent under `solidworks.blank.intent`. An older export has no `notes` key in its sheet mapping. Requiring every field in the current class would reject that older export even when the sheet reconstructs the exact original file.

The reader omits fields marked for null omission. The rewrite decoder restores only an omitted field declared with that marker and a default of `None`. It verifies the complete reconstructed source and rejects unknown mapping fields and nonempty note content. The command test exercises older neutral metadata with the field absent and with an explicit null. [Canonical rewrite behavior and evidence](../../../../../../Changes/Solidworks/Inspection/Drawings/Portable/SolidworksCanonicalBlankRewriteIntegration.md)
