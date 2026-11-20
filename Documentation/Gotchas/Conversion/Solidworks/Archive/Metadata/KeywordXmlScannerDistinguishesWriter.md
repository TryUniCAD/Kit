# Keyword XML writer imports trigger the XML parser rule

`DUO107` flags `QName` and `tostring` because its allowlist for
`xml.etree.ElementTree` lists only `Element` and `SubElement`.
The keyword writer uses `QName` in its tag validation and calls
`tostring` on an existing tree. Both operations run without parsing
XML input.

Keep the import-level exception restricted to these two writer
symbols. Route untrusted XML input through the existing hardened
reader. The fresh-process cases cover exact QName serialization and
refusal of both sentinel tag types.
[Scan job](https://github.com/TryUniCAD/Kit/actions/runs/44710841788/job/136201809268)
[Writer evidence](../../../../../../re/solidworks/records/KeywordFrameSlice2026.md)
