# SOLIDWORKS revolve KeyWords use compact empty tags

ElementTree serializes empty XML elements with a space before `/>`. The pinned SOLIDWORKS 2026 revolve discovery files use `/>` directly for empty KeyWords elements. Ordinary XML parsing accepts both spellings, and a byte comparison detects the space at the first empty element.

Compact the spelling when emitting the evidenced angular KeyWords form. Preserve the `0x86` prefix, UTF-8 declaration, CRLF framing and the ordinary revolve's `D1` degree suffix. The consumed sketch in this form has no `Type` attribute. [Exact disclosed KeyWords readback](../../../../../../re/solidworks/records/OrdinaryRevolvedBossReadback2026.md).
