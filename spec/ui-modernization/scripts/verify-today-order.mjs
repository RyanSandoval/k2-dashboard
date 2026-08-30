#!/usr/bin/env node
// Ryan, from his phone: "the writing of my note should be at the very top and the
// add thing (start here) should be below it." This pins that order so a later
// markup edit cannot quietly put the prompt back in front of the writing surface.
import { withApp, report } from './page.mjs';

const out = await withApp(page => page.evaluate(() => {
  navigateTo('jots');
  const order = [...document.querySelectorAll('#page-jots [id]')].map(e => e.id);
  const idx = id => order.indexOf(id);
  return {
    editorPresent: idx('daily-doc-today') > -1,
    startHerePresent: idx('home-start') > -1,
    editorBeforeStartHere: idx('daily-doc-today') < idx('home-start'),
    dateStaysOnTop: idx('jots-today-date') < idx('daily-doc-today'),
    dueStaysOnTop: idx('home-due') < idx('daily-doc-today'),
    _positions: { date: idx('jots-today-date'), due: idx('home-due'),
                  editor: idx('daily-doc-today'), startHere: idx('home-start') },
  };
}));
report(out, 'today-order-ok');
