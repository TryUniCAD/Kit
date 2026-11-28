# Read three owned origin axes in a cold SOLIDWORKS part

`open_document(source, source_format="solidworks.sldprt", strict=True)`
returns the three signed principal axes, their ordered plane selections,
and reconstructed signed box geometry for the measured cold F14c part.
Each `PlaneAxis` retains the exact linked feature and selection source
spans. The existing rectangle reader supplies the actual three editable
drivers and named body.

The bounded path requires a named stock from a reversed blind Top-plane
rectangle and three positive visible principal-axis roots with owned
supports, finite stations and matching presentation. The verification
uses two fresh guarded processes, the previous axis-free control and
six separate malformed-owner contrasts. Saved-cache and public writer
qualification keep their own requirements.

[Reader and source ownership details](../../../../../re/solidworks/records/AttachedBoxAxisRead2026.md)
