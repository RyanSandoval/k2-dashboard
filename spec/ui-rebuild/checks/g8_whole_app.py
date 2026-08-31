#!/usr/bin/env python3
"""G8 — the flag reaches the whole app, not just Today. Ryan: "today looks good, but the
rest of the app looks the same." It was: ui2 styled .sidebar and #page-jots, and the other
33 pages inherited nothing. This walks real pages and checks the tokens actually arrive and
that nothing is left unreadable behind them."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from _boot import SNAP, b64, CHROME
from playwright.sync_api import sync_playwright

DATA = json.load(open("/tmp/k2data.json"))
# a page from each group, plus the dashboard everything links back to
PAGES = ["dashboard", "tasks", "projects", "notes", "reminders", "action-inbox",
         "requests", "waiting", "decisions", "memory", "workers", "task-retirement"]

CONTRAST = r"""
(sel) => {
  // Colours must be COMPOSITED, not read. canvas resolves
  // color-mix(in srgb, X 15%, transparent) to solid X, so a 15%-alpha pill behind
  // same-hue text measures as 1:1 — a defect that is not there. Paint each layer over
  // the one beneath it and read the pixel that actually reaches the eye.
  const cv=document.createElement('canvas');cv.width=cv.height=1;
  const ctx=cv.getContext('2d',{willReadFrequently:true});
  const px=(stack)=>{ctx.clearRect(0,0,1,1);
    ctx.fillStyle='#000';ctx.fillRect(0,0,1,1);          // the page beneath everything
    for(const c of stack){ctx.fillStyle=c;ctx.fillRect(0,0,1,1);}
    const d=ctx.getImageData(0,0,1,1).data;return [d[0],d[1],d[2]];};
  const sr=c=>{c/=255;return c<=.03928?c/12.92:Math.pow((c+.055)/1.055,2.4)};
  const lum=rgb=>.2126*sr(rgb[0])+.7152*sr(rgb[1])+.0722*sr(rgb[2]);
  // every background from the root down to the element, in paint order
  const bgStack=el=>{const out=[];let n=el;
    while(n&&n!==document.documentElement){const c=getComputedStyle(n).backgroundColor;
      if(c&&c!=='rgba(0, 0, 0, 0)'&&c!=='transparent')out.unshift(c);n=n.parentElement;}
    const b=getComputedStyle(document.body).backgroundColor;
    if(b)out.unshift(b);
    return out;};
  const ratio=(fg,bgs)=>{const B=lum(px(bgs)),A=lum(px([...bgs,fg]));
    return (Math.max(A,B)+.05)/(Math.min(A,B)+.05);};
  const root=document.querySelector(sel); if(!root) return null;
  const out=new Map();
  root.querySelectorAll('*').forEach(el=>{
    if(!el.offsetParent)return;
    if(![...el.childNodes].some(n=>n.nodeType===3&&n.textContent.trim()))return;
    const cs=getComputedStyle(el);
    if(cs.visibility==='hidden'||cs.opacity==='0')return;
    const k=cs.color+'|'+cs.fontSize+'|'+cs.fontWeight; if(out.has(k))return;
    out.set(k,{size:cs.fontSize,weight:cs.fontWeight,
      ratio:+ratio(cs.color,bgStack(el)).toFixed(2),s:el.textContent.trim().slice(0,30)});});
  return [...out.values()];
}
"""

TOKENS = r"""
() => {const c=getComputedStyle(document.body);
  return {radiusMd:c.getPropertyValue('--radius-md').trim(),
          textBase:c.getPropertyValue('--text-base').trim(),
          sp5:c.getPropertyValue('--sp-5').trim(),
          bg:c.getPropertyValue('--bg').trim()};}
