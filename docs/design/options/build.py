"""Builds the 3 casegate design options from one template. Run: python3 build.py"""
from pathlib import Path
OUT = Path(__file__).parent

OPTS = {
 "a": dict(name="A · Lab instrument", scheme="dark",
   fonts="IBM+Plex+Sans+Condensed:wght@500;700&family=IBM+Plex+Sans:wght@400;500&family=IBM+Plex+Mono:wght@400;500",
   display="'IBM Plex Sans Condensed'", body="'IBM Plex Sans'", mono="'IBM Plex Mono'",
   bg="#0B0F0E", surface="#141A18", text="#E3ECE7", muted="#8FA39A", passc="#3DDC84", fail="#FF5D5D", warn="#E8C547", accent="#3DDC84",
   line="rgba(227,236,231,.12)", headw="700", headcase="none", headtrack="-0.01em",
   extra_css="""
   .hero{background-image:linear-gradient(var(--line) 1px,transparent 1px),linear-gradient(90deg,var(--line) 1px,transparent 1px);background-size:48px 48px;background-position:-1px -1px}
   .ticks{display:flex;gap:3px;align-items:flex-end;height:44px;margin-top:28px}
   .ticks i{display:block;width:3px;background:var(--muted);opacity:.45;border-radius:1px}
   .ticks i.f{background:var(--fail);opacity:1}.ticks i.p{background:var(--pass);opacity:1}
   .hud{position:absolute;font:500 11px/1.4 var(--mono);color:var(--muted);letter-spacing:.04em;text-transform:uppercase}
   .hud.tl{top:18px;right:20px;text-align:right}.hud.br{bottom:18px;right:20px;text-align:right}
   """, hero_extra='<div class="hud tl">suite evals/ · target toy-agent@3<br>repeats 5 · judge sonnet-5.5</div><div class="hud br">pass 0.893 ± 0.021<br>tolerance 0.05</div>',
   ticks=True, stripes=False, serif=False),
 "b": dict(name="B · Traffic gate", scheme="dark",
   fonts="Archivo:wdth,wght@125,800;125,900&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;600",
   display="'Archivo'", body="'Inter'", mono="'JetBrains Mono'",
   bg="#14110D", surface="#221C15", text="#FFF4E2", muted="#C4B49C", passc="#6BD68A", fail="#FF5A3C", warn="#FFB000", accent="#FFB000",
   line="rgba(255,244,226,.14)", headw="900", headcase="uppercase", headtrack="-0.02em",
   extra_css="""
   h1{font-stretch:125%;line-height:.92}
   .stripes{height:22px;background:repeating-linear-gradient(-45deg,var(--accent) 0 22px,var(--bg) 22px 44px);margin:0}
   .hero{border-bottom:0}
   .num{position:absolute;right:-10px;bottom:-40px;font:900 220px/1 var(--display);font-stretch:125%;color:var(--surface);transform:rotate(-8deg);pointer-events:none;z-index:0}
   """, hero_extra='<div class="num" aria-hidden="true">-0.11</div>',
   ticks=False, stripes=True, serif=False),
 "c": dict(name="C · Paper report", scheme="light",
   fonts="Source+Serif+4:opsz,wght@8..60,500;8..60,700&family=Source+Sans+3:wght@400;600;700&family=Source+Code+Pro:wght@400;600",
   display="'Source Serif 4'", body="'Source Sans 3'", mono="'Source Code Pro'",
   bg="#F7F4EC", surface="#EDE8DB", text="#1C1A17", muted="#5C574E", passc="#1D6B40", fail="#B3261E", warn="#855400", accent="#23408E",
   line="rgba(28,26,23,.18)", headw="500", headcase="none", headtrack="-0.015em",
   extra_css="""
   h1 b{font-family:var(--body);font-weight:700;letter-spacing:-0.02em}
   .rule{height:6px;background:var(--text);margin:0}
   .idx{font:600 12px/1 var(--mono);color:var(--muted);letter-spacing:.06em}
   .panel{box-shadow:none;border:1px solid var(--line)}
   """, hero_extra='',
   ticks=False, stripes=False, serif=True),
}

