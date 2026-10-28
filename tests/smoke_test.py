"""End-to-end checks for the Lean 12 app. Run: python3 tests/smoke_test.py path/to/index.html
Needs: pip install playwright && playwright install chromium. Optional: npm i axe-core for the accessibility scan."""
import sys, os, json
from playwright.sync_api import sync_playwright

TARGET = sys.argv[1] if len(sys.argv) > 1 else "/mnt/user-data/outputs/lean12_app.html"
URL = TARGET if TARGET.startswith("http") else "file://" + os.path.abspath(TARGET)
AXE_PATH = os.environ.get("AXE_PATH", "/tmp/audit/node_modules/axe-core/axe.min.js")
AXE = open(AXE_PATH).read() if os.path.exists(AXE_PATH) else None
results, errors = [], []

def check(name, ok, detail=""):
    results.append((name, bool(ok), detail))
    print(("PASS " if ok else "FAIL ") + name + (f"  [{detail}]" if detail and not ok else ""))

def new_page(b, w=390, h=844, scheme="light"):
    ctx = b.new_context(viewport={"width": w, "height": h}, is_mobile=True, has_touch=True, color_scheme=scheme)
    pg = ctx.new_page()
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.on("console", lambda m: errors.append(m.text) if m.type == "error" and "ERR_" not in m.text and "fonts.g" not in m.text else None)
    return ctx, pg

def tab(pg, i):
    pg.evaluate(f"document.querySelectorAll('#tabbar button')[{i}].click()"); pg.wait_for_timeout(120)

def axe(pg, label):
    if not AXE: return
    pg.evaluate(AXE)
    r = pg.evaluate("axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa','best-practice']}})")
    v = [f"{x['id']}x{len(x['nodes'])}" for x in r["violations"]]
    check(f"axe: {label}", not v, ", ".join(v))

