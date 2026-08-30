#!/usr/bin/env node
// No colour may bypass the token system, and text on the accent must be readable.
// Both were violated: 81 hex values never went through :root, --blue was never
// defined at all, and the same accent background carried black text in some places
// and white in others on a colour where only one of those is legible.
import { readFileSync } from 'node:fs';
import { withApp, report } from './page.mjs';

const src = readFileSync('/Users/ryansandoval/k2-dashboard/index.html', 'utf8');
// Hex was not the only way out of the token system: rgba() and hsl() bypass it too,
// which is how a raw rgba(0,0,0,0.7) scrim survived the first pass unnoticed.
const literal = /(#[0-9a-fA-F]{3,8}\b|\brgba?\(\s*\d|\bhsla?\(\s*\d)/;
const inlineStyles = src.match(/style="[^"]*"/g) || [];
const rawColours = inlineStyles.filter(a => literal.test(a));
const hexInInline = rawColours.length;
const undefinedVars = [...new Set((src.match(/var\(--[a-z0-9-]+/g) || [])
  .map(v => v.slice(4)))]
  .filter(v => !new RegExp(`(^|[;{\\s])${v}\\s*:`, 'm').test(src));

const out = await withApp(page => page.evaluate(() => {
  // Relative luminance per WCAG 2.x, from whatever the browser computed.
  // Chrome keeps oklch() all the way through getComputedStyle and canvas fillStyle,
  // so there is no string to parse. Paint the colour and read the pixel back — that
  // is the only value that is definitely what lands on screen.
  const ctx = document.createElement('canvas').getContext('2d', { willReadFrequently: true });
  const toRGB = (css) => {
    ctx.clearRect(0, 0, 1, 1);
    ctx.fillStyle = css;
    ctx.fillRect(0, 0, 1, 1);
    return [...ctx.getImageData(0, 0, 1, 1).data].slice(0, 3);
  };
  const lum = (css) => {
    const [r, g, b] = toRGB(css)
      .map(c => { c /= 255; return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4; });
    return 0.2126 * r + 0.7152 * g + 0.0722 * b;
  };
  const ratio = (a, b) => {
    const [hi, lo] = [lum(a), lum(b)].sort((x, y) => y - x);
    return Math.round(((hi + 0.05) / (lo + 0.05)) * 100) / 100;
  };
  const css = getComputedStyle(document.documentElement);
  const probe = (bgVar, fgVar) =>
    ratio(css.getPropertyValue(bgVar).trim(), css.getPropertyValue(fgVar).trim());
  return {
    accentOnBgRatio: probe('--bg', '--accent'),
    textOnAccentRatio: probe('--accent', '--bg'),
    yellowOnSurfaceRatio: probe('--surface2', '--yellow'),
  };
}));

report({
  noRawColoursInInlineStyles: hexInInline === 0,
  rawColourCount: hexInInline,
  rawColourSample: rawColours.slice(0, 3).map(a => a.slice(0, 90)),
  everyVarDefined: undefinedVars.length === 0,
  undefinedVars,
  // 4.5:1 is WCAG AA for body text. Buttons carry labels, so they need to clear it.
  textOnAccentReadable: out.textOnAccentRatio >= 4.5,
  ...out,
}, 'palette-ok');
