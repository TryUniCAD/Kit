# Provider cleanup must bind the process identity

A cleanup probe must distinguish a surviving owned child from another process with the same PID.
The old provider fixture logged only the child PID.
It checked that PID after cleanup had terminated the job and closed its handles.
The [Windows failure](https://github.com/TryUniCAD/Kit/actions/runs/45384866420/job/138413726421) therefore lacks evidence of which process remained live.

Record the child’s creation identity before releasing the provider.
Require that identity in the receipt and compare it with the independently observed live identity after cleanup.
Preserve verified job termination and fail on missing identity evidence.
[Windows process identifiers](https://learn.microsoft.com/en-us/windows/win32/procthread/process-handles-and-identifiers) remain valid only until process termination.
