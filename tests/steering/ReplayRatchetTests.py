from __future__ import annotations

import os as OsLib
import subprocess as Subprocess
import sys as System
import tempfile as Tempfile
import unittest as Unittest
from pathlib import Path as FilePath

KRepoRoot = FilePath(__file__).resolve().parents[2]

KAssertions = Unittest.TestCase()

KTableText = """KMethodProgram = (
    (0, 4, 1, "primitive:int", 7),
    (4, 8, 2, "primitive:double", float.fromhex("0x1.0p-1")),
)
"""

KGrownText = """KMethodProgram = (
    (0, 4, 1, "primitive:int", 7),
    (4, 8, 2, "primitive:double", float.fromhex("0x1.0p-1")),
    (12, 2, 3, "classref", 41),
)
"""

KProgramText = "EncodedData = ReplayResolved((), 0)\n"

KBalancedText = "src/family\tREP001\t2\nsrc/family\tREP002\t1\n"

KOtherText = "src/other\tREP001\t2\n"


def WriteTree(FolderPath: FilePath, TableText: str, BaselineText: str) -> None:
    MethodPath = FolderPath / "src" / "family" / "Methods" / "Table.py"
    MethodPath.parent.mkdir(parents=True)
    _ = MethodPath.write_text(TableText, encoding="utf-8")
    ProgramPath = FolderPath / "src" / "family" / "Program.py"
    _ = ProgramPath.write_text(KProgramText, encoding="utf-8")
    BaselinePath = FolderPath / "Baseline.txt"
    _ = BaselinePath.write_text(BaselineText, encoding="utf-8")


def WriteOther(FolderPath: FilePath) -> None:
    OtherPath = FolderPath / "src" / "other" / "Methods" / "Table.py"
    OtherPath.parent.mkdir(parents=True)
    _ = OtherPath.write_text(KTableText, encoding="utf-8")


def RunRatchet(
    FolderPath: FilePath, *ArgValues: str
) -> Subprocess.CompletedProcess[str]:
    EnvValues = {**OsLib.environ, "PYTHONPATH": str(KRepoRoot)}
    return Subprocess.run(
        [
            System.executable,
            "-m",
            "tools.Donors.CheckReplays",
            "--baseline-file",
            "Baseline.txt",
            *ArgValues,
        ],
        capture_output=True,
        text=True,
        check=False,
        cwd=FolderPath,
        env=EnvValues,
    )


def ReadBaseline(FolderPath: FilePath) -> str:
    return (FolderPath / "Baseline.txt").read_text(encoding="utf-8")


class TestBalanced(Unittest.TestCase):

    @staticmethod
    def CheckBalanced() -> None:
        CaseSelf = KAssertions
        with Tempfile.TemporaryDirectory() as TmpPath:
            FolderPath = FilePath(TmpPath)
            WriteTree(FolderPath, KTableText, KBalancedText)
            ResultInfo = RunRatchet(FolderPath, "src")
        CaseSelf.assertEqual(
            ResultInfo.returncode, 0, ResultInfo.stdout + ResultInfo.stderr
        )
        CaseSelf.assertIn("2 recorded field operations", ResultInfo.stdout)


class TestAliases(Unittest.TestCase):

    @staticmethod
    def CheckAliases() -> None:
        CaseSelf = KAssertions
        with Tempfile.TemporaryDirectory() as TmpPath:
            FolderPath = FilePath(TmpPath)
            WriteTree(FolderPath, KTableText, KBalancedText)
            TablePath = FolderPath / "src" / "family" / "Methods" / "Table.py"
            ResultInfo = RunRatchet(FolderPath, "src", str(TablePath.resolve()))
        CaseSelf.assertEqual(
            ResultInfo.returncode, 0, ResultInfo.stdout + ResultInfo.stderr
        )


class TestGrowth(Unittest.TestCase):

    @staticmethod
    def CheckGrowth() -> None:
        CaseSelf = KAssertions
        with Tempfile.TemporaryDirectory() as TmpPath:
            FolderPath = FilePath(TmpPath)
            WriteTree(FolderPath, KGrownText, KBalancedText)
            ResultInfo = RunRatchet(FolderPath, "src")
            UpdateInfo = RunRatchet(FolderPath, "--update-baseline", "src")
            BaselineText = ReadBaseline(FolderPath)
        CaseSelf.assertEqual(ResultInfo.returncode, 1)
        CaseSelf.assertIn("grew from 2 to 3", ResultInfo.stdout)
        CaseSelf.assertEqual(UpdateInfo.returncode, 1)
        CaseSelf.assertEqual(BaselineText, KBalancedText)


