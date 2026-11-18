# Native verification of a complete SDK drawing pair

A SOLIDWORKS 2026 Front drawing and its part now pass open, rebuild, view
movement, save and fresh reopen entirely from generated SDK files. The
drawing keeps 16 exact feature rows, the part retains its 19 top-level
rows and editable 14.3 mm depth, and the reference resolves to the
expected part on every open.

The unchanged 1:1 scale, new position, outline, model-to-view transform
and child mass properties pass measured comparison. Six native processes
and 602 numerical comparisons pass, including both pristine controls.
The normal layout reader also recovers both positions and the stored link.

Read the [native record](../../../../../../re/solidworks/records/SdkLinkedDrawingNative2026.md)
and [measurement](../../../../../../re/solidworks/measurements/2026/SdkLinkedDrawingNative01.json).
Native qualification of this disclosed pair is separate from held-out
coverage and public writer admission.
