#!/usr/bin/env python3
"""G10 — nothing floats on top of anything. Ryan photographed his phone: the Attach button
sat across the placeholder line, the search button covered a "-> note" button he could not
tap, and the START HERE card ran under the tab bar. All three are the same class of defect —
a fixed or absolute control sharing pixels with something it is not allowed to cover — so
this measures the class, not the three instances. Checked at the top of the page and again
scrolled to the end, because the resting state at the bottom is where the FAB parks."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from _boot import SNAP, b64, CHROME
from playwright.sync_api import sync_playwright

DATA = json.load(open("/tmp/k2data.json"))

PROBE = r"""
() => {
  const vis = e => { const s=getComputedStyle(e), r=e.getBoundingClientRect();
    return s.display!=='none' && s.visibility!=='hidden' && +s.opacity>0.05
           && r.width>0 && r.height>0; };
  const box = e => { const r=e.getBoundingClientRect();
    return {t:Math.round(r.top),l:Math.round(r.left),b:Math.round(r.bottom),
            r:Math.round(r.right),w:Math.round(r.width),h:Math.round(r.height)}; };
  const name = e => (e.getAttribute('aria-label') || e.className || e.tagName) + '';

  // Floating controls: positioned out of flow and small enough to be a control rather than
  // a layer. The tab bar itself is excluded by the width test (it spans the viewport) —
  // content is allowed to scroll *behind* it, it just may not come to rest under it, which
  // is the separate check below.
  const onScreen = r => r.top < innerHeight && r.bottom > 0 && r.left < innerWidth && r.right > 0;
  const floats = [...document.querySelectorAll('body *')].filter(e => {
    const s = getComputedStyle(e);
    return (s.position === 'fixed' || s.position === 'absolute') && vis(e)
           && e.getBoundingClientRect().width < 300
           && onScreen(e.getBoundingClientRect())
           // The tab bar is a sanctioned overlay: content is allowed to scroll behind it,
           // so its own children are not "floating on top of" what passes underneath.
           && !e.closest('.mobile-nav')
           // A closed drawer is transform-parked off-screen. It still has a box and still
           // reports display:block, so without this every drawer row reads as a collision.
           && !(e.closest('.mobile-more-drawer') && !e.closest('.mobile-more-drawer.open'));
  });

  // What a control may not cover: rendered text, and anything tappable.
  const targets = [...document.querySelectorAll('#page-jots *, .mobile-nav *')].filter(e =>
    vis(e) && (
      (e.children.length === 0 && (e.textContent||'').trim().length > 1) ||
      e.matches('button, a, input, [onclick]')
    ));

  const hits = [];
  for (const f of floats) {
    const a = box(f);
    for (const t of targets) {
      if (f === t || f.contains(t) || t.contains(f)) continue;
      const c = box(t);
      if (!onScreen(t.getBoundingClientRect())) continue;
      const ox = Math.min(a.r, c.r) - Math.max(a.l, c.l);
      const oy = Math.min(a.b, c.b) - Math.max(a.t, c.t);
      if (ox > 2 && oy > 2)
        hits.push({ f: name(f).slice(0,34), over: (t.textContent||'').trim().slice(0,34)
                    || name(t).slice(0,34), ox, oy });
    }
  }

  // The editor placeholder is a ::before, so it is not a DOM node and the sweep above
  // cannot see it. Check the writing surface's first line explicitly.
  // The block's own rect is always full-width, so comparing boxes cannot tell "the text
  // was displaced" from "the text is covered" — the fix would read as failing forever.
  // Measure where the glyphs actually are: Range rects when the line has text, and the
  // padding box when it is empty, because that is the strip the placeholder ::before is
  // laid out in and a ::before has no node to measure.
  const pm = document.querySelector('#page-jots .ProseMirror');
  const first = pm && pm.firstElementChild;
  const att = document.querySelector('#page-jots .note-attach-bar');
  let firstLine = null;
  if (first && att && vis(att)) {
    const a = box(att);
    let c;
    if ((first.textContent || '').trim()) {
      const rg = document.createRange(); rg.selectNodeContents(first);
      const rects = [...rg.getClientRects()];
      const top = rects.length ? rects[0] : first.getBoundingClientRect();
      c = {t:Math.round(top.top), l:Math.round(top.left),
           b:Math.round(top.bottom), r:Math.round(top.right)};
    } else {
      // The placeholder is a ::before, so it has no node and no client rect. It is also
      // absolutely positioned in ui2, which means it escapes the parent's padding — the
      // padding box would say "clear" while the glyphs run under the button. Chrome
      // returns USED values for a pseudo-element's box, so build its real rect from those.
      const pb = getComputedStyle(first, '::before'), r = first.getBoundingClientRect();
      const cs = getComputedStyle(first);
      const l = r.left + parseFloat(cs.paddingLeft) + (parseFloat(pb.left) || 0);
      c = {t: Math.round(r.top), l: Math.round(l),
           b: Math.round(r.top + (parseFloat(pb.height) || 0)),
           r: Math.round(l + (parseFloat(pb.width) || 0))};
    }
    firstLine = { ox: Math.min(a.r,c.r)-Math.max(a.l,c.l),
                  oy: Math.min(a.b,c.b)-Math.max(a.t,c.t),
                  empty: !(first.textContent||'').trim() };
  }

  const nav = document.querySelector('.mobile-nav').getBoundingClientRect();
  const scroller = document.querySelector('.main');
  const atEnd = scroller.scrollTop >= scroller.scrollHeight - scroller.clientHeight - 2;
  // content that has come to REST under the tab bar (only meaningful at the end of scroll)
  const resting = [...document.querySelectorAll('#page-jots .home-start, #page-jots .home-pick, '
      + '#page-jots .home-pick *, #page-jots .daily-doc-editor')]
    .filter(e => vis(e)).map(e => ({ el: name(e).slice(0,24), b: box(e).b }))
    .filter(o => o.b > Math.round(nav.top));

  return { hits, firstLine, atEnd, resting, navTop: Math.round(nav.top),
           fab: (()=>{const f=document.querySelector('.k2pal-mobile-fab');
                 return f && vis(f) ? box(f) : null;})() };
}
"""

def boot(pw):
    b = pw.chromium.launch(executable_path=CHROME)
    pg = b.new_context(viewport={"width": 390, "height": 844}, color_scheme="dark",
                       bypass_csp=True, is_mobile=True, has_touch=True).new_page()
    pg.route("https://api.github.com/**", lambda r: r.fulfill(
        status=200, content_type="application/json",
        body=json.dumps({"sha": "stub",
                         "content": b64(SNAP if "cron-snapshot" in r.request.url else DATA)})))
    pg.add_init_script("localStorage.setItem('k2auth','true');localStorage.setItem('gh_token','stub');"
                       "localStorage.setItem('k2.ui2','1');")
    pg.goto("file:///Users/ryansandoval/k2-dashboard/index.html")
    pg.wait_for_function("window._dataLoaded === true", timeout=30000)
    pg.wait_for_timeout(1500)
    return b, pg

def main():
    fails = []
    with sync_playwright() as pw:
        b, pg = boot(pw)
        top = pg.evaluate(PROBE)
        pg.evaluate("() => { const m=document.querySelector('.main'); m.scrollTop = m.scrollHeight; }")
        pg.wait_for_timeout(500)
        end = pg.evaluate(PROBE)
        b.close()

    for where, s in (("at rest", top), ("scrolled to the end", end)):
        for h in s["hits"]:
            fails.append(f'{where}: "{h["f"]}" covers "{h["over"]}" by {h["ox"]}x{h["oy"]}px')

    if top["firstLine"] and top["firstLine"]["ox"] > 2 and top["firstLine"]["oy"] > 2:
        fails.append(f'Attach sits across the first line of the note by '
                     f'{top["firstLine"]["ox"]}x{top["firstLine"]["oy"]}px')

    if not end["atEnd"]:
        fails.append("could not scroll the page to its end — the scroller is not <main>")
    for r in end["resting"]:
        fails.append(f'{r["el"]} comes to rest {r["b"]-end["navTop"]}px under the tab bar')

    if fails:
        print("G10 FAIL:\n  " + "\n  ".join(sorted(set(fails)))); return 1
    print(f'G10 PASS: no floating control overlaps text or a touch target, at rest or at the '
          f'end of scroll; Attach clears the first line; nothing rests under the {end["navTop"]}px '
          f'tab bar; search button {"parked at " + str(end["fab"]["t"]) + "px" if end["fab"] else "hidden"}')
    return 0

if __name__ == "__main__":
    sys.exit(main())