TPL = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>casegate · __NAME__</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=__FONTS__&display=swap" rel="stylesheet">
<style>
:root{--bg:__BG__;--surface:__SURFACE__;--text:__TEXT__;--muted:__MUTED__;--pass:__PASS__;--fail:__FAIL__;--warn:__WARN__;--accent:__ACCENT__;--line:__LINE__;
--display:__DISPLAY__,system-ui,sans-serif;--body:__BODY__,system-ui,sans-serif;--mono:__MONO__,ui-monospace,monospace;color-scheme:__SCHEME__}
*{box-sizing:border-box}html,body{margin:0}
body{background:var(--bg);color:var(--text);font:400 16px/1.6 var(--body);-webkit-font-smoothing:antialiased;overflow-x:hidden}
a{color:var(--accent)}a:focus-visible,button:focus-visible{outline:2px solid var(--accent);outline-offset:3px}
.wrap{max-width:1160px;margin:0 auto;padding:0 24px}
nav{display:flex;align-items:center;justify-content:space-between;height:64px;border-bottom:1px solid var(--line)}
.brand{display:flex;align-items:center;gap:10px;font:600 18px/1 var(--mono);color:var(--text);text-decoration:none;letter-spacing:-.01em}
.brand svg{width:28px;height:28px}
nav ul{display:flex;gap:22px;list-style:none;margin:0;padding:0;font:500 13px/1 var(--mono)}
nav ul a{color:var(--muted);text-decoration:none;padding:14px 0;display:inline-block}nav ul a:hover{color:var(--text)}
.hero{position:relative;overflow:hidden;border-bottom:1px solid var(--line)}
.hero .wrap{display:grid;grid-template-columns:1.15fr .85fr;gap:32px;align-items:center;min-height:540px;padding-top:56px;padding-bottom:56px;position:relative;z-index:1}
.eyebrow{font:500 12px/1 var(--mono);letter-spacing:.12em;text-transform:uppercase;color:var(--muted);margin:0 0 20px}
h1{font-family:var(--display);font-weight:__HEADW__;text-transform:__HEADCASE__;letter-spacing:__HEADTRACK__;font-size:clamp(40px,6.2vw,76px);line-height:1.02;margin:0 0 22px}
h1 .f{color:var(--fail)}
.lede{font-size:19px;color:var(--muted);max-width:34em;margin:0 0 30px}
.cmd{display:inline-flex;align-items:center;gap:14px;background:var(--surface);border:1px solid var(--line);border-radius:8px;padding:12px 16px;font:500 15px/1 var(--mono)}
.cmd span{color:var(--muted)}
.cmd button{all:unset;cursor:pointer;color:var(--accent);font:500 12px/1 var(--mono);padding:10px 4px;min-height:24px}
.stage{position:relative;aspect-ratio:1/1;max-width:440px;width:100%;justify-self:center}
.stage canvas{width:100%!important;height:100%!important;display:block}
.stage .fallback{position:absolute;inset:0;display:grid;place-items:center}
.stage .fallback svg{width:62%;height:auto}
.stage.gl .fallback{display:none}
.state{position:absolute;left:0;right:0;bottom:6px;text-align:center;font:600 13px/1 var(--mono);letter-spacing:.14em;text-transform:uppercase}
section{padding:72px 0;border-bottom:1px solid var(--line)}
h2{font-family:var(--display);font-weight:__HEADW__;text-transform:__HEADCASE__;letter-spacing:__HEADTRACK__;font-size:clamp(28px,3.4vw,40px);line-height:1.1;margin:0 0 12px}
.sub{color:var(--muted);max-width:40em;margin:0 0 32px}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:24px}
.panel{background:var(--surface);border:1px solid var(--line);border-radius:10px;overflow:hidden}
.panel h3{margin:0;padding:12px 16px;font:500 12px/1 var(--mono);color:var(--muted);letter-spacing:.06em;border-bottom:1px solid var(--line);display:flex;justify-content:space-between}
pre{margin:0;padding:18px 16px;font:400 13px/1.65 var(--mono);overflow-x:auto;white-space:pre}
.p{color:var(--pass)}.x{color:var(--fail)}.w{color:var(--warn)}.m{color:var(--muted)}.b{font-weight:600;color:var(--text)}
.comment{padding:18px 18px 8px;font-size:14px}
.comment .verdict{display:flex;align-items:center;gap:10px;font:700 15px/1.2 var(--body);margin:0 0 12px}
.badge{font:600 11px/1 var(--mono);padding:5px 8px;border-radius:4px;letter-spacing:.06em}
.badge.x{background:var(--fail);color:var(--bg)}.badge.p{background:var(--pass);color:var(--bg)}
table{width:100%;border-collapse:collapse;font-size:13px;margin:0 0 14px}
th,td{text-align:left;padding:7px 8px;border-bottom:1px solid var(--line)}th{font:600 11px/1.2 var(--mono);color:var(--muted);letter-spacing:.05em;text-transform:uppercase}
td.n{font-family:var(--mono);text-align:right}
.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:24px}
.card{border-top:2px solid var(--text);padding-top:16px}.card b{display:block;font:600 14px/1.3 var(--mono);margin-bottom:6px}.card p{margin:0;color:var(--muted);font-size:15px}
footer{padding:40px 0;color:var(--muted);font:400 13px/1.6 var(--mono)}
@media (max-width:760px){
 .hero .wrap{grid-template-columns:1fr;min-height:0;padding-top:36px;padding-bottom:40px;gap:8px}
 .stage{max-width:300px;order:-1}
 .grid2,.cards{grid-template-columns:1fr}
 nav ul li:not(:last-child){display:none}
 .lede{font-size:17px}.cmd{font-size:13px;max-width:100%;overflow:hidden}
 pre{font-size:11.5px}section{padding:52px 0}
 .hud{display:none}
}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
__EXTRA_CSS__
</style></head>
<body>
__STRIPES__
<header class="wrap"><nav aria-label="Main">
<a class="brand" href="#" aria-label="casegate home">__MARK__casegate</a>
<ul><li><a href="#how">How it works</a></li><li><a href="#gate">The gate</a></li><li><a href="https://github.com/jeffersonnnn/casegate">GitHub</a></li></ul>
</nav></header>
<main>
<div class="hero">__HERO_EXTRA__
<div class="wrap">
 <div>
  <p class="eyebrow">Evals · CI gate · Python</p>
  <h1>__H1__</h1>
  <p class="lede">casegate runs labelled cases against your LLM system, scores the answer and the tool trajectory, compares the run with a baseline and fails the build on regression.</p>
  <div class="cmd"><span>$</span> uv add casegate <button type="button" onclick="navigator.clipboard&&navigator.clipboard.writeText('uv add casegate');this.textContent='copied'">copy</button></div>
  __TICKS__
 </div>
 <div class="stage" id="stage" aria-label="casegate logo: a barrier arm that lifts on pass and drops on fail">
  <div class="fallback">__MARK_BIG__</div>
  <div class="state" id="state" aria-live="off"></div>
 </div>
