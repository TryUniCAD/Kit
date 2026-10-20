# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from interchange import CadDocument, Capability

from convert.adapters.base.ContractTypes import (
    KSourceType as Source,
    KTargetType as Destination,
)
from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.base.TransferContract import CapTransfer as CapabilityTransfer
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WriteResult import WriteResult
from convert.adapters.registry import AdapterRegistry
from convert.engine.Compatibility.EngineType import BuildEngine
from convert.engine.EngineReader import EngineRead
from convert.engine.EngineResult import BuildResult
from convert.engine.EngineWriter import EngineWrite
from convert.results.ResultDetails import ResultDetails
from convert.results.ResultFlags import ResultFlags

globals().update({"ConversionResult": BuildResult()})
globals().update({"ConversionEngine": BuildEngine(globals()["ConversionResult"])})
