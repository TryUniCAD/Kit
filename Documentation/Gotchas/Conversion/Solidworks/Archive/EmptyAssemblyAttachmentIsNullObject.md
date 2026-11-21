# An empty configuration attachment is a null object tag

The two zero bytes in an ordinary empty configuration's attachment
stream look like a count. The native loader passes the archive to the
typed attachment extraction operator, which reads an object tag.
Those bytes encode an absent attachment.

Use the normal tagged object grammar when the stream is needed. The
[loader trace](../../../../../re/solidworks/records/AssemblyAttachment2026.md)
shows the separate missing-stream route, and the
[empty assembly measurement](../../../../../re/solidworks/measurements/2026/EmptyAssemblyNative01.json)
verifies that the stream can be absent for these fresh empty assemblies.
