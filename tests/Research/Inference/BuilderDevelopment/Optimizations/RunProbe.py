# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.Security.PathBoundary import ResolveTemp

from pathlib import Path as FilePath
from sys import argv as CliArgs, path as SearchPaths


# one narrow entry point starts fixture controllers or workers without importing production code in pytest
def MainProbe() -> None:
    SearchPaths.insert(0, str(FilePath(__file__).resolve().parents[5]))
    from tests.Research.Inference.BuilderDevelopment.Optimizations.JsonBoundary import (
        ReadConfig,
    )

    ConfigValue = ReadConfig(ResolveTemp(CliArgs[1]).read_bytes())
    if ConfigValue["action"] == "broker":
        from tests.Research.Inference.BuilderDevelopment.Optimizations.BrokerChild import (
            MainBroker,
        )

        MainBroker()
    elif ConfigValue["action"] in {
        "remote",
        "token",
        "schema",
        "oversized",
        "incomplete",
        "queued",
        "owner",
        "recordshape",
        "instructions",
    }:
        from tests.Research.Inference.BuilderDevelopment.Optimizations.BrokerRequest import (
            MainRequest,
        )

        MainRequest()
    elif ConfigValue["action"] == "stale":
        from tests.Research.Inference.BuilderDevelopment.Optimizations.FakePeer import (
            MainPeer,
        )

        MainPeer()
    else:
        from tests.Research.Inference.BuilderDevelopment.Optimizations.WorkerChild import (
            MainWorker,
        )

        MainWorker()


if __name__ == "__main__":
    MainProbe()
