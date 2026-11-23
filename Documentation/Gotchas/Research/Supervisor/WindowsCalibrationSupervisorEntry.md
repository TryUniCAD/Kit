# Windows calibration imports the supervisor entry point

The offline calibration runs `CalibrationWindowsHost.py` inside the owned Windows Job Object.
The host records the interpreter identity and calls the imported `Supervisor.main` function.
A probe installed only under the supervisor's `__main__` guard therefore collects no controller timings on Windows.

Attach private instrumentation to the imported entry point before the host calls it.
Retain normal calibration supervision, receipts and Job Object cleanup to verify the observed workload.
The first four-member arm kept complete worker and cleanup evidence but missed A03 timings.
The matched replay collected those timings without changing the reader outputs. [Calibration evidence](../../../Changes/Research/Supervisor/Catalogue/CatalogueRescanThroughput.md)
