# SOLIDWORKS 2026 drawing default views

Fresh drawing roots initialize ten indexed `moView_c` owners. In the English
installation, index zero is `*Full Sheet` and indices one through nine are
`Unused`. Both transform owners on all ten objects start at identity.

The exact `moDrawing_c` constructor at `0x4c96b480` allocates index zero at
`0x4c96b962`, passing the string loaded from resource `0x2abc`. Its next loop
allocates the remaining nine independently with the original UTF-16 literal
at `0x4d26c9c8`. Each reaches the existing indexed constructor
`0x4c14fb90`, which creates separate identity transforms at `0x368` and
`0x370`. The [standard part view trace](StandardViewsConstruction2026.md)
documents the later rotation operation used for parts.

The constructor installs the actual drawing vtable at `0x4d26af68`. Its name
refresh cell `+0x1880` reaches `0x4c97ae50`. That function writes the same
resource and literal to `moView_c.f358` and leaves both transforms intact.
Its transform refresh cell `+0x15d0` reaches `0x4c97aef0`. The drawing
override assigns two identity transforms to the first view only. This
explains why a saved generated drawing can have the correct names alongside
rotations inherited from the former part constructor.

The [native ledger](PlainDrawingDefaultViews2026.json) binds eight complete
function or leaf spans, two instruction spans, three data spans, five
imports, two real virtual cells and the original English resource. The
resource tree was inventoried independently by REA. That resource is type
6, block 684, slot 12, language 1033. The [replay script](../../tooling/sw2026/drawing_notes/PinDrawingViewDefaults01.py)
verifies both private DLL hashes, all spans, dispatch cells and exact string
origins without starting CAD.

The internal ANSI note recipe now selects this initializer and the existing
native [ANSI detailing operation](DrawingAnsiStyleConstruction2026.md).
The two owners are independent. A source with a nondefault saved view or
typography still needs its actual native presentation projected and
regenerated. A complete native rendering comparison and public qualification
remain separate requirements.
