#!/usr/bin/env node
// The reminders page had two controls whose active state lived in JS as inline style
// writes — six per click on the mode toggle, four per pill on every render. Both are
// aria-pressed now, so this checks the state still lands AND still looks different.
import { withApp, report } from './page.mjs';

const out = await withApp(page => page.evaluate(() => {
  navigateTo('reminders');
  const px = (() => {
    const ctx = document.createElement('canvas').getContext('2d', { willReadFrequently: true });
    return (c) => { ctx.clearRect(0,0,1,1); ctx.fillStyle = c; ctx.fillRect(0,0,1,1);
      return [...ctx.getImageData(0,0,1,1).data].slice(0,3).join(); };
  })();
  const o = {};

  const once = document.getElementById('rem-mode-once');
  const rep = document.getElementById('rem-mode-repeat');
  setReminderMode('once');
  o.oncePressed = once.getAttribute('aria-pressed') === 'true';
  const onceBg = px(getComputedStyle(once).backgroundColor);
  const repBg = px(getComputedStyle(rep).backgroundColor);
  // aria-pressed without a visible difference is a state nobody can see.
  o.modeLooksDifferent = onceBg !== repBg;
  o.onceFieldsShown = getComputedStyle(document.getElementById('rem-once-fields')).display !== 'none';
  setReminderMode('repeat');
  o.repeatPressed = rep.getAttribute('aria-pressed') === 'true';
  o.onceUnpressed = once.getAttribute('aria-pressed') === 'false';
  o.repeatFieldsShown = getComputedStyle(document.getElementById('rem-repeat-fields')).display !== 'none';
  o.onceFieldsHidden = getComputedStyle(document.getElementById('rem-once-fields')).display === 'none';

  setReminderFilter('asked');
  const pills = [...document.querySelectorAll('#rem-filters button')];
  const on = pills.find(b => b.dataset.remfilter === 'asked');
  const off = pills.find(b => b.dataset.remfilter === 'all');
  o.filterPressed = on.getAttribute('aria-pressed') === 'true';
  o.filterLooksDifferent = px(getComputedStyle(on).backgroundColor) !==
                           px(getComputedStyle(off).backgroundColor);

  // outline:none with nothing in its place left keyboard users with no focus ring.
  const field = document.getElementById('rem-text');
  field.focus();
  o.fieldHasFocusIndicator = getComputedStyle(field).boxShadow !== 'none' ||
    px(getComputedStyle(field).borderTopColor) !==
    px(getComputedStyle(document.getElementById('rem-at')).borderTopColor);

  o.fieldsStyled = getComputedStyle(field).paddingLeft === '12px';
  return o;
}));

report(out, 'reminders-ok');