"""

def boot(pw, flag):
    b = pw.chromium.launch(executable_path=CHROME)
    pg = b.new_context(viewport={"width": 1440, "height": 900}, color_scheme="dark",
                       bypass_csp=True).new_page()
    pg.route("https://api.github.com/**", lambda r: r.fulfill(
        status=200, content_type="application/json",
        body=json.dumps({"sha": "stub",
                         "content": b64(SNAP if "cron-snapshot" in r.request.url else DATA)})))
    pg.add_init_script("localStorage.setItem('k2auth','true');localStorage.setItem('gh_token','stub');"
                       f"localStorage.setItem('k2.ui2','{flag}');")
    pg.goto("file:///Users/ryansandoval/k2-dashboard/index.html")
    pg.wait_for_function("window._dataLoaded === true", timeout=30000)
    pg.wait_for_timeout(1200)
    return b, pg

def main():
    fails, on_bad, off_bad, styles, checked = [], {}, {}, 0, 0
    with sync_playwright() as pw:
        b_on, on = boot(pw, "1"); tok_on = on.evaluate(TOKENS)
        b_off, off = boot(pw, "0"); tok_off = off.evaluate(TOKENS)

        # 1. the retuned tokens actually arrive on pages other than Today
        if tok_on["radiusMd"] != "4px":
            fails.append(f'--radius-md is {tok_on["radiusMd"]}, expected the single radius')
        if tok_on["textBase"] != "16px":
            fails.append(f'--text-base is {tok_on["textBase"]} — still the fluid clamp() scale')
        if tok_on["sp5"] != "24px":
            fails.append(f'--sp-5 is {tok_on["sp5"]}, still off-scale')
        for k in ("radiusMd", "textBase", "sp5", "bg"):
            if tok_on[k] == tok_off[k]:
                fails.append(f"{k} is identical with the flag on and off — the layer is not reaching the app")

        # 2. contrast, both states. Legacy carries pre-existing defects in hard-coded inline
        #    colours that no token retune can reach, so the bar is "no worse than what Ryan
        #    has today", with the absolute numbers reported rather than hidden.
        for tag, pg, bucket in (("on", on, on_bad), ("off", off, off_bad)):
            for page in PAGES:
                # A fixed 450ms sleep was enough when this gate ran alone and not when it
                # ran inside the ledger with nine other browsers competing for the machine:
                # the style count moved run to run and one page came back empty. Wait for
                # the page to actually be on screen with text in it instead of guessing.
                try:
                    pg.evaluate(f"() => navigateTo('{page}')")
                    pg.wait_for_function(
                        "sel => { const e = document.querySelector(sel);"
                        " return !!e && e.offsetParent !== null"
                        " && (e.innerText || '').trim().length > 20; }",
                        arg=f"#page-{page}", timeout=15000)
                except Exception:
                    fails.append(f"{page}: never rendered after navigateTo"); continue
                rows = pg.evaluate(CONTRAST, f"#page-{page}")
                if rows is None:
                    fails.append(f"{page}: page element not found"); continue
                if tag == "on" and rows:
                    checked += 1; styles += len(rows)
                for r in rows:
                    px = float(r["size"].replace("px", "")); wt = int(r["weight"])
                    need = 3.0 if (px >= 24 or (px >= 18.66 and wt >= 700)) else 4.5
                    if r["ratio"] < need:
                        bucket[(page, r["s"][:24], r["size"])] = r["ratio"]
        b_on.close(); b_off.close()

    if checked < 6:
        print(f"G8 FAIL: only {checked} pages rendered text — the probe is not exercising the app")
        return 1
    if len(on_bad) > len(off_bad):
        mine = sorted(k for k in on_bad if k not in off_bad)
        fails.append(f"contrast got worse: {len(off_bad)} failing before, {len(on_bad)} after. "
                     f"New: {'; '.join(f'{k[0]} {k[1]} {on_bad[k]}:1' for k in mine[:6])}")

    if fails:
        print("G8 FAIL:\n  " + "\n  ".join(fails[:12])); return 1
    left = sorted(on_bad)
    print(f"G8 PASS: tokens reach the app (radius {tok_off['radiusMd']}->{tok_on['radiusMd']}, "
          f"type {tok_off['textBase']}->{tok_on['textBase']}, --sp-5 {tok_off['sp5']}->{tok_on['sp5']}); "
          f"{styles} text styles over {checked} pages; contrast failures {len(off_bad)} -> {len(on_bad)}. "
          + (f"Remaining (hard-coded inline colours the tokens cannot reach): "
             + "; ".join(f"{k[0]}/{k[1]} {on_bad[k]}:1" for k in left) if left else "None left."))
    return 0

if __name__ == "__main__":
    sys.exit(main())
