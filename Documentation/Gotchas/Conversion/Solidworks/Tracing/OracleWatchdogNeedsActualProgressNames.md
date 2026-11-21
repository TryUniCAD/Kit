# Oracle watchdog needs the batch's actual progress filenames

The host watchdog's default filename is `Record.json`. The ordinary revolve batch writes the aggregate checkpoint to `Inspection.json` and gives each phase record a case-specific filename. A default observer recorded zero changes and reached the no-progress deadline while the guest continued writing the revolve records.

The host stopped its owned transport. The guest later persisted a passing terminal report with eight candidate phases and two healthy controls. An immediate process inventory still showed the fourth candidate's SOLIDWORKS PID. The follow-up inventory found the VM idle and the same three license processes. The exact native, transport and inventory hashes are retained in the lifecycle receipt. [Native receipt](../../../../../re/solidworks/measurements/2026/SdkOrdinaryRevolveNative01.json) [Progress observer change](../../../../Changes/Solidworks/Inspection/Oracle/SolidworksOracleProgressNames.md)

Pass `--progress-file Inspection.json` for this batch. Select only checkpoint files that change during execution. Use the native terminal report and a current process inventory when recovering after a transport timeout.
