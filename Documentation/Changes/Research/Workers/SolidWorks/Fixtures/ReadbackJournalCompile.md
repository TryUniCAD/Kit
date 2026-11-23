# Compile the managed readback journal during fixture setup

Two hosted Windows fixtures reached the PowerShell 15-second deadline
before the application worker could inspect their intended report faults.
The command shared its deadline between compiling the C# fixture and
creating the managed journal. It returned a timeout in one case that
exercises missing source evidence and one that exercises a broken
progress chain.
[Missing source case](https://github.com/TryUniCAD/Kit/actions/runs/45174474097/job/137692603899) ·
[Progress chain case](https://github.com/TryUniCAD/Kit/actions/runs/45175300556/job/137695305312)

Fixture setup compiles the pinned source and the test driver into a
fresh assembly before starting the listener. The timed capture loads
that assembly and drives the same managed journal through the child
process. The queue assertions still check the intended report faults and
the binding of the emitted journal to its native owner.
