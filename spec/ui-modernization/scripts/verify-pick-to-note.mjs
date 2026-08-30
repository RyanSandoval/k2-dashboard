#!/usr/bin/env node
// Ryan: "I added a Start here item and I closed the task. It's still showing in the
// list below and I bet it's duplicating and not closing the original task too."
// He was right on both counts. This pins the round trip: the note line carries the
// task id, ticking it closes the real task, and pressing the button twice does not
// make a second copy.
import { withApp, report } from './page.mjs';

const out = await withApp(async (page) => {
  // The editor is Tiptap loading from a CDN module, so give it a moment to mount.
  await page.evaluate(() => navigateTo('jots'));
  await page.waitForFunction(() => !!window._todayEditor, { timeout: 20000 });

  return page.evaluate(async () => {
    const o = {};
    const ed = window._todayEditor;
    const pick = homeTopPicks(1)[0];
    o.hasAPick = !!pick;
    const task = DATA.tasks.find(t => String(t.id) === String(pick.id));
    o.taskStartsOpen = !task.done;

    const countLinked = () => {
      let n = 0;
      ed.state.doc.descendants(node => {
        if (node.type.name === 'taskItem' && String(node.attrs.taskId) === String(pick.id)) n++;
      });
      return n;
    };

    homePickToNote(pick.id);
    o.insertedOnce = countLinked() === 1;
    // The link is the whole fix: without it the note line is just text.
    o.lineCarriesTaskId = countLinked() === 1;

    // Pressing it again must not add a second copy.
    homePickToNote(pick.id);
    o.noDuplicateOnSecondPress = countLinked() === 1;

    // Tick the note line the way the app does — dispatch and let onUpdate run — so
    // this proves the editor is wired to the sync, not merely that the sync works.
    // The first version of this test called syncNoteChecksToTasks() itself and
    // passed happily with the onUpdate hook deleted.
    const findPos = () => {
      let pos = null;
      ed.state.doc.descendants((node, p) => {
        if (node.type.name === 'taskItem' && String(node.attrs.taskId) === String(pick.id)) pos = p;
      });
      return pos;
    };
    const setChecked = (v) => {
      const pos = findPos();
      if (pos === null) return false;
      ed.view.dispatch(ed.state.tr.setNodeMarkup(pos, undefined,
        { ...ed.state.doc.nodeAt(pos).attrs, checked: v }));
      return true;
    };
    const settle = () => new Promise(r => setTimeout(r, 400));

    o.lineFound = setChecked(true);
    await settle();
    o.tickingNoteClosesTask = !!DATA.tasks.find(t => String(t.id) === String(pick.id)).done;

    // And it stops being offered back.
    o.dropsOutOfStartHere = !homeTopPicks(5).some(p => String(p.id) === String(pick.id));

    // Unticking reopens it, so the link works both ways.
    setChecked(false);
    await settle();
    o.untickingReopensTask = !DATA.tasks.find(t => String(t.id) === String(pick.id)).done;
    return o;
  });
});

report(out, 'pick-to-note-ok');
