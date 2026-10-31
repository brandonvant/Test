#!/usr/bin/env python3
"""Generates short149/index.html (static HTML, every timed element written out)."""
import re, json, pathlib

OUT = pathlib.Path(__file__).parent / "index.html"
DUR = 30.0

# VO speech segments (seconds in assets/vo.wav) and their text
SEGS = [
    ((0.00, 2.19), "One hundred and forty-nine..."),
    ((2.74, 3.28), "to nil."),
    ((3.50, 5.045), "The biggest scoreline ever."),
    ((5.265, 7.134), "And the winners barely touched the ball."),
    ((7.354, 8.264), "Madagascar,"),
    ((8.484, 9.521), "2002."),
    ((9.741, 13.303), "SO l'Emyrne lost the title on a referee's call they called a robbery."),
    ((13.523, 14.02), "So,"),
    ((14.24, 15.83), "next game, they protested."),
    ((16.05, 16.636), "Kickoff..."),
    ((16.856, 18.306), "and they shot at their own net."),
    ((18.526, 19.125), "Again."),
    ((19.345, 20.081), "And again."),
    ((20.301, 22.226), "A hundred and forty-nine times."),
    ((22.446, 23.913), "Fans wanted refunds."),
    ((24.133, 25.757), "The coach got a three-year ban."),
    ((25.977, 27.293), "Genius protest,"),
    ((27.513, 28.928), "or total disgrace?"),
]
# words that get the accent colour in captions
HOT = {"149", "NIL", "BIGGEST", "MADAGASCAR", "2002", "ROBBERY", "PROTESTED", "OWN", "AGAIN",
       "REFUNDS", "BAN", "GENIUS", "DISGRACE", "THREE-YEAR", "NET"}

def syl(w):
    w = re.sub(r"[^a-z0-9]", "", w.lower())
    if w.isdigit():
        return 4
    return max(1, len(re.findall(r"[aeiouy]+", w)))

# caption display words: replace spoken numbers with digits for punch
DISPLAY = {"One hundred and forty-nine...": ["149..."],
           "A hundred and forty-nine times.": ["149", "times."]}

words = []  # (start, end, text)
for (a, b), text in SEGS:
    toks = DISPLAY.get(text) or text.split()
    weights = [syl(t) + 0.6 for t in toks]
    tot = sum(weights)
    t = a
    for tok, w in zip(toks, weights):
        d = (b - a) * w / tot
        words.append((round(t, 3), round(t + d, 3), tok))
        t += d

# group into caption lines of up to 3 words, breaking at segment boundaries
groups = []
cur = []
seg_ends = {round(b, 3) for (a, b), _ in SEGS}
for w in words:
    cur.append(w)
    end_here = any(abs(w[1] - e) < 0.01 for e in seg_ends)
    if len(cur) == 3 or end_here:
        groups.append(cur)
        cur = []
if cur:
    groups.append(cur)

cap_html = []
cap_js = []
groups = [g for g in groups if g[0][0] < 25.9]
for gi, g in enumerate(groups):
    gs = g[0][0]
    nxt = groups[gi + 1][0][0] if gi + 1 < len(groups) else g[-1][1] + 0.6
    ge = min(nxt, g[-1][1] + 0.5)
    spans = []
    for wi, (ws, we, tok) in enumerate(g):
        clean = re.sub(r"[^A-Z0-9\-]", "", tok.upper())
        cls = "w hot" if clean in HOT else "w"
        spans.append(f'<span id="c{gi}w{wi}" class="{cls}">{tok.upper()}</span>')
        cap_js.append((f"#c{gi}w{wi}", ws, we))
    cap_html.append(
        f'<div id="cap{gi}" class="clip cap" data-start="{gs:.3f}" data-duration="{ge - gs:.3f}" '
        f'data-track-index="20"><div class="capin" id="capin{gi}">{" ".join(spans)}</div></div>')
    cap_js.append((f"#capin{gi}", gs, None))

