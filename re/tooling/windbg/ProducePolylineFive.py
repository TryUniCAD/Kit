from __future__ import annotations
import json as JsonData
from pathlib import Path as PathInfo
import sys as System

from convert import convert as ConvertDoc
from convert import open_document as OpenDoc
from convert import write_document as WriteDoc


def ConvertOne(Source: PathInfo, Neutral: PathInfo, Target: PathInfo) -> dict[str, object]:
    try:
        ConvertDoc(Source, Neutral, source_format="solidworks.sldprt", allow_carrier=False)
        Document = OpenDoc(Neutral)
        Result = WriteDoc(Document, Target, allow_carrier=False)
        return {
            "source": str(Source),
            "neutral": str(Neutral),
            "target": str(Target),
            "vendor_loadable": Result.IsVendorLoadable,
            "application_usable": Result.IsAppUsable,
            "near_lossless": Result.IsNearLossless,
            "diagnostics": [str(Item) for Item in Result.diagnostics],
        }
    except Exception as Error:
        return {
            "source": str(Source),
            "neutral": str(Neutral),
            "target": str(Target),
            "vendor_loadable": False,
            "application_usable": False,
            "near_lossless": False,
            "diagnostics": [repr(Error)],
        }


def MainRun() -> int:
    Root = PathInfo(__file__).resolve().parents[3]
    Corpus = Root / ".rescratch" / "polyline"
    Cases = [f"poly5r{Index:03d}" for Index in range(1, 65)] if "--all" in System.argv[1:] else ["poly5a"]
    Records = []
    for Name in Cases:
        Source = Corpus / f"{Name}.SLDPRT"
        Neutral = Corpus / f"kit-five-source-{Name}.json"
        Target = Corpus / f"kit-{Name}.SLDPRT"
        Records.append(ConvertOne(Source, Neutral, Target))
    Failed = [
        Record
        for Record in Records
        if not (Record["vendor_loadable"] and Record["application_usable"] and Record["near_lossless"])
    ]
    print(JsonData.dumps({"records": len(Records), "passed": len(Records) - len(Failed), "failed": len(Failed), "failures": Failed}, indent=2))
    return 0 if not Failed else 1


if __name__ == "__main__":
    raise SystemExit(MainRun())
