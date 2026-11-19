# Owner repair uses the pointer array count

Ordinary SOLIDWORKS 2026 partition loading repairs absent `FACE_ID_2001` runtime owners from integer field 3 using repair 1 and refresh 0. An absent pointer-values node has zero elements and can enter reconstruction. A one-element null array has positive count and skips replacement.

Keep the nontransmitted pointer-values link absent in the cold representation and retain the actual integer mirror. Let the body-model attach and load repair reconstruct the owner at runtime. [Exact caller and repair loop](../../../../../../re/solidworks/records/DownstreamPartOwnerReload2026.md)
