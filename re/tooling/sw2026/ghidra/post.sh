#!/bin/bash
# post.sh proj program logname postScript args...  (arbitrary postScripts appended)
G=${SW26GH:?set SW26GH to a dot-free Ghidra work directory holding proj/ scripts/ out/ logs/}
export JAVA_HOME=${JAVA_HOME:-/opt/homebrew/opt/openjdk@21}
export GHIDRA_HEADLESS_MAXMEM=${MEM:-10G}
H=${GHIDRA_HEADLESS:-/opt/homebrew/Cellar/ghidra/12.1.3/libexec/support/analyzeHeadless}
proj=$1; prog=$2; log=$3; shift 3
"$H" $G/proj/$proj $proj -process $prog -noanalysis -scriptPath $G/scripts "$@" > $G/logs/$log.log 2>&1
echo "EXIT $?" >> $G/logs/$log.log
