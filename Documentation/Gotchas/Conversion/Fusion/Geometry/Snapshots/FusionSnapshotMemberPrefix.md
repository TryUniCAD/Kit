# Snapshot part names are relative to the active asset

`DocumentSnap.Name` contains the member path relative to the active Fusion asset. The Design serializer uses the shorter BRep part name. The physical ZIP member adds the active asset prefix to the typed path. Reading the relative path directly through `ZipFile.read` refused a valid newly generated archive even after strict typed readback passed.

Use the typed relative path for the serializer join. Use `ContainerLayout.KAssetPrefix` with that path when verifying the physical ZIP payload. Keep both paths explicit in evidence that binds the member bytes. See the [independent snapshot generator](../../../../../Changes/Research/Encoder/FusionGeneratedCuboidSnapshot.md).
