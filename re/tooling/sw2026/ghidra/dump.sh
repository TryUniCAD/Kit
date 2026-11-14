#!/bin/bash
# dump.sh proj program outfile specfile depth max [extra postScripts...]
G=${SW26GH:?set SW26GH to a dot-free Ghidra work directory holding proj/ scripts/ out/ logs/}
export JAVA_HOME=${JAVA_HOME:-/opt/homebrew/opt/openjdk@21}
export GHIDRA_HEADLESS_MAXMEM=${MEM:-6G}
H=${GHIDRA_HEADLESS:-/opt/homebrew/Cellar/ghidra/12.1.3/libexec/support/analyzeHeadless}
proj=$1; prog=$2; out=$3; spec=$4; depth=$5; max=$6; shift 6
pre=""
if [ -n "$RENAME" ]; then pre="-postScript RenameArchiveApi.java"; fi
"$H" ${PROJ_ROOT:-$G/proj}/$proj $proj -process $prog -noanalysis -scriptPath $G/scripts $pre -postScript DumpFunctions.java $out $spec $depth $max "$@" > $G/logs/dump_$(basename $out).log 2>&1
echo "EXIT $?" >> $G/logs/dump_$(basename $out).log
