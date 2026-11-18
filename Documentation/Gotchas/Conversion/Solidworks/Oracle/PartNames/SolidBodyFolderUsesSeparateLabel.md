# The solid body folder has its own label

The feature tree's body folder retains the label `Solid Bodies` after a
native body rename. In two SOLIDWORKS 2026 saves, the explicit names
`Body` and `Centered Solid` belong to the kernel body attribute.
An SDK projection based on the folder name loses each body label.

Resolve `SDL/TYSA_NAME` through the actual body owner when projecting
an explicit native label.

[Measured folder and native body names](../../../../../../re/solidworks/measurements/2026/SdkPartNamingArchive02.json)
