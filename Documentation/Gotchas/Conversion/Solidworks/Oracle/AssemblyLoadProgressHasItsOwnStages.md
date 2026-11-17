# Assembly load progress has its own stages

Opening the empty assembly returned successfully with zero errors or warnings.
The watchdog still clicked Close on the untitled progress window labelled
`Open Components`, `Update Assembly` and `Update Graphics`. The part/drawing
progress classifier did not recognize that triplet. That source phase failed.

The assembly observer records the known owned progress window without clicking
it. Other owned dialogs remain failures. Record the exact observed labels and
require a new clean source batch after changing the observation path. Do not
reclassify the original dismissed-window batch as acceptance evidence.

The [first source receipt](../../../../../re/solidworks/measurements/2026/AssemblySourceAttempt01.json)
records the button action and the independent open status.
