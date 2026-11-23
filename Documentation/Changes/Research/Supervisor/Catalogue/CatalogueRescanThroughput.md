# Catalogue rescan throughput

Fresh feature catalogue runs allow up to eight `inference.rescan` jobs per physical session.
The runner retains the strict 16 MiB input footprint limit, 256 MiB admission floor and 768 MiB worker stop threshold.
The private offline controller allows eight logical claims per configured worker up to the existing store ceiling of 64.
The native pipeline retains its 64-claim ceiling. A resumed catalogue uses its saved registry and store.

Group staging renews leases before copying inputs and when due during and after copying.
The launch gate renews each lease again after durable process publication and before the worker starts.
During settlement, A03 renews only members whose intake is still pending.
A group of eight avoids 28 checks of earlier members during settlement.
Each member retains its own lease, deadline, fingerprint, artifact verification and accepted receipt.
The owner transaction, group recovery and durable singleton retry markers retain their existing protocols.

## Windows group-size calibration

The baseline uses `14570404846c8aa1f90b02e68d6f70a419719ca7` and 64 distinct pinned Fusion discovery archives from 36 study families.
The 7,130,847 input bytes match the committed Git blobs and the pinned corpus at `74a0bc353421c25f7a6c539897baadf593a05766`.
Selection excluded nondiscovery splits and their byte aliases.
The older 9,670,016-byte private manifest was unavailable. The [historical pair](../GroupedOfflineCalibration.md) is a separate measurement.

The host used an Intel Core i9-10900, 20 logical CPUs, Windows build 26200, Python 3.14.6 and pywin32 312.
Each arm used a fresh store, one physical slot, 20 logical slots, one worker thread and a strict 16 MiB footprint limit.
All arms used the same ordered manifest, 256 MiB admission floor and 1,024 MiB worker stop threshold.
They reserved two logical CPUs and 4 GiB of RAM.
Each job used a 60-second lease, a 120-second deadline and strict-first decoding with `allow_partial=true`.
Each arm had a 720-second supervisor limit.

| Group cap | Sessions | Wall seconds | Archives/min | Claim-to-settlement p95 | Decode-to-settlement p95 | Sampled peak working set |
| --------: | -------: | -----------: | -----------: | ----------------------: | -----------------------: | -----------------------: |
|         4 |       16 |      148.067 |       25.934 |                10.868 s |                  2.154 s |             91,181,056 B |
|         8 |        8 |       87.153 |       44.061 |                11.437 s |                  2.816 s |             91,205,632 B |
|        16 |        4 |       57.780 |       66.458 |                17.131 s |                  5.639 s |             91,480,064 B |
|        20 |        4 |       63.114 |       60.843 |                18.949 s |                  7.240 s |             92,606,464 B |

| Group cap | Reader, validation and serialization | Group claims | Group heartbeats | Group settlement |
| --------: | -----------------------------------: | -----------: | ---------------: | ---------------: |
|         4 |                             90.412 s | 6.612 s / 17 |    16.703 s / 48 |    12.796 s / 16 |
|         8 |                             52.738 s |  4.038 s / 9 |     8.289 s / 24 |      7.655 s / 8 |
|        16 |                             30.691 s |  2.319 s / 5 |     3.612 s / 12 |      8.884 s / 4 |
|        20 |                             32.376 s |  2.907 s / 5 |     5.120 s / 12 |      7.005 s / 4 |

Controller totals measure complete adapter calls and include subprocess startup and transaction commit.
Each arm includes one empty grouped claim and one empty singleton claim at shutdown.
The reader total includes imports, validation and serialization. Wall time also includes staging, process launch, polling and cleanup.
First-member reader intervals totalled 82.115, 42.756, 20.665 and 21.604 seconds.
All later members totalled 8.297, 9.982, 10.025 and 10.772 seconds.
The working-set measurement samples the owned Windows Job Object, excluding the supervisor launcher and interpreter.
Maximum measured input footprints were 797,507, 1,337,310, 2,039,027 and 2,593,411 bytes.
The cap-20 arm formed groups of 20, 20, 20 and four.

All arms accepted each archive once, verified complete process measurements and closed every owned session, claim and process.
The shared neutral output digest is `6860ae50eb52ca9aae99a87290a0abaf78fa4773d3e5a01c8c2829690e13c424`.
The canonical manifest SHA-256 is `8857156e9c5dd5bd8fbd7e623b166ae155c86b5e6739620000595617d0fbc2e7`.
The provenance SHA-256 is `9500cf83f07e34a0e0fe97052bc036d74eaadfc5abdf5e7ea420389b2aa71588`.
The baseline report SHA-256 is `97d3331a4f07e117dbb7839ed117f212329ed68ac403f797a95827147a66aa58`.
The cap-20 report SHA-256 is `804746a798e06d05dae3fcf8f3e4904c12d4042d06d15ea7204881d12ceb1507`.

Eight improved throughput by 70% over four with a 0.569 second increase in claim-to-settlement p95.
Sixteen added 5.694 seconds to that p95 and increased total settlement time compared with eight.
Twenty used the same number of sessions as sixteen and had a higher settlement p95 on this roster.
The catalogue uses eight to balance throughput with time to settle each member.
Group protocol 1 supports up to 20 members for runners with a suitable footprint and logical claim budget.