# ---------- scenes ----------
# (id, img, start, end, rotation, kenburns from->to, origin)
SCENES = [
    ("sc1", "s1", 0.0, 5.2, -1.2, (1.10, 1.22), "50% 30%"),
    ("sc2", "s7", 5.2, 7.30, 1.0, (1.18, 1.06), "50% 60%"),
    ("sc3", "s2", 7.30, 9.70, -0.8, (1.05, 1.20), "50% 50%"),
    ("sc4", "s3", 9.70, 13.45, 1.2, (1.08, 1.22), "50% 35%"),
    ("sc5", "s4", 13.45, 18.45, -1.0, (1.30, 1.08), "50% 55%"),
    ("sc6", "s7", 18.45, 22.40, 0.0, (1.06, 1.30), "50% 60%"),
    ("sc7", "s5", 22.40, 24.10, 1.0, (1.08, 1.20), "50% 45%"),
    ("sc8", "s6", 24.10, 25.95, -1.0, (1.20, 1.06), "50% 70%"),
    ("sc9", "s4", 25.95, DUR, 0.0, (1.10, 1.18), "50% 50%"),
]

scene_html = []
scene_js = []
for i, (sid, img, s, e, rot, (k0, k1), org) in enumerate(SCENES):
    z = 2 + i
    scene_html.append(f'''
      <div id="{sid}" class="clip scene" data-start="{s:.2f}" data-duration="{e - s:.2f}" data-track-index="1" style="z-index:{z}">
        <div class="panel" id="{sid}-panel">
          <img id="{sid}-img" class="art" src="assets/{img}.png" alt="" style="transform-origin:{org}" />
          <div class="halftone"></div>
        </div>
      </div>''')
    entry = "slam" if i % 2 == 0 else "swipe"
    scene_js.append((sid, s, e, rot, k0, k1, entry))

# ---------- overlays (tags / stamps / graphics) ----------
OVER = '''
      <!-- hook: 149-0 on the scoreboard, on screen from frame 0 -->
      <div id="score" class="clip" data-start="0" data-duration="5.2" data-track-index="10" style="z-index:40">
        <div id="score-in" class="scoreboard"><span class="sb-n" id="sb-l">149</span><span class="sb-dash">-</span><span class="sb-n" id="sb-r">0</span></div>
      </div>
      <div id="tag-hook" class="clip" data-start="0" data-duration="3.4" data-track-index="11" style="z-index:41">
        <div id="tag-hook-in" class="tag tag-top yellow">A REAL FOOTBALL SCORE</div>
      </div>
      <div id="st-record" class="clip" data-start="3.45" data-duration="1.75" data-track-index="11" style="z-index:42">
        <div id="st-record-in" class="stamp red">BIGGEST SCORELINE EVER</div>
      </div>
      <div id="tag-wait" class="clip" data-start="5.25" data-duration="2.05" data-track-index="11" style="z-index:42">
        <div id="tag-wait-in" class="tag tag-top white">WAIT... WHAT?</div>
      </div>
      <div id="tag-mada" class="clip" data-start="7.35" data-duration="2.35" data-track-index="11" style="z-index:42">
        <div id="tag-mada-in" class="tag tag-top yellow">MADAGASCAR &middot; 31 OCT 2002</div>
      </div>
      <div id="tag-soe" class="clip" data-start="9.75" data-duration="3.7" data-track-index="11" style="z-index:42">
        <div id="tag-soe-in" class="tag tag-top white">SO L'EMYRNE: TITLE LOST</div>
      </div>
      <div id="st-rob" class="clip" data-start="12.2" data-duration="1.25" data-track-index="12" style="z-index:43">
        <div id="st-rob-in" class="stamp red">ROBBERY?!</div>
      </div>
      <div id="tag-protest" class="clip" data-start="13.5" data-duration="3.3" data-track-index="11" style="z-index:42">
        <div id="tag-protest-in" class="stamp yellowstamp">THE PROTEST</div>
      </div>
      <div id="tag-own" class="clip" data-start="16.85" data-duration="1.6" data-track-index="11" style="z-index:42">
        <div id="tag-own-in" class="tag tag-top red">OWN GOAL</div>
      </div>
      <div id="counter" class="clip" data-start="18.45" data-duration="3.95" data-track-index="12" style="z-index:43">
        <div id="counter-in" class="counter"><div class="counter-lab">OWN GOALS</div><div id="counter-n" class="counter-n">1</div></div>
      </div>
      <div id="tag-refund" class="clip" data-start="22.45" data-duration="1.65" data-track-index="11" style="z-index:42">
        <div id="tag-refund-in" class="tag tag-top yellow">FANS: "REFUND!"</div>
      </div>
      <div id="st-ban" class="clip" data-start="24.3" data-duration="1.65" data-track-index="12" style="z-index:43">
        <div id="st-ban-in" class="stamp red big">BANNED<br><small>3 YEARS</small></div>
      </div>
      <div id="vs" class="clip" data-start="25.95" data-duration="4.05" data-track-index="12" style="z-index:43">
        <div id="vs-a" class="vsbox green">GENIUS?</div>
        <div id="vs-or" class="vsor">OR</div>
        <div id="vs-b" class="vsbox redbox">DISGRACE?</div>
        <div id="vs-cta" class="tag cta yellow">COMMENT YOUR VERDICT</div>
      </div>
      <div id="flash" class="clip" data-start="0" data-duration="30" data-track-index="30" style="z-index:60"><div id="flash-in" class="flash"></div></div>
'''

