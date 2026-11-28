# End-reference presence controls stored arrays

An ordinary blind extrusion can decode without `moEndSpec_c.f28` or `f48`. Their preceding `has_f28` and `has_f48` bytes control whether those embedded arrays exist on the wire. A constructed runtime graph and a decoded wire graph do not have identical field membership.

The first origin-drawing normalizer indexed both arrays unconditionally. Four generated children correctly stored presence zero and omitted the payload fields, so the observer raised `KeyError: f28`. Four disclosed native children instead stored presence one with `n=0` and no items. Both representations have no selected end-reference objects. Neither justifies a synthetic stored array in the other branch.

Select the exact presence branch. Zero requires an absent or null payload. One requires an explicit array whose count equals its actual row count. This ordinary no-reference profile admits only zero rows. Reject malformed presence, a contradictory payload or a populated array. Preserve the actual representation separately from semantic projection.

The current SDK [field layout](../../../../../../src/convert/adapters/solidworks/Archive/Bodies/Layouts/Resolved/FeatureFields.py) and [typed end reader](../../../../../../src/convert/adapters/solidworks/Core/TypedResolved/Ends/ReadEndMode.py) already express this distinction. The private projection correction changes no SDK codec, constructed stream or public admission.
