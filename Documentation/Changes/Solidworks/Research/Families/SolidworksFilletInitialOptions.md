# SOLIDWORKS single-edge fillet initial options

The exact SP05.2 native source trace binds the initial `Fillet_c.fc20`
array to the first kernel solve. A present empty array selects fresh
options. The solver subsequently stores six words on its default
successful branch. [Source evidence](../../../../../re/solidworks/records/EdgeFilletInitialOptions2026.md)
