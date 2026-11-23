# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import argparse
import json
import tempfile
from pathlib import Path

from LifecycleCases import check_dependents, check_invalidation, check_supersession
from RaceCases import check_graph, check_races
from SchedulingCases import check_grouped, check_limits, check_priority, check_resources
from SupervisorCases import check_supervisor


def main():
    parser = argparse.ArgumentParser(description="Exercise shared queue behavior through concurrent controller processes")
    parser.add_argument("scenario", choices=("races", "lifecycle", "scheduling", "supervisor"))
    args = parser.parse_args()
    scenarios = {
        "races": (check_races, check_graph),
        "lifecycle": (check_supersession, check_invalidation, check_dependents),
        "scheduling": (check_limits, check_priority, check_resources, check_grouped),
        "supervisor": (check_supervisor,),
    }
    with tempfile.TemporaryDirectory(prefix="kit-shared-queue-") as temporary:
        root = Path(temporary)
        reports = [scenario(root) for scenario in scenarios[args.scenario]]
    print(json.dumps({"scenario": args.scenario, "status": "passed", "reports": reports}, sort_keys=True))


if __name__ == "__main__":
    main()