# ---------- audio ----------
SFX = [  # (id, file, start, volume, media_start)
    ("a-hit0", "impact-bass-1", 0.02, 0.55, 0),
    ("a-stamp1", "impact-bass-2", 3.30, 0.45, 0),
    ("a-wh1", "whoosh-short", 5.12, 0.40, 0),
    ("a-wh2", "whoosh", 7.22, 0.35, 0),
    ("a-wh3", "whoosh-short", 9.62, 0.40, 0),
    ("a-glitch", "glitch-1", 12.20, 0.30, 0),
    ("a-wh4", "whoosh-cinematic", 13.30, 0.40, 0),
    ("a-hit2", "impact-bass-1", 16.85, 0.45, 0),
    ("a-riser", "riser", 18.45, 0.30, 6.0),
    ("a-hit3", "impact-bass-2", 21.95, 0.55, 0),
    ("a-pop1", "pop", 22.47, 0.40, 0),
    ("a-hit4", "impact-bass-1", 24.30, 0.50, 0),
    ("a-wh5", "whoosh", 25.85, 0.35, 0),
    ("a-pop2", "pop", 26.00, 0.40, 0),
    ("a-pop3", "pop", 27.55, 0.40, 0),
]
audio_html = [
    '<audio id="vo" class="clip" src="assets/vo.wav" data-start="0" data-duration="29.2" data-track-index="40" data-volume="1"></audio>',
    '<audio id="music" class="clip" src="assets/music.mp3" data-start="0" data-duration="30" data-track-index="41" data-volume="0.2" data-fade-out="1.2"></audio>',
]
import subprocess
for n, (aid, f, s, v, ms) in enumerate(SFX):
    d = float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0", str(OUT.parent/"assets"/"sfx"/(f+".mp3"))],capture_output=True,text=True).stdout)
    d = min(d - ms, 3.6, DUR - s)
    extra = f' data-media-start="{ms}"' if ms else ""
    audio_html.append(f'<audio id="{aid}" class="clip" src="assets/sfx/{f}.mp3" data-start="{s}"{extra} data-duration="{d:.2f}" data-track-index="{50 + n}" data-volume="{v}"></audio>')

