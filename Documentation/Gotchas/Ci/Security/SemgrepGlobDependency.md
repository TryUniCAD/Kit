# Semgrep glob dependency

Semgrep 1.185.0 declares wcmatch 8.x. That range includes a denial-of-service issue affecting glob matching. The queue vulnerability scanner rejects the resulting lockfile. Kit overrides wcmatch to 11.2, the first fixed version, and locks its bracex dependency alongside it.

A local Semgrep 1.185.0 scan with wcmatch 11.2 selected the intended Python fixture through an include glob and reported the expected rule match with no scanner errors. The merge queue still runs the repository scan and checks the lockfile. [Advisory](https://osv.dev/vulnerability/GHSA-53pm-wgxf-c6qf)
