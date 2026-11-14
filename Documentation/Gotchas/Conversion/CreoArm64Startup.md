# Creo ARM64 startup exits before the model window

## Expectation

A licensed Creo Parametric installation starts from its desktop shortcut on Windows 11 ARM under Parallels.

## Observed behavior

The launcher exits with code 1000 before a model window appears.
The process list shows no `xtop.exe`.
The license status utility still reports the expected features.

## Cause

Creo is an x64 application.
The startup profile does not declare the x64 processor environment on this ARM64 host.

## Workaround

Add the x64 processor declarations to the startup profile before launching Creo.
Use the vendor-supported startup profile for the installed release.
Do not change the license file or the installation.

## Evidence

- Local Creo 2027.2.0.0 on Windows 11 ARM under Parallels.
- The same profile started after the processor declarations were added.
- The vendor empty-part control then opened with its datum planes and coordinate system.

## Scope

This is an oracle environment issue.
It does not change the PSB format and must not appear in production conversion code.