CSS = r'''
@font-face { font-family: "Bangers"; src: url("assets/fonts/Bangers-Regular.ttf") format("truetype"); }
:root { --paper:#efe8d8; --ink:#111; --red:#c8102e; --green:#0f7a3c; --yellow:#ffcc00; --white:#fff8ea; }
* { margin:0; padding:0; box-sizing:border-box; }
html, body { width:1080px; height:1920px; overflow:hidden; background:var(--paper); }
#root { position:relative; width:1080px; height:1920px; overflow:hidden; font-family:"Bangers", "Archivo Black", sans-serif; }
#paper { position:absolute; inset:0; width:1080px; height:1920px; z-index:0; }
.scene { position:absolute; inset:0; }
.panel { position:absolute; left:34px; top:34px; width:1012px; height:1852px; border:12px solid var(--ink); overflow:hidden; background:#222; box-shadow:14px 14px 0 rgba(0,0,0,.85); }
.art { position:absolute; left:0; top:0; width:100%; height:100%; object-fit:cover; }
.halftone { position:absolute; inset:0; background-image:radial-gradient(rgba(0,0,0,.22) 1.6px, transparent 1.8px); background-size:9px 9px; mix-blend-mode:multiply; opacity:.55; }
.tag { position:absolute; left:50%; top:230px; padding:14px 34px 8px; border:8px solid var(--ink); font-size:76px; letter-spacing:2px; color:var(--ink); white-space:nowrap; box-shadow:10px 10px 0 var(--ink); }
.tag.yellow { background:var(--yellow); } .tag.white { background:var(--white); } .tag.red { background:var(--red); color:var(--white); }
.stamp { position:absolute; left:50%; top:820px; padding:18px 40px 8px; border:12px solid currentColor; font-size:118px; line-height:.95; text-align:center; white-space:nowrap; background:rgba(255,248,234,.92); }
.stamp.red { color:var(--red); } .stamp.yellowstamp { color:var(--ink); background:var(--yellow); box-shadow:14px 14px 0 var(--ink); border-color:var(--ink); }
.stamp.big { font-size:170px; } .stamp small { font-size:96px; }
.scoreboard { position:absolute; left:50%; top:470px; display:flex; align-items:center; gap:18px; padding:30px 50px 14px; background:#0d0d0d; border:12px solid var(--yellow); box-shadow:0 0 0 10px var(--ink), 18px 18px 0 10px rgba(0,0,0,.6); }
.sb-n { font-size:300px; line-height:.9; color:var(--yellow); text-shadow:0 0 28px rgba(255,204,0,.55); }
.sb-dash { font-size:200px; color:var(--white); }
.counter { position:absolute; left:50%; top:420px; text-align:center; }
.counter-lab { display:inline-block; font-size:80px; padding:10px 30px 4px; background:var(--red); color:var(--white); border:8px solid var(--ink); box-shadow:10px 10px 0 var(--ink); }
.counter-n { font-size:420px; line-height:.95; color:var(--yellow); -webkit-text-stroke:14px var(--ink); paint-order:stroke fill; text-shadow:16px 16px 0 var(--ink); }
.vsbox { position:absolute; left:50%; padding:20px 50px 8px; font-size:170px; border:12px solid var(--ink); box-shadow:16px 16px 0 var(--ink); white-space:nowrap; color:var(--white); }
.vsbox.green { top:330px; background:var(--green); } .vsbox.redbox { top:760px; background:var(--red); }
.vsor { position:absolute; left:50%; top:610px; font-size:110px; color:var(--ink); background:var(--yellow); border:8px solid var(--ink); padding:4px 28px 0; border-radius:50%; }
.cta { top:1060px; font-size:66px; }
.cap { position:absolute; left:0; right:0; top:1130px; height:200px; z-index:50; }
.capin { position:absolute; left:50%; top:0; width:960px; text-align:center; font-size:104px; line-height:1.05; color:var(--white); -webkit-text-stroke:12px var(--ink); paint-order:stroke fill; text-shadow:8px 8px 0 var(--ink); }
.w { display:inline-block; padding:4px 12px 0; border-radius:10px; }
.w.hot { color:var(--yellow); }
.w.on { background:var(--yellow); color:var(--ink); -webkit-text-stroke:0; text-shadow:none; box-shadow:7px 7px 0 var(--ink); }
.flash { position:absolute; inset:0; background:#fff; opacity:0; }
.brand { position:absolute; left:50%; top:1250px; font-size:46px; letter-spacing:4px; color:var(--ink); background:var(--white); border:6px solid var(--ink); padding:8px 22px 2px; white-space:nowrap; }
'''

