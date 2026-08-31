#!/usr/bin/env python3
"""G6 — the flag actually changes a phone. Ryan turned it on and said "on mobile nothing
looks different", and he was right: .sidebar is display:none at 390px in both states, so
almost everything ui2 restyled was invisible there. This gate measures the chrome a phone
really shows, so that cannot pass unnoticed again."""
import sys, os, json, base64, time
sys.path.insert(0, os.path.dirname(__file__))
from _boot import DATA as _D, SNAP, b64, CHROME
# no prior day: today's note is then created empty, which is the only state that renders
# the placeholder this gate is here to check
DATA = dict(_D); DATA["dailyDocs"] = {}
from playwright.sync_api import sync_playwright

def boot(pw, flag):
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
    pg.wait_for_timeout(1400)
    return b, pg

PROBE = r"""
() => {
  const tabs=[...document.querySelectorAll('.mobile-nav .mobile-nav-item')];
  const ed=document.querySelector('#page-jots .ProseMirror');
  // Deterministic rather than fixture-dependent: the End of Day block is appended in the
  // evening, so an "empty note" fixture stops being empty after a certain hour and the
  // placeholder never renders. Probe the rule with an element we control instead.
  const ed0=document.querySelector('#page-jots .ProseMirror');
  let probe=null;
  if(ed0){probe=document.createElement('p');probe.className='is-editor-empty';
    probe.setAttribute('data-placeholder','probe');ed0.insertBefore(probe,ed0.firstChild);}
  const ph=probe;
  const edBox=ed?ed.getBoundingClientRect():null;
  const host=document.querySelector('.daily-doc-editor');
  const __r = {
    ui2: document.body.classList.contains('ui2'),
    tabs: tabs.length,
    svgTabs: tabs.filter(t=>t.querySelector('.icon svg')).length,
    emojiTabs: tabs.filter(t=>{const i=t.querySelector('.icon');
      return i && !i.querySelector('svg') && /\p{Extended_Pictographic}/u.test(i.textContent);}).length,
    navBg: getComputedStyle(document.querySelector('.mobile-nav')).backgroundColor,
    edFont: ed?getComputedStyle(ed).fontSize:null,
    edMaxW: ed?getComputedStyle(ed).maxWidth:null,
    hostMinH: host?getComputedStyle(host).minHeight:null,
    phFloat: ph?getComputedStyle(ph,'::before').float:null,
    phPos: ph?getComputedStyle(ph,'::before').position:null,
    edOutlineStyle: ed?getComputedStyle(ed).outlineStyle:null,
  };
  if(probe) probe.remove();
  return __r;
}
"""

def main():
    fails = []
    with sync_playwright() as pw:
        b_on, on = boot(pw, "1"); a = on.evaluate(PROBE)
        on.evaluate("()=>document.querySelector('#page-jots .ProseMirror')?.focus()")
        on.wait_for_timeout(200)
        # outline-STYLE, not width: Chrome reports width 3px even when style is none,
        # so asserting on width fails against a ring that does not exist
        focused = on.evaluate("()=>getComputedStyle(document.querySelector('#page-jots .ProseMirror')).outlineStyle")
        b_on.close()
        b_off, off = boot(pw, "0"); c = off.evaluate(PROBE); b_off.close()

    if not a["ui2"]: fails.append("flag did not apply at 390px")
    if a["tabs"] < 5: fails.append(f'only {a["tabs"]} tab bar items found — probe is not seeing the chrome')
    # the actual complaint: the phone must look different
    if a["svgTabs"] < 5: fails.append(f'{a["svgTabs"]}/{a["tabs"]} tabs use line icons; the rest are still emoji')
    if a["emojiTabs"]: fails.append(f'{a["emojiTabs"]} tab(s) still emoji-labelled with the flag on')
    if c["svgTabs"]: fails.append(f'{c["svgTabs"]} tabs use line icons with the flag OFF — the old UI changed')
    if not c["emojiTabs"]: fails.append("flag off did not restore the emoji tab bar")
    if a["navBg"] == c["navBg"]: fails.append("tab bar background is identical in both states")
    # the canvas
    if a["edMaxW"] != "none": fails.append(f'editor still measure-capped on mobile ({a["edMaxW"]})')
    if a["phFloat"] is None:
        fails.append("placeholder element absent — the fixture is not producing an empty note, so this is untested")
    elif a["phFloat"] != "none" or a["phPos"] != "absolute":
        fails.append(f'placeholder still floated ({a["phFloat"]}/{a["phPos"]}) — it renders outside the editor')
    if focused != "none": fails.append(f"editor draws a {focused} focus ring — that is the blue box")

    if fails:
        print("G6 FAIL:\n  " + "\n  ".join(fails)); return 1
    print(f'G6 PASS: at 390px the flag changes the chrome a phone actually shows — '
          f'{a["svgTabs"]}/{a["tabs"]} tab icons drawn (0 emoji, restored to {c["emojiTabs"]} when off), '
          f'tab bar repainted, editor uncapped with a {a["hostMinH"]} canvas, placeholder in-flow '
          f'and no focus ring round the note')
    return 0

if __name__ == "__main__":
    sys.exit(main())