The first three arms ran in ascending order. The cap-20 arm ran in a later timing window.
Host CPU busy time, including the benchmark, was 15.20%, 21.14%, 13.87% and 21.58% respectively.
An earlier uninstrumented four-member arm took 160.005 seconds and produced the same output digest.
The calibration has no rescan assessment dependencies. It measures one host and one physical slot.
See [Windows calibration instrumentation](../../../../Gotchas/Research/Supervisor/WindowsCalibrationSupervisorEntry.md) for the probe location.

## Matched controller replay

The cap-eight replay used the same manifest, package inventory, limits and calibration runner.
It used the controller and staging changes from `1684dd0f285afb242b536454b1c19d1cba3cbea0`.
All 64 archives completed once in eight groups with complete telemetry and clean shutdown.
The neutral hash for each job matched the baseline.

| Cap-eight observation         | Baseline | Candidate |
| ----------------------------- | -------: | --------: |
| Group heartbeat calls         |       24 |        16 |
| Heartbeat adapter wall        |  8.289 s |   5.590 s |
| Group claim adapter wall      |  4.038 s |   5.692 s |
| Group settlement adapter wall |  7.655 s |  10.121 s |
| Reader interval total         | 52.738 s |  62.924 s |
| Wall time                     | 87.153 s | 105.682 s |
| Claim-to-settlement p95       | 11.437 s |  20.905 s |
| Sampled peak working set      |  91.2 MB |   91.1 MB |

Every candidate group made two heartbeat calls before decoding. Every baseline group made three.
The candidate replay measured fewer heartbeat calls and less heartbeat wall time.
Total wall time and settlement time were higher in the candidate run.
Host CPU busy time was 15.17% during the candidate, compared with 21.14% during the baseline.
The candidate report SHA-256 is `be4924ef0ec982c5491372ea5f40b648d9ae348ae2a5f1cd750132112f0ce029`.

## Physical worker capacity probe

A separate probe used the baseline code, cap eight, 64 logical leases and default adaptive limits.
The configured two-CPU and 4 GiB memory reserves remained in effect.
Each arm accepted the same 64 inputs once with the same neutral output digest.

| Requested physical slots | Startup limit | Peak simultaneous readers | Wall seconds | Archives/min | Host CPU busy | Peak sampled working set | Minimum available RAM |
| -----------------------: | ------------: | ------------------------: | -----------: | -----------: | ------------: | -----------------------: | --------------------: |
|                        8 |             4 |                         4 |       36.917 |      104.017 |        21.03% |             294,920,192 B |      13,051,379,712 B |
|                       16 |             8 |                         4 |       32.554 |      117.959 |        24.70% |             367,009,792 B |      13,001,084,928 B |
|                       18 |             9 |                         6 |       23.341 |      164.519 |        35.21% |             453,345,280 B |      12,871,184,384 B |

Each arm had eight full groups. At cap eight, 64 logical leases hold at most eight full groups at once.
No arm sustained its requested decode overlap for one second or ran through the 60-second adaptive growth boundary.
Even the four-reader peak at eight requested slots lasted only 0.270 seconds of simultaneous reader work.
Available memory and host CPU observations show spare resources during this short workload.
The probe does not establish a sustained throughput recommendation or a Windows adaptive ramp gain.
The physical probe SHA-256 is `288ff9cf2b24328ae8dc6288ccc25f28fc5a9c1c9eef859e7393555abb58cf24`.

## P03 catalogue rescan replay

The matched replay used the SOLIDWORKS extrude catalogue fixture on the same Windows host.
It used one physical worker with Python 3.14.6, NumPy 2.4.6 and pywin32 312.
The worker configuration retained two reserved CPUs and 4 GiB of reserved memory.
The private harness reported native verification unavailable before the catalogue attempted any application launch.
[Catalogue native verification](../../../../Gotchas/Research/Offline/CatalogueNativeVerification.md) · [Catalogue inference dependencies](../../../../Gotchas/Research/Offline/CatalogueInferenceNeedsNumPy.md)

| Observation | Baseline | Candidate |
| --- | ---: | ---: |
| Rescan groups | 4 and 4 | 8 |
| First rescan claim to final settlement | 15.18 s | 7.90 s |
| Command wall time | 38.45 s | 29.50 s |
| Claim-to-settlement p95 | 7.41 s | 7.86 s |

Baseline source was `14570404846c8aa1f90b02e68d6f70a419719ca7`.
Candidate source was `0330d81c6526d788393e860e0bfbab4c9ae56a70`.
Both runs completed all eight P03 rescans once and produced equal neutral digests, scope order and job results.
Both retained P04 waiting evidence and reported `coverage_incomplete`.
The fixed P03 scope contains eight sources. The wider caps were measured only in the archive calibration.

Fixture SHA-256 `5601bae9faac269300b7416cd7010e43e8c74353fe891d3edf8a09c61bc22be1`.
Neutral output SHA-256 `623a3800c0170fd0f85ffb63ba81a2027d531c68a3855bbb711edcdc1a9558d4`.
Baseline replay SHA-256 `3b7f34ceb802f704e0d433d6c84f3fa9e221d193d90910a6fc54cc3937a75845`.
Candidate replay SHA-256 `375147243183191bcb4326124e844b04f7f3b33cf0333986bb0258df0dc15e79`.

[Research supervisor guide](../../../../Reference/Research/ResearchSupervisor.md#optional-grouped-sessions)
