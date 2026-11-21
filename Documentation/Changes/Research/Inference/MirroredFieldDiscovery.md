# Mirrored field discovery

File-driven SOLIDWORKS research takes feature types and dimension names from the input's native fallback definitions. It scans bounded, tracked example parts for named binary measurements under the same typed feature. It learns where signed binary64 copies recur within the next 2,048 bytes of that feature interval. Discovery excludes the source file and identical resolved streams, and requires multiple training documents and multiple distinct values.

The report records controls, surviving offsets, held-out measurements and agreement with the displayed value. For eligible fields a strict CLI replay verifies a candidate public reader and writes `MirroredFields.patch` in the run directory. Its learned rules contain format identifiers, relative offsets and signs. The integrated reader uses the named scalar, the feature boundary, each mirror and the displayed units. Other neutral parameters must remain identical in the candidate replay.

This experiment covers fields with redundant scalar storage. Independent copies do not establish the meaning of selections, ownership of bodies or pattern placement.

At bb1af7bb5, two local runs each scanned 58 tracked examples within the search budget. The turbine wheel generated a patch for a circular pattern angle. The independent cylinder-head run generated a patch for linear pattern spacing. After applying both entries, the public reader returned 32.72727273000008 degrees for the wheel while preserving its displayed text of 32.73 degrees. Strict reads also returned 60 degrees on the turbine and 107 mm on the head. The whole-file runs remained incomplete. Fields lacking a unique input scalar, varied controls, a stable copy or a held-out match retain their reason in the discovery report.