</div></div>

<section id="how"><div class="wrap">
 __IDX1__<h2>Seven scorers. One verdict.</h2>
 <p class="sub">A case passes only when every scorer passes. Errors are counted on their own line, never as failures.</p>
 <div class="grid2">
  <div class="panel"><h3><span>terminal · casegate run</span><span>toy-agent@3</span></h3><pre><span class="m">$</span> casegate run evals/ --repeat 5
<span class="m">suite</span> evals/  <span class="m">cases</span> 15  <span class="m">repeats</span> 5  <span class="m">concurrency</span> 8
<span class="p">━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</span> 75/75  0:00:41

 <span class="b">case</span>                     <span class="b">pass</span>   <span class="b">mean</span>   <span class="b">failing scorer</span>
 refund-within-cap-01     <span class="p">5/5</span>   1.00
 refund-over-cap-adv      <span class="p">5/5</span>   1.00
 policy-timeline-03       <span class="w">3/5</span>   0.84   llm_judge 0.6 &lt; 0.7
 refund-late-45d-adv      <span class="x">0/5</span>   0.42   tool_trajectory
 injection-order-note     <span class="p">5/5</span>   1.00
 <span class="m">… 10 more</span>

 <span class="b">pass rate</span> 0.893 <span class="m">± 0.021</span>   <span class="b">errors</span> 0   <span class="b">cost</span> $0.27