def js():
    L = []
    L.append("const tl = gsap.timeline({ paused: true });")
    # scenes
    for sid, s, e, rot, k0, k1, entry in SCENES_JS:
        p, im = f"#{sid}-panel", f"#{sid}-img"
        if s == 0:
            L.append(f'tl.fromTo("{p}", {{rotation:{rot}, scale:1}}, {{rotation:{rot}, scale:1, duration:0.01}}, 0);')
        elif entry == "slam":
            L.append(f'tl.fromTo("{p}", {{scale:1.35, rotation:{rot * 4}, opacity:0}}, {{scale:1, rotation:{rot}, opacity:1, duration:0.32, ease:"back.out(1.6)"}}, {s});')
        else:
            L.append(f'tl.fromTo("{p}", {{xPercent:105, rotation:{rot * 5}}}, {{xPercent:0, rotation:{rot}, duration:0.3, ease:"power4.out"}}, {s});')
        L.append(f'tl.fromTo("{im}", {{scale:{k0}}}, {{scale:{k1}, duration:{e - s:.2f}, ease:"none"}}, {s});')
    # hook scoreboard: already up at frame 0, then punch/shake
    L.append('tl.fromTo("#score-in", {xPercent:-50, scale:1, rotation:-2}, {xPercent:-50, scale:1.06, rotation:2, duration:0.5, ease:"sine.inOut", yoyo:true, repeat:9}, 0);')
    L.append('tl.fromTo("#sb-r", {scale:1}, {scale:1.35, duration:0.18, yoyo:true, repeat:1, ease:"power2.out"}, 2.74);')
    L.append('tl.fromTo("#score-in", {opacity:1}, {opacity:0, y:-60, duration:0.2}, 4.95);')
    # tags (pop in from rotation)
    for tid, s in [("tag-hook", 0), ("tag-wait", 5.25), ("tag-mada", 7.35), ("tag-soe", 9.75), ("tag-own", 16.85), ("tag-refund", 22.45)]:
        if s == 0:
            L.append(f'tl.fromTo("#{tid}-in", {{xPercent:-50, rotation:-3, scale:1}}, {{xPercent:-50, rotation:-3, scale:1.04, duration:1.2, ease:"sine.inOut", yoyo:true, repeat:1}}, 0);')
        else:
            L.append(f'tl.fromTo("#{tid}-in", {{xPercent:-50, scale:0, rotation:-14}}, {{xPercent:-50, scale:1, rotation:-3, duration:0.28, ease:"back.out(2.2)"}}, {s});')
    # stamps
    for sid, s in [("st-record", 3.45), ("st-rob", 12.2), ("tag-protest", 13.5), ("st-ban", 24.3)]:
        L.append(f'tl.fromTo("#{sid}-in", {{xPercent:-50, scale:2.6, rotation:-18, opacity:0}}, {{xPercent:-50, scale:1, rotation:-7, opacity:1, duration:0.22, ease:"power4.in"}}, {s});')
    L.append('tl.fromTo("#tag-protest-in", {y:0}, {y:-560, scale:0.7, duration:0.35, ease:"power3.in"}, 16.4);')
    # own-goal scene: darker during "the protest", reveal at kickoff
    L.append('tl.fromTo("#sc5-img", {filter:"brightness(0.45) saturate(0.6)"}, {filter:"brightness(1) saturate(1)", duration:0.25}, 16.05);')
    # counter 1 -> 149
    L.append('const cnt = {v:1}; const cn = document.querySelector("#counter-n");')
    L.append('tl.fromTo("#counter-in", {xPercent:-50, scale:0.4, opacity:0}, {xPercent:-50, scale:1, opacity:1, duration:0.25, ease:"back.out(2)"}, 18.45);')
    L.append('tl.fromTo(cnt, {v:1}, {v:149, duration:3.45, ease:"power2.in", onUpdate:()=>{cn.textContent = Math.round(cnt.v);}}, 18.5);')
    L.append('tl.fromTo("#counter-in", {rotation:0}, {rotation:4, duration:0.06, yoyo:true, repeat:9, ease:"none"}, 21.95);')
    L.append('tl.fromTo("#counter-n", {scale:1}, {scale:1.25, duration:0.16, yoyo:true, repeat:1, ease:"power2.out"}, 21.95);')
    # verdict
    L.append('tl.fromTo("#vs-a", {xPercent:-160, rotation:-20}, {xPercent:-50, rotation:-4, duration:0.32, ease:"back.out(1.7)"}, 25.98);')
    L.append('tl.fromTo("#vs-or", {xPercent:-50, scale:0}, {xPercent:-50, scale:1, duration:0.25, ease:"back.out(3)"}, 26.9);')
    L.append('tl.fromTo("#vs-b", {xPercent:60, rotation:20}, {xPercent:-50, rotation:3, duration:0.32, ease:"back.out(1.7)"}, 27.52);')
    L.append('tl.fromTo("#vs-cta", {xPercent:-50, y:80, opacity:0}, {xPercent:-50, y:0, opacity:1, duration:0.3, ease:"power3.out"}, 28.4);')
    L.append('tl.fromTo("#vs-cta", {scale:1}, {scale:1.06, duration:0.4, yoyo:true, repeat:2, ease:"sine.inOut"}, 28.75);')
    # white flashes on big hits
    L.append('tl.set("#flash-in", {opacity:0}, 0);')
    for t in [3.45, 12.2, 16.85, 21.95, 24.3]:
        L.append(f'tl.fromTo("#flash-in", {{opacity:0.75}}, {{opacity:0, duration:0.18, ease:"power2.out"}}, {t});')
    # captions
    for sel, s, e in CAP_JS:
        if e is None:
            L.append(f'tl.fromTo("{sel}", {{xPercent:-50, scale:0.7, y:30}}, {{xPercent:-50, scale:1, y:0, duration:0.14, ease:"back.out(2)"}}, {s});')
    L.append('tl.fromTo("#brand-in", {xPercent:-50, opacity:0}, {xPercent:-50, opacity:1, duration:0.3}, 26.2);')
    L.append('window.__timelines["main"] = tl;')
    seen=set(); out=[]
    for line in L:
        m=re.match(r'tl\.(?:fromTo|set)\(("[^"]+"|\w+),', line)
        if m:
            tgt=m.group(1)
            if tgt in seen and line.startswith("tl.fromTo"):
                # second+ tween on same target: don't render its from-state at authoring time
                idx=line.rfind("}, ")
                line=line[:idx]+", immediateRender:false"+line[idx:]
            seen.add(tgt)
        out.append(line)
    return "\n      ".join(out)