with sync_playwright() as p:
    b = p.chromium.launch()

    # ---- basic render, plan, theme -------------------------------------------------
    ctx, pg = new_page(b, scheme="dark"); pg.goto(URL); pg.wait_for_timeout(400)
    check("title and heading", "Lean 12" in pg.title() and pg.locator("h1").inner_text() == "Day A")
    check("default theme is light even on a dark phone", pg.evaluate("getComputedStyle(document.body).backgroundColor") == "rgb(236, 239, 242)")
    check("Day A has 8 lifts", pg.locator("button.ex").count() == 8)
    check("landmarks: header, main, nav", pg.locator("header").count() == 1 and pg.locator("main").count() == 1 and pg.locator("nav").count() == 1)
    pg.locator('.seg button[data-d="B"]').click()
    check("Day B has 9 lifts", pg.locator("button.ex").count() == 9)
    check("no Smith or barbell in the plan", pg.evaluate("!/smith|barbell/i.test(document.body.innerText)"))
    pg.locator('.seg button[data-d="A"]').click()

    # ---- warm-up checklist ---------------------------------------------------------
    pg.locator("summary").first.click()
    pg.locator('[data-k="pre-0"]').click()
    check("warm-up counter updates and stays open", "1 of 7" in pg.locator("summary").first.inner_text() and pg.locator("details").first.evaluate("d=>d.open"))

    # ---- exercise sheet: focus, inert, escape, restore ----------------------------------
    pg.locator('[data-k="ex-1"]').click(); pg.wait_for_timeout(250)
    check("sheet moves focus to its heading", pg.evaluate("document.activeElement.id") == "sheet-title")
    check("background is inert while sheet is open", pg.evaluate("document.getElementById('main').hasAttribute('inert')"))
    inside = True
    for _ in range(45):
        pg.keyboard.press("Tab")
        if not pg.evaluate("!!document.activeElement.closest('#sheet, #timer')"): inside = False
    check("focus stays inside the sheet over 45 tabs", inside)
    pg.keyboard.press("Escape"); pg.wait_for_timeout(250)
    check("Escape closes the sheet and returns focus to the lift", pg.evaluate("document.activeElement.getAttribute('data-k')") == "ex-1")
    check("background is no longer inert", not pg.evaluate("document.getElementById('main').hasAttribute('inert')"))

    # ---- logging, units, timer -----------------------------------------------------
    pg.locator('[data-k="ex-1"]').click(); pg.wait_for_timeout(200)
    pg.locator('[data-k="s0l-inc"]').click(); pg.locator('[data-k="s0l-inc"]').click()
    load = pg.locator(".setrow").first.locator("input").first.input_value()
    check("dumbbell stepper adds 2 kg per tap", load == "4", load)
    pg.locator('[data-k="s0d"]').click()
    check("timer appears after ticking a set", pg.locator("#timer.on").count() == 1)
    check("timer button says Skip rest", pg.locator("#timer button", has_text="Skip rest").count() == 1)
    check("focus survives set tick (no reset to page start)", pg.evaluate("document.activeElement.getAttribute('data-k')") == "s0d")
    pg.keyboard.press("Escape"); pg.wait_for_timeout(200)
    pg.locator('[data-k="ex-2B"]').click(); pg.wait_for_timeout(200)
    check("stack machines are labelled stack", "stack" in pg.locator(".setrow .stepper .u").first.inner_text())
    pg.keyboard.press("Escape")

    # ---- progression: all sets at top of range suggests going up ---------------------
    st = json.loads(pg.evaluate("localStorage.getItem('lean12_v1')"))
    st["sessions"]["2020-01-01_A"] = {"date": "2020-01-01", "day": "A", "done": True, "ex": {"goblet_squat": {"sets": [{"l": 16, "r": 12, "d": True}] * 3, "rir": 1}}}
    pg.evaluate("v=>localStorage.setItem('lean12_v1',JSON.stringify(v))", st); pg.reload(); pg.wait_for_timeout(300)
    pg.locator('[data-k="ex-1"]').click(); pg.wait_for_timeout(200)
    t = pg.locator(".sugg").first.inner_text()
    check("goblet squat suggests 18 kg after 3x12 at 16 kg", "Time to go up" in t and "18 kg" in t, t)
    pg.keyboard.press("Escape")

    # ---- old data compatibility (retired exercises, old Day C) ----------------------------
    st["sessions"]["2020-01-02_C"] = {"date": "2020-01-02", "day": "C", "done": True, "ex": {"smith_squat": {"sets": [{"l": 30, "r": 10, "d": True}], "rir": 2}}}
    st["lastDay"] = "C"
    pg.evaluate("v=>localStorage.setItem('lean12_v1',JSON.stringify(v))", st); pg.reload(); pg.wait_for_timeout(300)
    for i, n in enumerate(["train", "log", "progress", "guide", "data"]):
        tab(pg, i)
        check(f"old data does not break {n}", pg.locator("text=Something went wrong").count() == 0)
    tab(pg, 0)
    check("after an old Day C the next day is A", pg.locator("h1").inner_text() == "Day A")

    # ---- daily log: labels linked to inputs ----------------------------------------------
    tab(pg, 1)
    check("every form control has a linked label", pg.evaluate("""[...document.querySelectorAll('#main input:not([type=hidden]), #main select, #main textarea')].every(e=>e.id&&document.querySelector('label[for="'+e.id+'"]'))"""))
    pg.locator('#main input[type=number]').first.fill("74.6"); pg.locator('#main input[type=number]').first.dispatch_event("change")
    pg.locator('[data-k="sum-foods"]').click(); pg.locator('[data-k="food-0"]').click()
    check("food quick-add updates protein", "6 g" in pg.locator("#main").inner_text())
    check("Add food panel stays open after adding", pg.locator('[data-k="sum-foods"]').evaluate("s=>s.parentElement.open"))

    # ---- data tab: dialogs, restore validation, prototype pollution -----------------------
    tab(pg, 4)
    pg.locator("button", has_text="Delete all data").click(); pg.wait_for_timeout(150)
    names = pg.locator("#dlg button").all_inner_texts()
    check("delete dialog has clear button labels", names == ["Delete everything", "Keep my data"], str(names))
    check("dialog focus starts on the safe option", pg.evaluate("document.activeElement.innerText") == "Keep my data")
    pg.locator("#dlg button", has_text="Keep my data").click(); pg.wait_for_timeout(100)
    check("keeping data keeps the weight", json.loads(pg.evaluate("localStorage.getItem('lean12_v1')"))["daily"] != {})
    pg.locator("textarea").nth(1).fill('{"settings":{},"daily":{"__proto__":{"polluted":"yes"}},"sessions":{}}')
    pg.locator("button", has_text="Restore backup").click(); pg.wait_for_timeout(150)
    check("restore asks before replacing", pg.locator("#dlg.on").count() == 1)
    pg.locator("#dlg button", has_text="Keep current data").click()
    check("no prototype pollution from a backup", pg.evaluate("({}).polluted") is None)
    pg.locator("textarea").nth(1).fill("not json")
    pg.locator("button", has_text="Restore backup").click(); pg.wait_for_timeout(100)
    check("invalid backup is rejected with a clear message", "not a valid backup" in pg.locator("#toast").inner_text())

    # ---- progress empty state -------------------------------------------------------------
    ctx2, p2 = new_page(b); p2.goto(URL); p2.wait_for_timeout(300); tab(p2, 2)
    check("progress empty state tells you what to do", p2.locator("text=Log your first morning weight").count() == 1)
    ctx2.close()

    # ---- corrupted storage recovers ----------------------------------------------------------
    ctx3, p3 = new_page(b)
    p3.add_init_script("localStorage.setItem('lean12_v1','{not valid json')")
    p3.goto(URL); p3.wait_for_timeout(300)
    check("corrupt data: app still opens", p3.locator("h1").inner_text() == "Day A")
    check("corrupt data: user is told and a copy is kept", "could not be read" in p3.locator(".banner").first.inner_text() and p3.evaluate("localStorage.getItem('lean12_v1_unreadable')") is not None)
    ctx3.close()

    # ---- accessibility scans (axe) ----------------------------------------------------------------
    ctx4, p4 = new_page(b); p4.goto(URL); p4.wait_for_timeout(300)
    axe(p4, "Train, Day A, light")
    p4.locator('.seg button[data-d="B"]').click(); axe(p4, "Train, Day B, light (amber contrast)")
    p4.locator('[data-k="ex-1"]').click(); p4.wait_for_timeout(250); axe(p4, "exercise sheet, Day B, light")
    p4.locator('#sheet .pair').first.click(); p4.wait_for_timeout(200); axe(p4, "enlarged pictures")
    p4.keyboard.press("Escape"); p4.keyboard.press("Escape")
    for i, n in ((1, "Log"), (2, "Progress"), (3, "Guide"), (4, "Data")):
        tab(p4, i); axe(p4, n + ", light")
    p4.locator('.themebtn').click(); p4.wait_for_timeout(150)
    check("theme button cycles to dark", p4.evaluate("document.documentElement.getAttribute('data-theme')") == "dark")
    for i, n in ((0, "Train"), (1, "Log"), (2, "Progress")):
        tab(p4, i); axe(p4, n + ", dark")
    ctx4.close()

    # ---- touch targets and 200% zoom --------------------------------------------------------------------
    ctx5, p5 = new_page(b); p5.goto(URL); p5.wait_for_timeout(300)
    small = set()
    def sweep(label):
        for t in p5.evaluate("""(()=>{var o=[];document.querySelectorAll('button,input,select,textarea,summary,a').forEach(function(e){if(e.closest('[inert]')||e.classList.contains('skip'))return;var r=e.getBoundingClientRect();if(!r.width||!r.height)return;var cs=getComputedStyle(e);if(cs.visibility==='hidden')return;if(r.width<43.5||r.height<43.5)o.push((e.getAttribute('aria-label')||e.textContent||e.tagName).trim().slice(0,30)+' '+Math.round(r.width)+'x'+Math.round(r.height));});return o;})()"""): small.add(label + ": " + t)
    sweep("train"); p5.locator('[data-k="ex-1"]').click(); p5.wait_for_timeout(250); sweep("sheet"); p5.keyboard.press("Escape")
    for i, n in ((1, "log"), (2, "progress"), (3, "guide"), (4, "data")): tab(p5, i); sweep(n)
    check("all tap targets are at least 44 px", not small, "; ".join(sorted(small))[:300])
    ctx5.close()
    ctx6, p6 = new_page(b, 195, 422); p6.goto(URL); p6.wait_for_timeout(300)
    bad = []
    for i, n in enumerate(["train", "log", "progress", "guide", "data"]):
        tab(p6, i); ov = p6.evaluate("document.documentElement.scrollWidth-document.documentElement.clientWidth")
        if ov > 1: bad.append(f"{n}:{ov}px")
    p6.locator('[data-k="ex-1"]').click() if False else None
    tab(p6, 0); p6.locator('[data-k="ex-1"]').click(); p6.wait_for_timeout(250)
    ov = p6.evaluate("document.getElementById('sheet').scrollWidth-document.getElementById('sheet').clientWidth")
    if ov > 1: bad.append(f"sheet:{ov}px")
    check("no horizontal overflow at 200% zoom (all tabs and the set logger)", not bad, ", ".join(bad))
    ctx6.close()
    ctx7, p7 = new_page(b, 360, 740); p7.goto(URL); p7.wait_for_timeout(300)
    p7.locator('[data-k="ex-1"]').click(); p7.wait_for_timeout(250)
    sm = p7.evaluate("""[...document.querySelectorAll('#sheet button,#sheet input')].filter(e=>{var r=e.getBoundingClientRect();return r.width&&(r.width<43.5||r.height<43.5)}).map(e=>(e.getAttribute('aria-label')||e.tagName)+' '+Math.round(e.getBoundingClientRect().width)+'px').slice(0,5)""")
    check("set logger keeps 44 px targets on a 360 px phone", not sm, str(sm))
    ctx7.close()

    check("no console or page errors", not errors, "; ".join(errors)[:300])
    b.close()

fails = [r for r in results if not r[1]]
print(f"\n{len(results)-len(fails)}/{len(results)} checks passed")
sys.exit(1 if fails else 0)
