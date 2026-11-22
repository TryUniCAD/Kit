# Fresh sweep packet needs its local parent

The first disclosed cold-sweep staging command successfully verified all 31 frozen packet members. It then stopped before copying the packet because the parent of `C:\KitSweepCold01\Packet` had never been created on the guest. The packet digest and native candidate files stayed unchanged.

For the original frozen job, create the declared fresh guest parent before retrying the same stage command. Future freezes create any missing ancestors while still requiring both the designated packet and the results directories to be fresh. A final custody mismatch also produces an explicit failed terminal receipt. [Cold sweep protocol](../../../../../re/solidworks/records/OrdinarySweepColdConstruction2026.md)
