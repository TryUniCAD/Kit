# Restore breakpoint detach can change first-open results

The same generated SOLIDWORKS 2026 prism opens with warning 32 and zero bodies under the ordinary COM flags. A hardware breakpoint followed by detach in the early kernel restore wrapper can produce zero warnings and one body. Continuing the open with the debugger attached after that same stop reproduces the original warning and empty public body inventory.

Keep the input digest, adjacent native probe sites, debugger lifetime and two uninstrumented control runs in the report. Read the kernel body count during the warning-producing path and qualify loadability through the ordinary uninstrumented application lifecycle. [Measured comparison](../../../../../../re/solidworks/records/PrismOpenBodyAdmission2026.md)
