# A DWG that Kit authors does not finish opening in Fusion

Fusion 2706.1.17 did not finish opening any drawing whose DWG Kit authored.
`Documents.open` waited in `DrawingDocument::waitForOpenToComplete`, while the drawing engine sat idle in its message loop.
Fusion showed no dialog, and only a restart released it.

| Variant             | DWG                                                      | Waited before restart |
| ------------------- | -------------------------------------------------------- | --------------------- |
| `K1SheetOnly`       | Authored sheet without views                             | Stopped by hand       |
| `S5SheetDimension`  | Authored sheet with one dimension                        | 602 s                 |
| `T5SheetDimension`  | `S5SheetDimension` with the AppInfo of a Fusion save     | 307 s                 |
| `U12AuthoredShellShorts` | `H1NoAcm` objects in Kit's shell                    | 460 s                 |

The Kit-built F2D members are not the cause.
`N2AuthoredF2d` wraps the Fusion-saved `H1NoAcm` DWG in Kit-built members, and it opened in 4.3 s with 3 views and 1 dimension.

Two parts of the authored DWG stop the open.
The first is the four header values that the [header tail gotcha](FusionDrawingHeaderTail.md) records.

The second is the combination of Kit's shell sections.
Each variant below is `Q1NoDataStore` with one part of Kit's shell, and each kept the A1 header values.

| Variant            | Part taken from Kit's shell                         | Result                           |
| ------------------ | --------------------------------------------------- | -------------------------------- |
| `Q8AuthoredSections` | Section set without `AcDb:Preview` and `AcDb:AppInfoHistory` | Opened in 5.2 s      |
| `W1KitAppInfo`     | One Kit product entry, without the trusted-file entry | Opened in 4.7 s                |
| `W3KitAuxHeader`   | Auxiliary header with a save count of 1             | Opened in 3.5 s                  |
| `W4KitSummary`     | Summary with empty texts                            | Opened in 3.4 s                  |
| `W5KitFreeSpace`   | Object free-space record                            | Opened in 6.1 s                  |
| `W6KitClassCounts` | Class instance counts recounted from the objects    | Opened in 3.6 s                  |
| `U4AuthoredShellTail` | All of the above together                        | Not open after 185 s, no dialog  |

`U4AuthoredShellTail` has the same header and object bytes as `Q8AuthoredSections`.
Only its AppInfo, auxiliary header, class, free-space and summary sections differ.
The runs do not show which pair or group of those changes stops the open.

The trusted-file entry of AppInfo is not needed.
`W1KitAppInfo` opened without it, so Kit never writes that entry.
