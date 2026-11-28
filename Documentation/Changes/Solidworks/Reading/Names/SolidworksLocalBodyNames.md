# SOLIDWORKS local imported-body names

With B-rep enabled, `convert.open_document` can bind the single planar local
solid of an ordinary SOLIDWORKS 2026 SP05.2 BaseBody part to its design body.
The active configuration, stored LocalBodies group, resolved feature, and
managed atom must agree. The reader publishes the label on the design body
and its identity in `BrepBody.design_body_id`.

A derived name follows the stored feature key and any agreeing kernel UTF-16
name. An explicitly named body follows its Unicode atom and agreeing kernel
name. Check `metadata["solidworks.native_body_names"]` for the native owner.

Eleven disclosed parts retained identical feature timelines and B-rep geometry
apart from the new body binding. The original, feature-only rename, Unicode
body rename, generated parts, and native saves passed. This profile covers one
closed planar local solid with linear edges and a body-free active partition.
[Readback evidence](../../../../../re/solidworks/records/SdkImportedLocalBodyNames2026.md)
