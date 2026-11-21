# SOLIDWORKS 2026 through-all cut projection

Task `B04-SW2026-EXTRUDE-THROUGHALL` is delivered through PR #121. The public reader now binds both feature definitions from the actual resolved and configuration graphs in six disclosed native saves.

| Disclosed design | Primary end | Secondary end | Native reverse flag | Stock depth before and after edit |
| --- | --- | --- | --- | --- |
| D01 | Through all | Absent | Set | 27.91 mm, 41.53 mm |
| D02 | Through all | Absent | Clear | 32.47 mm, 46.37 mm |
| D03 | Through all | Through all | Set | 24.83 mm, 38.71 mm |

The linked `moEndSpec_c` tuples `(f08, f0c, f10)` are `(1, 1, 0)` for a single through-all direction and `(0, 1, 1)` for two. The independent reversal flag `f8c` comes from the actual native owner. Both saved directions report zero to the vendor depth query, with null typed slots `f18` and `f20` and no actual cut display dimensions. The neutral primary and secondary lengths are absent. The existing archive decoder retains the full unary and binary source fields.

The cut end is schema one, starts on its actual sketch, and has no draft, secondary length or alternate geometric owner in this profile. The source constructor initializes the separate `f158` word to zero. Saved cut words in the three original disclosed states include `1119080160`, `1717906144`, and `812717568`. The reader retains those raw words in the typed archive and uses the active end selections and actual owners for portable intent.

The stock is a single forward mid-plane prism with a live length. The cut consumes its managed output atom through the exact saved body chooser and keeps its own result atom. Its free circle carries the native centre and radius, with zero sketch constraints. The public timeline retains both sketch links and the consumed producer, and `CadDocument` wire serialization preserves both through-all directions and the absent lengths.

The [audit](../../tooling/sw2026/AuditThroughAllProjection.py) uses the pinned SP05.2 source and edited reopen records. Twelve strict public path and byte reads match the native stock lengths, circle values, cut directions and observed absence of active cut drivers. The saved B-rep loads in every positive read. Six fresh diagnostic processes reject added active distances, a conflicting second end, a foreign chooser owner, an incorrect consumed atom and a mismatched wrapper atom. The [receipt](../measurements/2026/PublicThroughAllEndRead01.json) binds all eighteen SDK process results to the exact source files. The original hold-outs remain sealed for writer qualification.