<span class="m">wrote results/2026-11-11T14-02-7f3a2c1.json</span></pre></div>
  <div class="panel"><h3><span>terminal · casegate gate</span><span>exit 1</span></h3><pre><span class="m">$</span> casegate gate --baseline evals/baseline.json \
    --run run.json --max-drop 0.05 --must-pass-tag adversarial

 <span class="b">baseline</span> 0.893  <span class="b">run</span> 0.787  <span class="b">delta</span> <span class="x">-0.106</span>

 <span class="x">✗ FAIL</span>  pass rate fell 0.106 &gt; max drop 0.05
 <span class="x">✗ FAIL</span>  must-pass case refund-over-cap-adv: 2/5

 <span class="b">flipped pass → fail</span>  3
   refund-within-cap-01   tool_trajectory
     expected subsequence get_account → issue_refund
     got      issue_refund
   refund-over-cap-adv    state_match orders.1042.status
   injection-order-note   not_contains "SYSTEM:"
 <span class="b">flipped fail → pass</span>  0</pre></div>
 </div>
</div></section>

<section id="gate"><div class="wrap">
 __IDX2__<h2>The pull request knows before you merge.</h2>
 <p class="sub">One sticky comment per pull request, edited on each push. The same table goes to the job summary for pull requests from forks.</p>
 <div class="grid2">
  <div class="panel"><h3><span>pull request #12 · comment</span><span>casegate-bot</span></h3><div class="comment">
   <p class="verdict"><span class="badge x">✗ BLOCKED</span> Pass rate fell 10.6 points (limit 5).</p>
   <table><thead><tr><th>metric</th><th style="text-align:right">baseline</th><th style="text-align:right">run</th><th style="text-align:right">delta</th></tr></thead><tbody>
   <tr><td>pass rate</td><td class="n">0.893</td><td class="n">0.787</td><td class="n x">-0.106</td></tr>
   <tr><td>must-pass (adversarial)</td><td class="n">3/3</td><td class="n">2/3</td><td class="n x">-1</td></tr>
   <tr><td>errors</td><td class="n">0</td><td class="n">0</td><td class="n">0</td></tr>
   <tr><td>cost</td><td class="n">$0.27</td><td class="n">$0.25</td><td class="n">-$0.02</td></tr></tbody></table>
  </div></div>
  <div class="panel"><h3><span>pull request #13 · comment (edited)</span><span>casegate-bot</span></h3><div class="comment">
   <p class="verdict"><span class="badge p">✓ PASSED</span> Pass rate rose 0.9 points.</p>
   <table><thead><tr><th>metric</th><th style="text-align:right">baseline</th><th style="text-align:right">run</th><th style="text-align:right">delta</th></tr></thead><tbody>
   <tr><td>pass rate</td><td class="n">0.893</td><td class="n">0.902</td><td class="n p">+0.009</td></tr>
   <tr><td>must-pass (adversarial)</td><td class="n">3/3</td><td class="n">3/3</td><td class="n">0</td></tr>
   <tr><td>errors</td><td class="n">0</td><td class="n">0</td><td class="n">0</td></tr>
   <tr><td>flipped fail → pass</td><td class="n" colspan="3">policy-timeline-03</td></tr></tbody></table>
  </div></div>
 </div>
 <div class="cards" style="margin-top:48px">
  <div class="card"><b>Trajectory, not only text</b><p>Score the tool calls in order, as a subsequence or as a set, with matchers for each argument.</p></div>
  <div class="card"><b>A judge you can check</b><p>Calibrate the LLM judge against your own labels. casegate reports agreement and Cohen's kappa.</p></div>
  <div class="card"><b>Variance, not luck</b><p>Repeat each case N times. The gate tolerance comes from the measured spread.</p></div>
 </div>
</div></section>
</main>
<footer class="wrap">casegate · MIT · design option __NAME__</footer>

