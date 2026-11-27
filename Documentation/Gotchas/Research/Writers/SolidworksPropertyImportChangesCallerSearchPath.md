# A pinned property import can change the caller's module search path

The composition command accepts a clean pinned property checkout. Its property
module adds that checkout's automation and encoder directories to `sys.path`
when imported. A complete property encoder directory also contains an older
`ExactSketchIntent.py`.

The maintained process smoke hydrated both property directories through the
existing historical-checkout helper. The later composition import selected
that foreign sketch helper. The final module-identity guard refused the valid
request with `ExactSketchIntent escaped its expected checkout`, before output.
The earlier narrow local property checkout did not expose this collision.

The composition now restores its caller's search path after the pinned property
import, including on an import failure. Exact dependency, clean-checkout and
module-identity guards remain active. The property verifier and shared artifact
helper also have explicit origin checks. The test retains the colliding encoder
directory rather than omitting it.

The [maintained process case](../../../../tests/CliResearch/EmptyOwners/CompositionTests.py)
uses the real three-request command. [Composition scope](../../../../re/solidworks/records/EmptyOwnersPartComposition.md)
keeps native and full-source qualification separate.
