# Standard views need generated orientation records

## Expected

The model can leave its ten standard-view pointers null and the vendor loader
will reconstruct each canonical view from the array index.

## Observed

The generated polygons open, regenerate one solid and pass measured depth edits,
but selecting the standard isometric view still shows their front faces. The
same capture procedure renders the original control's depth in isometric view.
The models are visible; ordinary standard-view selection is wrong.

Native `setDocumentDefaultViews` at `0x4c0352c0` creates ten distinct `moView_c`
records with the indexed constructor. The load fallback for null wire entries
uses the no-argument constructor and writes the view number without replaying
the indexed orientation constructor. Null pointers do not encode those rotations.

The [capture report](../../../../../re/solidworks/measurements/2026/PolygonViewports.json)
retains the exact application identity, input hashes, native statuses and image
hashes. Its reviewed PNGs are format transcodes of the native BMP captures.

## Workaround

Recover each view record's constructor and wire rules, generate the records from
canonical orientations and model data, then repeat native viewport inspection.
Do not copy view objects or saved rotation tables from a vendor document.
This serializer repair remains unfinished.
