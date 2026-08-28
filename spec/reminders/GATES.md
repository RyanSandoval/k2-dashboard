# Gates: Reminders section (K2 Dashboard)

OWNS: spec/reminders/**, index.html, ~/.openclaw/workspace/scripts/k2-cron-snapshot.sh, ~/.openclaw/workspace/scripts/reminder_queue_drain.py

Scope: A Reminders section in the K2 dashboard that lists every live reminder cron
(one-shot + recurring), and lets Ryan create, edit, snooze and cancel them from the
browser via a queue that a zero-model drain cron applies with the openclaw cron CLI.

- [x] G1: cron snapshot emits reminder text + schedule for reminder-shaped jobs
  CHECK: bash /Users/ryansandoval/k2-dashboard/spec/reminders/checks/g1_snapshot.sh
  EXPECT: G1 PASS
  EVIDENCE: exit=0; shell=/bin/sh; cwd=/Users/ryansandoval/k2-dashboard/spec/reminders; path=793cb2a96b74/13 entries; output=G1 PASS: 20 reminders via the real script (--emit), text+note+schedule present, non-reminders clean

- [x] G2: drainer plans correct CLI ops for create/update/cancel from a queue fixture
  CHECK: python3 /Users/ryansandoval/.openclaw/workspace/scripts/reminder_queue_drain.py --self-check
  EXPECT: G2 PASS
  EVIDENCE: exit=0; shell=/bin/sh; cwd=/Users/ryansandoval/k2-dashboard/spec/reminders; path=793cb2a96b74/13 entries; output=G2 PASS: create/update/snooze/cancel plan correct argv; payload is argv, not shell

- [x] G3: drainer is idempotent and rejects malformed input (bad cron expr, bad target, oversize text)
  CHECK: python3 /Users/ryansandoval/.openclaw/workspace/scripts/reminder_queue_drain.py --self-check-safety
  EXPECT: G3 PASS
  EVIDENCE: exit=0; shell=/bin/sh; cwd=/Users/ryansandoval/k2-dashboard/spec/reminders; path=793cb2a96b74/13 entries; output=G3 PASS: 13 malformed actions rejected, valid control accepted, applied ids skipped

- [x] G4: every inline script block in index.html still parses
  CHECK: node --experimental-vm-modules /Users/ryansandoval/k2-dashboard/spec/reminders/checks/g4_syntax.mjs
  EXPECT: G4 PASS
  EVIDENCE: exit=0; shell=/bin/sh; cwd=/Users/ryansandoval/k2-dashboard/spec/reminders; path=793cb2a96b74/13 entries; output=(node:88670) ExperimentalWarning: VM Modules is an experimental feature and might change at any time | (Use `node --trace-warnings ...` to show where the warning was created)

- [x] G5: headless browser renders the Reminders page from a stubbed snapshot — rows, groups, and the create form are present
  CHECK: python3 /Users/ryansandoval/k2-dashboard/spec/reminders/checks/g5_render.py
  EXPECT: G5 PASS
  EVIDENCE: exit=0; shell=/bin/sh; cwd=/Users/ryansandoval/k2-dashboard/spec/reminders; path=793cb2a96b74/13 entries; output=G5 PASS: reminders render + group + humanize, non-reminders excluded, create queues a valid action; mobile drawer entry navigates (screenshots: /tmp/g5_reminders.png, /tmp/g5_reminders_mobile.png)

- [x] G6: a real reminder created through the queue lands as a live cron job and is visible in the snapshot
  EVIDENCE: Ran live 2026-08-28: queued a create through DATA.reminderActions -> drainer produced cron 03f47baf-3781-4c7b-8758-e6c09660a4f1 with the right argv; queued an update carrying a 2-line note -> argv message became "⏰ Reminder: ...\nnote line one\nnote line two"; snapshot split it back into reminderText + reminderNote. Test cron removed and the queue cleared afterwards.
