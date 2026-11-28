#!/bin/bash
G=${SW26GH:?set SW26GH to a dot-free Ghidra work directory holding proj/ scripts/ out/ logs/}
export JAVA_HOME=${JAVA_HOME:-/opt/homebrew/opt/openjdk@21}
export GHIDRA_HEADLESS_MAXMEM=${MEM:-6G}
H=${GHIDRA_HEADLESS:-/opt/homebrew/Cellar/ghidra/12.1.3/libexec/support/analyzeHeadless}
proj=$1; prog=$2; out=$3; spec=$4; depth=$5
"$H" ${PROJ_ROOT:-$G/proj}/$proj $proj -process $prog -noanalysis -readOnly -scriptPath $G/scripts -postScript DumpArchiveClosure.java $out $spec $depth 240 > $G/logs/closure_$(basename $out).log 2>&1
echo "EXIT $?" >> $G/logs/closure_$(basename $out).log