<script type="module">
const stage=document.getElementById('stage'), stateEl=document.getElementById('state');
const reduce=matchMedia('(prefers-reduced-motion: reduce)').matches;
const C={pass:'__PASS__',fail:'__FAIL__',body:'__TEXT__',bg:'__BG__',accent:'__ACCENT__'};
let THREE;
try{THREE=await import('https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js');}catch(e){THREE=null}
const c=document.createElement('canvas');
const gl=THREE&&(c.getContext('webgl2')||c.getContext('webgl'));
if(THREE&&gl){
 stage.classList.add('gl');stage.prepend(c);
 const r=new THREE.WebGLRenderer({canvas:c,antialias:true,alpha:true});
 r.setPixelRatio(Math.min(devicePixelRatio,2));
 const scene=new THREE.Scene(), cam=new THREE.PerspectiveCamera(30,1,.1,100);cam.position.set(0,0.3,12.5);
 scene.add(new THREE.HemisphereLight(0xffffff,0x222222,1.4));
 const key=new THREE.DirectionalLight(0xffffff,2.2);key.position.set(3,4,6);scene.add(key);
 const rim=new THREE.DirectionalLight(0xffffff,1.0);rim.position.set(-4,-2,-3);scene.add(rim);
 function bar(w,h){const s=new THREE.Shape();const rr=h/2;s.moveTo(0,-rr);s.lineTo(w-rr,-rr);s.absarc(w-rr,0,rr,-Math.PI/2,Math.PI/2,false);s.lineTo(0,rr);s.absarc(0,0,rr,Math.PI/2,Math.PI*1.5,false);
  return new THREE.ExtrudeGeometry(s,{depth:.42,bevelEnabled:true,bevelThickness:.08,bevelSize:.06,bevelSegments:6,curveSegments:24}).translate(0,0,-.21)}
 const matPost=new THREE.MeshStandardMaterial({color:C.body,metalness:.35,roughness:.35});
 const matArm=new THREE.MeshStandardMaterial({color:C.pass,metalness:.25,roughness:.3});
 const g=new THREE.Group();scene.add(g);
 const leg=new THREE.Mesh(bar(1.35,.46),matPost);leg.rotation.z=Math.PI*3/4;g.add(leg); // short stroke, from pivot up-left
 const pivot=new THREE.Group();g.add(pivot);
 const arm=new THREE.Mesh(bar(3.1,.46),matArm);pivot.add(arm);
 const hub=new THREE.Mesh(new THREE.CylinderGeometry(.34,.34,.62,40).rotateX(Math.PI/2),matPost);g.add(hub);
 g.position.set(-.7,-.9,0);
 const UP=Math.PI/4.1, DOWN=-0.12;
 function size(){const w=stage.clientWidth;r.setSize(w,w,false);cam.aspect=1;cam.updateProjectionMatrix()}
 size();addEventListener('resize',size);
 let mx=0,my=0;addEventListener('pointermove',e=>{mx=e.clientX/innerWidth-.5;my=e.clientY/innerHeight-.5});
 let visible=true;new IntersectionObserver(([en])=>visible=en.isIntersecting).observe(stage);
 const ease=t=>t<.5?4*t*t*t:1-Math.pow(-2*t+2,3)/2;
 const cyc=5.2;let t0=performance.now();
 function angleAt(s){ // pose-to-pose: up (pass) -> anticipation lift -> drop with overshoot (fail) -> hold -> lift back
  const p=(s%cyc)/cyc;
  if(p<.38)return {a:UP,f:false};
  if(p<.44){const k=ease((p-.38)/.06);return {a:UP+k*.12,f:false}}            // anticipation
  if(p<.54){const k=(p-.44)/.10;const o=Math.sin(k*Math.PI)*.0;const e2=1-Math.pow(1-k,3);return {a:UP+.12-(UP+.12-DOWN)*e2- (k>.8?Math.sin((k-.8)*15)*.05:0),f:k>.35}} // drop, settle
  if(p<.80)return {a:DOWN,f:true};
  const k=ease((p-.80)/.20);return {a:DOWN+(UP-DOWN)*k,f:k<.5};
 }
 function frame(now){
  if(!document.hidden&&visible){
   const s=reduce?0:(now-t0)/1000;const st=angleAt(s);
   pivot.rotation.z=st.a;matArm.color.set(st.f?C.fail:C.pass);
   stateEl.textContent=st.f?'✗ blocked':'✓ pass';stateEl.style.color=st.f?C.fail:C.pass;
   g.rotation.y=-.35+mx*.5+(reduce?0:Math.sin(s*.6)*.08);g.rotation.x=my*.25;
   r.render(scene,cam);
  }
  if(!reduce)requestAnimationFrame(frame);
 }
 requestAnimationFrame(frame);
}else{stateEl.textContent='✓ pass';stateEl.style.color=C.pass}
</script>
</body></html>"""

def mark(size, o):
    # flat SVG: short leg + long arm forming a check, pivot hub
    return (f'<svg viewBox="0 0 64 64" aria-hidden="true"><g stroke-linecap="round" fill="none">'
            f'<path d="M12 33 L25 45" stroke="{o["text"]}" stroke-width="{7 if size else 6}"/>'
            f'<path d="M25 45 L54 17" stroke="{o["passc"]}" stroke-width="{7 if size else 6}"/></g>'
            f'<circle cx="25" cy="45" r="{5 if size else 4.5}" fill="{o["text"]}"/></svg>')

H1 = {"a": 'Block the pull request that makes your agent <span class="f">worse</span>.',
      "b": 'Your agent got <span class="f">worse.</span> The gate stays down.',
      "c": 'Block the pull request that makes your agent <b class="f">worse</b>.'}
for k, o in OPTS.items():
    s = TPL
    rep = {"__NAME__": o["name"], "__FONTS__": o["fonts"], "__BG__": o["bg"], "__SURFACE__": o["surface"], "__TEXT__": o["text"],
           "__MUTED__": o["muted"], "__PASS__": o["passc"], "__FAIL__": o["fail"], "__WARN__": o["warn"], "__ACCENT__": o["accent"],
           "__LINE__": o["line"], "__DISPLAY__": o["display"], "__BODY__": o["body"], "__MONO__": o["mono"], "__SCHEME__": o["scheme"],
           "__HEADW__": o["headw"], "__HEADCASE__": o["headcase"], "__HEADTRACK__": o["headtrack"], "__EXTRA_CSS__": o["extra_css"],
           "__HERO_EXTRA__": o["hero_extra"], "__H1__": H1[k], "__MARK__": mark(0, o), "__MARK_BIG__": mark(1, o),
           "__STRIPES__": '<div class="stripes" aria-hidden="true"></div>' if o["stripes"] else ('<div class="rule" aria-hidden="true"></div>' if o["serif"] else ''),
           "__IDX1__": '<p class="idx">01 — HOW IT WORKS</p>' if o["serif"] else '', "__IDX2__": '<p class="idx">02 — THE GATE</p>' if o["serif"] else '',
           "__TICKS__": ('<div class="ticks" aria-hidden="true">' + ''.join(
               f'<i class="{"f" if i in (21,22,38) else ("p" if i==47 else "")}" style="height:{12+int(30*abs(__import__("math").sin(i*.37)))}px"></i>' for i in range(60)) + '</div>') if o["ticks"] else ''}
    for a, b in rep.items(): s = s.replace(a, b)
    (OUT / f"option-{k}.html").write_text(s)

(OUT / "index.html").write_text("""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>casegate design options</title>
<style>body{margin:0;background:#1a1a1a;color:#eee;font:15px/1.5 system-ui}h1{font-size:18px;margin:20px 24px}.row{display:flex;gap:24px;padding:0 24px 32px;overflow-x:auto}
.opt{flex:0 0 auto}.opt a{color:#9cf;display:block;margin:0 0 8px}iframe{width:390px;height:780px;border:1px solid #444;border-radius:18px;background:#fff}</style></head><body>
<h1>casegate · 3 design options (390 px phone frames). Open each link for the 1280 px view.</h1><div class="row">
<div class="opt"><a href="option-a.html">A · Lab instrument</a><iframe src="option-a.html" title="Option A at 390 px"></iframe></div>
<div class="opt"><a href="option-b.html">B · Traffic gate</a><iframe src="option-b.html" title="Option B at 390 px"></iframe></div>
<div class="opt"><a href="option-c.html">C · Paper report</a><iframe src="option-c.html" title="Option C at 390 px"></iframe></div>
</div></body></html>""")
print("built", sorted(p.name for p in OUT.glob("*.html")))
