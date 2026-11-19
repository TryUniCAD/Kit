# Sheet last orientation owns pan and zoom

The drawing sheet's last orientation is an optional pan and zoom transform, despite its name. SOLIDWORKS copies it into the view pan/zoom transform during sheet activation. An absent pointer makes the getter return false. The nearby border-profile field owns unrelated sketch data.

Read and construct the distinct sheet and active-document view fields from the actual planar camera intent. Check viewport rendering separately when qualifying a drawing.

[Native source and construction evidence](../../../../../../re/solidworks/records/DrawingLastSheetViewport2026.md)
