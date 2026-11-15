# Configuration version changes on save

The base configuration constructor seeds `f9a8` with `2045`. That word is not
a fixed format constant for a new 2026 configuration.

Native saving replaces it with the selected archive version when the
configuration has an opened model. The serializer then writes that version to
CMgr. Its branch without an opened model preserves the previous version.
Fresh graph construction must apply the ordinary save rule to the actual
owner graph, rather than reuse the constructor seed.

The parent-owned native failure trace observed global version `19000` with
helper context version `2045`; the healthy control had `19000` in both.
The generated configuration still contained the constructor seed.
The fresh factory now emits its selected target version. The exact loader
transfer and corrected candidate acceptance require further evidence.

The [construction record](../../../../../re/solidworks/records/ModelConstruction2026.md#configuration-construction)
records the native assignment and branch condition.
