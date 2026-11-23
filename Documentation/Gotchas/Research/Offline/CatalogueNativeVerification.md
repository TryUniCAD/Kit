# Catalogue reports can start native verification

The feature catalogue can run its inference jobs without a configured native worker.
After those jobs finish, it separately checks for a native verification API for each format with completed rescans.
This check can lead to application startup even when the run omitted `--native-config`.

Use the fixed offline calibration tool when timing must exclude native applications.
A private catalogue measurement can force API unavailability at the report boundary with the normal catalogue, controller and workers.
Record that override and the native verification status with each measurement. [Catalogue rescan throughput](../../../Changes/Research/Supervisor/CatalogueRescanThroughput.md)
