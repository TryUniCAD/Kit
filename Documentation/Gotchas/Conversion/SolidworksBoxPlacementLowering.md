# Box placement lowering

## Expectation

A standalone FreeCAD `Part::Box` or `PartDesign::AdditiveBox` with a pure XY placement
translation can be lowered to the recovered rectangle-pad program by translating the
four sketch corners, keeping the same length, width, and height parameters.

## Actual behavior

The recovered box `ResolvedFeatures` program hard-codes a `Point1@Origin` relation
string at logical offset 7047, and the rectangle sketch is otherwise unconstrained. The
sketch relation and constraint grammar is not recovered, so writing translated corners
without changing that relation would either rebuild the rectangle back against the model
origin or leave a sketch whose constraints no longer match its geometry. Either result
would keep a parameter and history capability that the output cannot honor.

A first implementation that only translated the corners passed the structural checks
(`HasVendorPartEncoding`, vendor-loadable, application-usable) and decoded the expected
bounds, but review correctly identified that it had not been rebuilt in SOLIDWORKS and
that the origin relation was unchanged. No donor stream, relation rewrite, or capability
downgrade was acceptable, so the change was withdrawn.

## Workaround

Keep the identity placement requirement for the box family: any nonzero placement still
declines native encoding and the public writer falls back to its normal carrier or
usability error. Supporting translated boxes requires recovering the sketch
relation/constraint records or a native placement record, then validating a rebuild and
the translated position in the SOLIDWORKS oracle. That work is blocked in this
environment because the Parallels VM rejects `prlctl exec` without credentials
(`Unable to authenticate the user`) and the audited FCStd corpus is absent.

See [the box program string table](../../../../src/convert/adapters/solidworks/programs/resolved/box/Methods/Archive/SuCArchive/WriteString.py)
and [the translated-box review finding](https://github.com/TryUniCAD/Kit/pull/110).
