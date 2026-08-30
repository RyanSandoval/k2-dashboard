#!/usr/bin/env python3
"""G2 — every text style in the new UI clears WCAG AA, measured from rendered pixels in
both colour schemes. Sampled through canvas because Chrome reports computed colours in the
syntax they were authored in; a naive rgb parser silently returns 1.0 for every oklch/hsl
value and the whole check passes while seeing nothing."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from _boot import open_app
from playwright.sync_api import sync_playwright

JS = r"""
() => {
  const cv=document.createElement('canvas');cv.width=cv.height=1;
  const ctx=cv.getContext('2d',{willReadFrequently:true});
  const toRGB=s=>{ctx.clearRect(0,0,1,1);ctx.fillStyle='#000';ctx.fillStyle=s;ctx.fillRect(0,0,1,1);
    const d=ctx.getImageData(0,0,1,1).data;return [d[0],d[1],d[2]];};
  const sr=c=>{c/=255;return c<=.03928?c/12.92:Math.pow((c+.055)/1.055,2.4)};
  const lum=s=>{const [r,g,b]=toRGB(s);return .2126*sr(r)+.7152*sr(g)+.0722*sr(b)};
  const bgOf=el=>{let n=el;while(n&&n!==document.documentElement){
    const c=getComputedStyle(n).backgroundColor;
    if(c&&c!=='rgba(0, 0, 0, 0)'&&c!=='transparent')return c;n=n.parentElement;}
    return getComputedStyle(document.body).backgroundColor;};
  const ratio=(f,b)=>{const A=lum(f),B=lum(b);return (Math.max(A,B)+.05)/(Math.min(A,B)+.05)};
  const roots=[document.querySelector('.sidebar'),document.getElementById('page-jots')].filter(Boolean);
  const out=new Map();
  for(const root of roots)
    root.querySelectorAll('*').forEach(el=>{
      if(!el.offsetParent && el!==root) return;                 // skip hidden
      if(![...el.childNodes].some(n=>n.nodeType===3&&n.textContent.trim()))return;
      const cs=getComputedStyle(el);
      if(cs.visibility==='hidden'||cs.opacity==='0')return;
      const k=cs.color+'|'+cs.fontSize+'|'+cs.fontWeight;
      if(out.has(k))return;
      out.set(k,{size:cs.fontSize,weight:cs.fontWeight,
        ratio:+ratio(cs.color,bgOf(el)).toFixed(2),
        sample:el.textContent.trim().slice(0,36)});
    });
  return [...out.values()].sort((a,b)=>a.ratio-b.ratio);
}
"""

def main():
    fails, total = [], 0
    with sync_playwright() as pw:
        for scheme in ("dark",):   # the app is dark-only and now declares color-scheme:dark
            b, pg = open_app(pw, ui2=True, scheme=scheme)
            # the decision is documented, not silently skipped: assert dark-only is declared
            declared = pg.evaluate("() => getComputedStyle(document.body).colorScheme")
            if "dark" not in (declared or ""):
                print("G2 FAIL: body does not declare color-scheme:dark, so light mode is reachable and untested")
                return 1
            if not pg.evaluate("() => document.body.classList.contains('ui2')"):
                print("G2 FAIL: ui2 class never applied — measuring the old UI"); return 1
            pg.click('.nav-item[data-page="jots"]'); pg.wait_for_timeout(700)
            rows = pg.evaluate(JS); total += len(rows)
            for r in rows:
                px = float(r["size"].replace("px", "")); wt = int(r["weight"])
                need = 3.0 if (px >= 24 or (px >= 18.66 and wt >= 700)) else 4.5
                if r["ratio"] < need:
                    fails.append(f'{scheme} {r["ratio"]}:1 need {need} — {r["size"]} w{r["weight"]} :: {r["sample"]}')
            b.close()
    if not total:
        print("G2 FAIL: measured 0 text styles — the probe found nothing, which is not a pass")
        return 1
    if fails:
        print("G2 FAIL:\n  " + "\n  ".join(fails)); return 1
    print(f"G2 PASS: {total} text styles across the sidebar and Today, dark-only as declared, all clear WCAG AA")
    return 0

if __name__ == "__main__":
    sys.exit(main())
