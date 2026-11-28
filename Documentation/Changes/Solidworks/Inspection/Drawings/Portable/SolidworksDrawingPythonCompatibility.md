# Portable drawing API compatibility

The Python compatibility checks cover the four public drawing models and the additive `CadDocument.drawing` field. They verify the exact top-level and document facade exports, dataclass names and field order, positional matching, and serialization type registration.

The four earlier failures reproduced against the published PR revision `35be78dec`, whose compatibility fixtures still held the pre-drawing export and field lists. The updated checks exercise both the drawing additions and the existing exact contracts.
