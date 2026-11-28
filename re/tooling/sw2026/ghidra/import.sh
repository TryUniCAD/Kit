#!/bin/bash
G=${SW26GH:?set SW26GH to a dot-free Ghidra work directory holding proj/ scripts/ out/ logs/}
BIN=${SW26BIN:?set SW26BIN to the folder of copied SOLIDWORKS 2026 DLLs}
export JAVA_HOME=${JAVA_HOME:-/opt/homebrew/opt/openjdk@21}
H=${GHIDRA_HEADLESS:-/opt/homebrew/Cellar/ghidra/12.1.3/libexec/support/analyzeHeadless}
name=$1; mem=$2; shift 2
export GHIDRA_HEADLESS_MAXMEM=$mem
start=$(date +%s)
"$H" $G/proj/$name $name $(for f in "$@"; do echo -import $BIN/$f; done) -scriptPath $G/scripts -analysisTimeoutPerFile 21600 -max-cpu 6 > $G/logs/import_$name.log 2>&1
echo "EXIT $? ELAPSED $(( $(date +%s) - start ))" >> $G/logs/import_$name.log
