#!/bin/bash
# G5 — the editor is untouched. index.html holds a live TipTap editor with carry-forward,
# agent results and task retirement shipped into it today; a restyle that breaks any of
# them costs more than the design gains.
set -u
R=/Users/ryansandoval/k2-dashboard
fail=0
run() { out=$("$@" 2>&1); rc=$?; echo "$out" | tail -1; [ $rc -ne 0 ] && fail=1; }

echo "-- carry-forward --"
run node $R/spec/carry-forward/checks/g1_extract.mjs
run node $R/spec/carry-forward/checks/g2_once.mjs
run node $R/spec/carry-forward/checks/g3_safety.mjs
run python3 $R/spec/carry-forward/checks/g4_roundtrip.py
echo "-- agent results --"
run bash $R/spec/jot-results/checks/g4_registered.sh
echo "-- task retirement --"
run node $R/spec/task-retirement/checks/g1_selection.mjs
run node $R/spec/task-retirement/checks/g2_bulk.mjs
run node $R/spec/task-retirement/checks/g3_undo.mjs
run node $R/spec/task-retirement/checks/g4_wiring.mjs

if [ $fail -ne 0 ]; then echo "G5 FAIL: a previously-shipped suite regressed"; exit 1; fi
echo "G5 PASS: carry-forward 4/4, agent-result node registered, task-retirement 4/4 — all unchanged"
