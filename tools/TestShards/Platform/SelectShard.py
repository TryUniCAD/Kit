import argparse as ArgParse
from pathlib import Path as FilePath

from tools.TestShards.AllocateTests import AllocateTests
from tools.TestShards.LoadHistory import LoadHistory


# platform runners need reproducible balanced selections without changing their complete collected roster
def MainRun() -> None:
    ParserInfo = ArgParse.ArgumentParser()
    _ = ParserInfo.add_argument(
        "--collected", type=FilePath, required=True, dest="CollectedPath"
    )
    _ = ParserInfo.add_argument(
        "--history", type=FilePath, required=True, dest="HistoryPath"
    )
    _ = ParserInfo.add_argument("--index", type=int, required=True, dest="ShardIndex")
    _ = ParserInfo.add_argument("--count", type=int, required=True, dest="ShardCount")
    _ = ParserInfo.add_argument(
        "--output", type=FilePath, required=True, dest="OutputPath"
    )
    ArgsInfo = ParserInfo.parse_args()
    TestIds = ArgsInfo.CollectedPath.read_text(encoding="utf-8").splitlines()
    if not 0 <= ArgsInfo.ShardIndex < ArgsInfo.ShardCount <= len(TestIds):
        ParserInfo.error("platform index and shard count must select nonempty shards")
    if len(set(TestIds)) != len(TestIds) or any(
        not TestId.strip() for TestId in TestIds
    ):
        ParserInfo.error("platform roster must contain unique nonempty node ids")
    History = LoadHistory(ArgsInfo.HistoryPath)
    Plans = AllocateTests(TestIds, History, len(TestIds), ArgsInfo.ShardCount)
    _ = ArgsInfo.OutputPath.write_text(
        "\n".join(Plans[ArgsInfo.ShardIndex].TestIds) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    MainRun()