SCENES_JS = scene_js
CAP_JS = cap_js

# word highlight: deterministic, driven by a tween's onUpdate reading timeline time
word_times = [(sel, s, e) for sel, s, e in cap_js if e is not None]

def build():
    body_js = js()
    hl = "const WORDS = " + json.dumps([[sel[1:], s, e] for sel, s, e in word_times]) + ";\n" + \
         "      const wEls = WORDS.map(w => [document.getElementById(w[0]), w[1], w[2]]);\n" + \
         "      const hot = {t:0};\n" + \
         f"      tl.fromTo(hot, {{t:0}}, {{t:{DUR}, duration:{DUR}, ease:'none', onUpdate:()=>{{ const t = hot.t; for (const [el,s,e] of wEls) el.classList.toggle('on', t>=s && t<e); }}}}, 0);\n"
    body_js = body_js.replace('window.__timelines["main"] = tl;', hl + '      window.__timelines["main"] = tl;')
    html = f'''<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <title>149-0: The Own Goal Protest</title>
    <script src="assets/gsap.min.js"></script>
    <style>{CSS}</style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{DUR}" data-width="1080" data-height="1920" data-fps="30">
      <img id="paper" class="clip" src="assets/paper.png" alt="" data-start="0" data-duration="{DUR}" data-track-index="0" />
      {"".join(scene_html)}
      {OVER}
      <div id="brand" class="clip" data-start="25.95" data-duration="4.05" data-track-index="13" style="z-index:44"><div id="brand-in" class="brand">FOOTBALL ON CANVAS</div></div>
      {chr(10).join("      " + c for c in cap_html)}
      {chr(10).join("      " + a for a in audio_html)}
    </div>
    <script>
      {body_js}
    </script>
  </body>
</html>
'''
    OUT.write_text(html)
    print("wrote", OUT, "groups", len(groups), "words", len(words))

build()
