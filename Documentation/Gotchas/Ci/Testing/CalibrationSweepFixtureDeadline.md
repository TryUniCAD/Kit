# Calibration sweep fixture deadline

The constrained calibration case runs eight real Fusion decode jobs through
one slot in each trial. Its trial deadline includes supervisor startup,
sampling, and settlement. The case checks that every job completes with
physical resource measurements while reported decode overlap stays within
the slot limit.

Three Linux queue candidates reached the original 30-second fixture deadline.
The first trials completed six, seven, and eight jobs respectively. The trial
with all eight completed jobs reached the deadline before its supervisor exited.
[Section reader candidate](https://github.com/TryUniCAD/Kit/actions/runs/44784279646/job/136455371687) ·
[Fusion catalogue candidate](https://github.com/TryUniCAD/Kit/actions/runs/44788351710/job/136469560686) ·
[SOLIDWORKS catalogue candidate](https://github.com/TryUniCAD/Kit/actions/runs/44788019447/job/136468439580)

Use a 45-second deadline for each of the four trials in the positive sweep.
The observed six jobs in 30.54 seconds imply about 41 seconds for eight jobs
at the same rate. The separate five-second timeout case still checks early
termination, and the sweep retains its 240-second process watchdog.
[Positive sweep](../../../../tests/Research/Calibration/CalibrationTests.py) ·
[Timeout case](../../../../tests/Research/Calibration/CalibrationFailureTests.py) ·
[Process runner](../../../../tests/Research/Calibration/RunCalibration.py)
