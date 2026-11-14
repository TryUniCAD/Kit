# Creo oracle notes

## Environment

The local oracle is Creo Parametric 2027.2.0.0 on Windows 11 ARM under Parallels Desktop.
The installation is licensed and is used only for research and acceptance measurement.
Production code does not import or launch it.

## Control procedure

1. Start Creo in a fresh process.
2. Open the vendor empty-part control.
3. Confirm the model tree shows the default datum planes and coordinate system.
4. Record the process id and the visible model name.
5. Close the process before the next candidate.

The control used here was `solid_start_part_mmks.prt` with SHA-256 `b1374d7d356830300a8a4736b6f59a0ba5ef60938398a707fab02e69454aa`.
It opened with `FRONT`, `TOP`, `RIGHT`, and `DEFAULT_CSYS` in the model tree.

## Observed results

| Candidate | Result | Meaning |
| --- | --- | --- |
| Vendor empty-part control | Opened | Oracle and control are healthy |
| Hand-built legacy ASCII part | Rejected; Creo exited | Legacy ASCII is not a usable writer target for this release |
| Synthetic PSB container | Not opened | Container framing alone is not a valid model |

The synthetic PSB test is a parser fixture, not a vendor acceptance candidate.
It has no native model records.

## ARM64 note

Creo is an x64 application.
On Windows 11 ARM, the startup profile must declare the x64 processor environment before the application starts.
Without that declaration the launcher exits before the model window appears.
This is an environment requirement, not a format rule.

## Acceptance still required

A future writer must produce a fresh part with:

- a live feature tree;
- at least one solid body;
- measured volume and centre of mass;
- a driving dimension edit and rebuild;
- a healthy control before and after the candidate.

No such result exists for this change.
