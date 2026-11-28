# Face attribute names may repeat

A helper for ordinary body names requires every owned attribute name to be unique. Applying that rule to the actual cylindrical faces rejects valid disclosed SOLIDWORKS 2026 saves: the face owns two separate `FACE_AUTOMATION_2_2001` attributes.

Walk and validate the complete actual owner chain, then require the requested identity attribute uniquely. The concentric projection requires one `FACE_ID_2001`; it does not reject unrelated repeated automation attributes or choose one identity by ordinal.

[Actual owner evidence and malformed-input checks](../../../../../../re/solidworks/records/PublicConcentricMateRead2026.md)
