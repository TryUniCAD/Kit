# Strict SOLIDWORKS saved open-shell readback

The normal SDK recognizes an ordinary SOLIDWORKS 2026 part with one saved
inward open shell on a rectangular Front-plane blind boss. It reads the
active thickness from the linked `D1` parameter. The shell has one removal
selection, `face:1` of its historical stock boss. The separate auxiliary
edge stays outside the removal selection.

Full reads bind the closed saved result to its true producing feature and
configuration atom. Both modes follow the saved rollback to the stock that
owns the removed cap. Design-only reads retain the feature, sketch relations,
selection and topology summary after validating the same chronology.
Call `convert.open_document(source, strict=True, include_brep=False)` for
design-only inspection. Alternate selectors, outward mode and inconsistent
source ownership raise a format error. Permissive inspection retains the
native feature information and an unresolved-history diagnostic.

The [evidence record](../../../../re/solidworks/records/SavedOpenShellReader2026.md)
covers the original and native-edited disclosures from SOLIDWORKS 2026 SP05.2,
their independently observed geometry and guarded process contrasts. The
shared queue exercises the native retained transaction codec with a tracked
independent control and the shell geometry guard with an authored rounded
boundary. Native shell writing, arbitrary shell modes and protected
acceptance are tracked separately.

Both strict read modes report bounds from the saved vertices after validating
them against the sketch footprint. The shared rounding scenario checks that
the reported box extends to an admitted rounded vertex.
