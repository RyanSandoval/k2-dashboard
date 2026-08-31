#!/usr/bin/env python3
"""G7 — on a phone the note is the page. Before this pass the canvas was 407px sitting
under 91px of header and search and above 319px of suggestion cards, and the floating
search button covered the tab bar. Measured, because "it looks better" is what the last
two passes claimed while Ryan's phone looked identical."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from _boot import SNAP, b64, CHROME
from playwright.sync_api import sync_playwright

DATA = json.load(open("/tmp/k2data.json")); DATA["dailyDocs"] = {}

PROBE = r"""
() => {
  const R = s => { const e=document.querySelector(s); if(!e) return null;
    const r=e.getBoundingClientRect(); return {top:Math.round(r.top),h:Math.round(r.height),
      bottom:Math.round(r.bottom),w:Math.round(r.width)}; };
  const nav = document.querySelector('.mobile-nav').getBoundingClientRect();
  const fab = document.querySelector('.k2pal-mobile-fab');
  const picks=[...document.querySelectorAll('.home-pick')].map(e=>Math.round(e.getBoundingClientRect().height));
  const tap=[...document.querySelectorAll('.home-pick-do,.mobile-nav-item,.jot-search')]
    .map(e=>Math.round(e.getBoundingClientRect().height));
  return {
    vh: window.innerHeight,
    canvas: R('.daily-doc-editor'),
    start:  R('.home-start'),
    head:   R('.home-head'),
    search: R('.jot-search'),
    navTop: Math.round(nav.top),
    fabBottom: fab ? Math.round(fab.getBoundingClientRect().bottom) : null,
    fabVisible: fab ? getComputedStyle(fab).display !== 'none' : false,
    picks, minTap: tap.length ? Math.min(...tap) : null,
    hOverflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
  };
}
"""

def boot(pw, flag="1"):
    b = pw.chromium.launch(executable_path=CHROME)
    pg = b.new_context(viewport={"width": 390, "height": 844}, color_scheme="dark",
                       bypass_csp=True, is_mobile=True, has_touch=True).new_page()
    pg.route("https://api.github.com/**", lambda r: r.fulfill(
        status=200, content_type="application/json",
        body=json.dumps({"sha": "stub",
                         "content": b64(SNAP if "cron-snapshot" in r.request.url else DATA)})))
    pg.add_init_script("localStorage.setItem('k2auth','true');localStorage.setItem('gh_token','stub');"
                       f"localStorage.setItem('k2.ui2','{flag}');")
    pg.goto("file:///Users/ryansandoval/k2-dashboard/index.html")
    pg.wait_for_function("window._dataLoaded === true", timeout=30000)
    pg.wait_for_timeout(1500)
    return b, pg

def main():
    fails = []
    with sync_playwright() as pw:
        b, pg = boot(pw, "1"); a = pg.evaluate(PROBE); b.close()
        b, pg = boot(pw, "0"); off = pg.evaluate(PROBE); b.close()

    # 1. the floating button must not cover the tab bar
    if a["fabVisible"] and a["fabBottom"] is not None and a["fabBottom"] > a["navTop"]:
        fails.append(f'search button overlaps the tab bar by {a["fabBottom"]-a["navTop"]}px')

    # 2. the canvas is the page: more than everything above it, and more than the suggestions
    above = a["head"]["h"] + (a["search"]["h"] if a["search"] else 0)
    if a["canvas"]["h"] <= above:
        fails.append(f'canvas {a["canvas"]["h"]}px is not bigger than the {above}px of chrome above it')
    if a["start"] and a["canvas"]["h"] < a["start"]["h"] * 1.5:
        fails.append(f'canvas {a["canvas"]["h"]}px vs suggestions {a["start"]["h"]}px — suggestions still compete')
    if a["canvas"]["top"] > a["vh"] * 0.22:
        fails.append(f'canvas starts {a["canvas"]["top"]}px down a {a["vh"]}px screen — too much before the writing')

    # 3. it must actually be an improvement, not a claim
    if off["start"] and a["start"] and a["start"]["h"] >= off["start"]["h"]:
        fails.append(f'suggestions not compressed: {off["start"]["h"]}px -> {a["start"]["h"]}px')
    if a["canvas"]["h"] <= off["canvas"]["h"]:
        fails.append(f'canvas not grown: {off["canvas"]["h"]}px -> {a["canvas"]["h"]}px')

    # 4. nothing broke to get there
    if a["minTap"] is not None and a["minTap"] < 44:
        fails.append(f'smallest touch target is {a["minTap"]}px, under the 44px minimum')
    if a["hOverflow"] > 0:
        fails.append(f'page scrolls sideways by {a["hOverflow"]}px')

    if fails:
        print("G7 FAIL:\n  " + "\n  ".join(fails)); return 1
    print(f'G7 PASS: canvas {off["canvas"]["h"]} -> {a["canvas"]["h"]}px and starts {a["canvas"]["top"]}px in; '
          f'suggestions {off["start"]["h"]} -> {a["start"]["h"]}px ({len(a["picks"])} rows, tallest {max(a["picks"])}px); '
          f'{"search button clears the tab bar by %dpx" % (a["navTop"]-a["fabBottom"]) if a["fabVisible"] else "search button not shown on Today (G10: it covered a -> note button)"}; '
          f'smallest touch target {a["minTap"]}px; no sideways scroll')
    return 0

if __name__ == "__main__":
    sys.exit(main())
