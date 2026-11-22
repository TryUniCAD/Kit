# Local scaffold uses the native plane type

The KeyWords reader projects a native `Feature Type="moRefPlane_c"`
to portable kind `Plane`. It keeps the actual XML type. Some resolved plane
rows omit a separate class marker.

The saved local-body path needs to recognize these native plane rows as
reference scaffold before it identifies the imported solid. Use the retained
XML type and require the resolved class, when present, to agree. This restores
local body ownership and applies the existing strict rollback and storage
checks. [Local body readback](../../../../../Changes/Solidworks/Inspection/Parts/SolidworksLocalBodyReadback.md)
