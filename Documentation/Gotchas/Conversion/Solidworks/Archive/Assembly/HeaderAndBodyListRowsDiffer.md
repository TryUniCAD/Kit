# Header and object-body list APIs expose different item shapes

The shared archive body representation stores an object list's items as
rows such as `{"o": node}`. The standalone SDK Header codec instead
stores its ordered `suObList.items` as a tuple of actual nodes. Both
representations retain native object identity, but their Python row
accessors are different.

The mate constructor's existing `DatumTime` helper currently expects
object-body rows. A diagnostic generated a child from a neutral request,
read its generated ModelHeader with the SDK Header codec and supplied
that actual header to the distance constructor. Its one direct log node
failed the embedded-record guard before any distance/mate allocation.
The generated parent/child comparison using the composer's original
body-header view remains a separate passing result.

Project direct header log and stamp nodes explicitly at this boundary,
preserving their identities and values. Do not skip a valid log list or
use a synthetic unset time to hide the shape mismatch. This is an API
view difference, not a reason to add a different native field layout.

[SDK Header list decoder](../../../../../../src/convert/adapters/solidworks/Archive/Header/ReadHeaderList.py),
[current mate epoch helper](../../../../../../src/convert/adapters/solidworks/Archive/Construction/PlanarMates/DatumTime.py)
and the [distance composition boundary](../../../../../../re/solidworks/records/SdkDrivingDistanceConstruction2026.md#header-api-composition-boundary)
record the exact scope.

The scoped [`ReadLogItems` projection](../../../../../../src/convert/adapters/solidworks/Archive/Construction/PlanarMates/ReadLogItems.py)
now lets `DatumTime` consume both views while retaining actual nodes and
strict class/schema/count checks. The [source-only integration proof](../../../../../../re/solidworks/records/SdkHeaderEpochIntegration2026.md)
preserves the earlier diagnostic and qualifies the new boundary separately.
