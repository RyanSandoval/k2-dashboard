#!/usr/bin/env bash
# G4 — the node must be defined AND registered in the editor's extension list AND styled.
# Defining it without registering it is the silent-failure shape: results parse in the
# writer's tests, then get dropped by the real editor.
set -uo pipefail
F=/Users/ryansandoval/k2-dashboard/index.html
FAIL=0
note() { echo "  $1"; FAIL=1; }

grep -q "name: 'agentResult'" "$F" || note "AgentResult node is not defined"
grep -q 'tag: .div\[data-type="agentResult"\]' "$F" || note "no parseHTML rule for the result node"
grep -qE '^\s+AgentResult,' "$F" || note "AgentResult is not in the createEditor extension list"
grep -q '\.agent-result {' "$F" || note "no styles for .agent-result"
grep -q '\.agent-result-label' "$F" || note "no styles for the result label"

# registration must sit inside the extensions array, not merely somewhere in the file
awk '/const extensions = \[/,/\];/' "$F" | grep -q 'AgentResult' || note "AgentResult is defined but not inside the extensions array"

# control: the same check must fail for a node that does not exist
awk '/const extensions = \[/,/\];/' "$F" | grep -q 'NotARealNode' && note "control: extension check matched a non-existent node"

node --experimental-vm-modules /Users/ryansandoval/k2-dashboard/spec/reminders/checks/g4_syntax.mjs >/dev/null 2>&1 || note "index.html no longer parses"

[ "$FAIL" -eq 0 ] || { echo "G4 FAIL:"; exit 1; }
echo "G4 PASS: node defined, parseHTML rule present, registered in the extension list, styled, file parses"