class TestNewRoot(Unittest.TestCase):

    @staticmethod
    def CheckNewRoot() -> None:
        CaseSelf = KAssertions
        with Tempfile.TemporaryDirectory() as TmpPath:
            FolderPath = FilePath(TmpPath)
            WriteTree(FolderPath, KTableText, KBalancedText)
            WriteOther(FolderPath)
            ResultInfo = RunRatchet(FolderPath, "src")
        CaseSelf.assertEqual(ResultInfo.returncode, 1)
        CaseSelf.assertIn("src/other: REP001", ResultInfo.stdout)
        CaseSelf.assertIn("are new (2)", ResultInfo.stdout)


class TestShrink(Unittest.TestCase):

    @staticmethod
    def CheckShrink() -> None:
        CaseSelf = KAssertions
        LooseText = KBalancedText.replace("REP001\t2", "REP001\t5")
        with Tempfile.TemporaryDirectory() as TmpPath:
            FolderPath = FilePath(TmpPath)
            WriteTree(FolderPath, KTableText, LooseText)
            ResultInfo = RunRatchet(FolderPath, "src")
            UpdateInfo = RunRatchet(FolderPath, "--update-baseline", "src")
            FinalInfo = RunRatchet(FolderPath, "src")
            BaselineText = ReadBaseline(FolderPath)
        CaseSelf.assertEqual(ResultInfo.returncode, 1)
        CaseSelf.assertIn("fell from 5 to 2", ResultInfo.stdout)
        CaseSelf.assertEqual(UpdateInfo.returncode, 0, UpdateInfo.stderr)
        CaseSelf.assertEqual(FinalInfo.returncode, 0, FinalInfo.stderr)
        CaseSelf.assertTrue(BaselineText.endswith(KBalancedText))


class TestPartial(Unittest.TestCase):

    @staticmethod
    def CheckPartial() -> None:
        CaseSelf = KAssertions
        LooseText = (KBalancedText + KOtherText).replace("REP001\t2", "REP001\t5")
        with Tempfile.TemporaryDirectory() as TmpPath:
            FolderPath = FilePath(TmpPath)
            WriteTree(FolderPath, KTableText, LooseText)
            WriteOther(FolderPath)
            UpdateInfo = RunRatchet(FolderPath, "--update-baseline", "src/family")
            MethodInfo = RunRatchet(
                FolderPath, "--update-baseline", "src/other/Methods"
            )
            PartialText = ReadBaseline(FolderPath)
            FinalInfo = RunRatchet(FolderPath, "--update-baseline", "src")
            BaselineText = ReadBaseline(FolderPath)
        CaseSelf.assertEqual(UpdateInfo.returncode, 0, UpdateInfo.stderr)
        CaseSelf.assertEqual(MethodInfo.returncode, 0, MethodInfo.stderr)
        CaseSelf.assertIn("src/family\tREP001\t2\n", PartialText)
        CaseSelf.assertIn("src/other\tREP001\t5\n", PartialText)
        CaseSelf.assertEqual(FinalInfo.returncode, 0, FinalInfo.stderr)
        CaseSelf.assertTrue(BaselineText.endswith(KBalancedText + KOtherText))


class TestInputs(Unittest.TestCase):

    @staticmethod
    def CheckInputs() -> None:
        CaseSelf = KAssertions
        with Tempfile.TemporaryDirectory() as TmpPath:
            FolderPath = FilePath(TmpPath)
            WriteTree(FolderPath, KTableText, "src/family\tREP001\n")
            MalformedInfo = RunRatchet(FolderPath, "src")
            WriteTree(FolderPath / "unknown", KTableText, "src/family\tREP01\t2\n")
            UnknownInfo = RunRatchet(FolderPath / "unknown", "src")
            (FolderPath / "Baseline.txt").unlink()
            MissingInfo = RunRatchet(FolderPath, "src")
        CaseSelf.assertEqual(MalformedInfo.returncode, 2)
        CaseSelf.assertEqual(UnknownInfo.returncode, 2)
        CaseSelf.assertIn("unknown baseline rule", UnknownInfo.stderr)
        CaseSelf.assertEqual(MissingInfo.returncode, 2)
