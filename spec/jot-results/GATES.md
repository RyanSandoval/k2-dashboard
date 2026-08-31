# Gates: agent results written back into the daily note

OWNS: spec/jot-results/**, index.html, ~/.openclaw/workspace/scripts/jot_result_writer.py

Scope: when a 🤖 mention in a jot causes something to happen, the result appears in the
note under the line that caused it — not on a page Ryan never opens. Covers the TipTap
node so results survive editing, the writer that inserts them, and the guarantee that
writing into a daily note can never damage what Ryan wrote.

- [x] G1: the writer inserts a result under the right line, is idempotent, and preserves every word Ryan wrote
  CHECK: python3 /Users/ryansandoval/.openclaw/workspace/scripts/jot_result_writer.py --self-check
  EXPECT: G1 PASS
  EVIDENCE: exit=0; shell=/bin/sh; cwd=/Users/ryansandoval/k2-dashboard/spec/jot-results; path=af8e72e0c344/13 entries; output=G1 PASS: result lands under its own line, idempotent on re-run, every word of the note preserved (incl. unicode and multiple mentions)

- [x] G2: the writer refuses to write when it cannot prove the note survived intact
  CHECK: python3 /Users/ryansandoval/.openclaw/workspace/scripts/jot_result_writer.py --self-check-safety
  EXPECT: G2 PASS
  EVIDENCE: exit=0; shell=/bin/sh; cwd=/Users/ryansandoval/k2-dashboard/spec/jot-results; path=af8e72e0c344/13 entries; output=G2 PASS: 8 bad inputs refused, valid control accepted, verify() catches dropped/altered/truncated/duplicated content, markup escaped

- [x] G3: TipTap round-trips the result node — loading a note with results and saving it back does not drop or mangle them
  CHECK: python3 /Users/ryansandoval/k2-dashboard/spec/jot-results/checks/g3_roundtrip.py
  EXPECT: G3 PASS
  EVIDENCE: exit=0; shell=/bin/sh; cwd=/Users/ryansandoval/k2-dashboard/spec/jot-results; path=af8e72e0c344/13 entries; output=G3 PASS: TipTap parses and re-serializes the result node intact, inside its task item

- [x] G4: index.html still parses and the result node is registered in the editor's extension list
  CHECK: bash /Users/ryansandoval/k2-dashboard/spec/jot-results/checks/g4_registered.sh
  EXPECT: G4 PASS
  EVIDENCE: exit=0; shell=/bin/sh; cwd=/Users/ryansandoval/k2-dashboard/spec/jot-results; path=af8e72e0c344/13 entries; output=G4 PASS: node defined, parseHTML rule present, registered in the extension list, styled, file parses

- [x] G5: a real result written into today's live note renders under its line and the note is unharmed
  EVIDENCE: Written live into today's note 2026-08-28 under req a-mtdhvwd8-2n8x. Snapshot taken first; after the write his text was byte-identical (verified by tag-stripped comparison), exactly one result node present, and all 136 daily notes intact. Node deployed to Pages before any edit could strip it (sw v54).
