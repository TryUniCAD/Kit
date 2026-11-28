# A displayed circle centre can lose its exact wire value

The disclosed Front diameter circle stores its centre Y as `-0.005675`
metres. The model displays `-5.675000000000001` millimetres. Multiplying that
display by 0.001 gives the adjacent binary64 metre value and changes the
regenerated archive.

Keep the actual typed native centre with the separate fixed-point owner.
Confirm that the original metre word produces the public coordinates,
then use the shared exact inverse to reconstruct the constructor's
millimetre input. Verify the complete regenerated source and exact
measured file hash before publication.
[Measured circle republication proof](../../../../../../re/solidworks/records/SdkColdCircleRepublication2026.md)
