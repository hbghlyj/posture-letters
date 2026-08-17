#!/usr/bin/env python3
"""Build the self-contained browser specimen for Posture Master."""
from __future__ import annotations

import base64
from pathlib import Path

ROOT = Path(__file__).resolve().parent
font_data = base64.b64encode((ROOT / "posture-master.woff2").read_bytes()).decode("ascii")
print_data = base64.b64encode((ROOT / "assets/original-print.png").read_bytes()).decode("ascii")

html = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#efe1c4">
<title>Posture Master — a contorted human alphabet</title>
<style>
@font-face {
  font-family: "Posture Master";
  src: url(data:font/woff2;base64,__FONT_DATA__) format("woff2");
  font-style: normal;
  font-weight: 400;
  font-display: swap;
}
:root {
  --paper:#efe1c4;
  --paper-light:#f8f0df;
  --ink:#17243a;
  --red:#de493b;
  --red-dark:#a92f28;
  --rule:#bca680;
  --muted:#695e50;
  --lime:#c6d75e;
  --display-size:clamp(72px, 14vw, 198px);
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{
  margin:0;
  color:var(--ink);
  background:
    radial-gradient(circle at 16% 12%,rgba(255,255,255,.65),transparent 25rem),
    repeating-linear-gradient(0deg,transparent 0 5px,rgba(89,59,28,.018) 5px 6px),
    var(--paper);
  font-family:Georgia,"Times New Roman",serif;
  overflow-x:hidden;
}
button,input,textarea{font:inherit;color:inherit}
a{color:inherit}
.skip-link{position:absolute;top:-60px;left:1rem;background:var(--ink);color:white;padding:.8rem 1rem;z-index:20}
.skip-link:focus{top:1rem}
.masthead{
  min-height:100vh;
  border:10px solid var(--ink);
  position:relative;
  display:flex;
  flex-direction:column;
}
.masthead::before,.masthead::after{content:"";position:absolute;inset:10px;border:1px solid var(--rule);pointer-events:none}
.masthead::after{inset:18px;border-color:rgba(23,36,58,.28)}
nav{
  position:relative;z-index:2;
  display:flex;align-items:center;justify-content:space-between;gap:1.5rem;
  padding:1.35rem clamp(1.5rem,4vw,4.5rem);
  border-bottom:1px solid var(--ink);
  text-transform:uppercase;letter-spacing:.12em;font:700 .72rem/1.2 Arial,sans-serif;
}
.brand{display:flex;align-items:center;gap:.8rem;text-decoration:none}
.brand-mark{font-family:"Posture Master";font-size:2.7rem;line-height:.6;color:var(--red)}
.nav-links{display:flex;gap:1.6rem;align-items:center}
.nav-links a{text-decoration:none;border-bottom:1px solid transparent}
.nav-links a:hover{border-color:currentColor}
.hero{
  width:min(1540px,100%);margin:auto;padding:clamp(3rem,7vw,7rem) clamp(1.5rem,6vw,7rem);
  display:grid;grid-template-columns:minmax(0,1fr) minmax(250px,.38fr);gap:clamp(2rem,5vw,6rem);align-items:end;
  position:relative;z-index:1;
}
.kicker{font:700 .72rem/1.5 Arial,sans-serif;letter-spacing:.2em;text-transform:uppercase;color:var(--red-dark);margin:0 0 1rem;display:flex;align-items:center;gap:.8rem}
.kicker::before{content:"";width:3rem;border-top:3px double currentColor}
h1{margin:0;font-family:"Posture Master";font-size:clamp(82px,12.3vw,202px);line-height:.72;letter-spacing:-.025em;font-weight:400;white-space:nowrap;color:var(--ink)}
h1 span{display:block}h1 span:last-child{color:var(--red);transform:translateX(.15em)}
.hero-copy{border-left:1px solid var(--ink);padding-left:clamp(1.25rem,3vw,2.5rem);padding-bottom:.5rem}
.hero-copy .issue{display:inline-block;background:var(--ink);color:var(--paper-light);font:700 .67rem Arial,sans-serif;letter-spacing:.13em;text-transform:uppercase;padding:.5rem .7rem;transform:rotate(-1.5deg);margin-bottom:1.3rem}
.hero-copy h2{font-size:clamp(1.55rem,2.4vw,2.55rem);font-weight:normal;line-height:1.03;margin:0 0 1rem;font-style:italic}
.hero-copy p{line-height:1.62;color:var(--muted);margin:0 0 1.5rem}
.actions{display:flex;flex-wrap:wrap;gap:.7rem}
.button{display:inline-flex;align-items:center;gap:.55rem;border:1px solid var(--ink);padding:.75rem .9rem;text-decoration:none;text-transform:uppercase;letter-spacing:.1em;font:700 .65rem Arial,sans-serif;background:var(--paper-light);box-shadow:3px 3px 0 var(--ink);transition:.15s transform,.15s box-shadow}
.button:hover{transform:translate(2px,2px);box-shadow:1px 1px 0 var(--ink)}
.button.primary{background:var(--red);color:#fff8ea}
.hero-foot{position:relative;z-index:1;border-top:1px solid var(--ink);display:grid;grid-template-columns:auto 1fr auto;align-items:center;gap:1.2rem;padding:.8rem clamp(1.5rem,4vw,4.5rem);font:700 .65rem Arial,sans-serif;letter-spacing:.12em;text-transform:uppercase}
.hero-foot .line{height:1px;background:var(--rule)}
.ticker{background:var(--red);color:#fff7e4;overflow:hidden;border-bottom:1px solid var(--ink);border-top:1px solid var(--ink);padding:.55rem 0}
.ticker-track{width:max-content;font-family:"Posture Master";font-size:3.6rem;line-height:.75;word-spacing:.1em;animation:parade 30s linear infinite}
@keyframes parade{to{transform:translateX(-50%)}}
section{position:relative}
.section-head{display:flex;align-items:end;justify-content:space-between;gap:2rem;margin-bottom:2rem}
.eyebrow{margin:0 0 .55rem;font:700 .68rem Arial,sans-serif;letter-spacing:.17em;text-transform:uppercase;color:var(--red-dark)}
.section-head h2,.reference-copy h2{font-weight:normal;font-size:clamp(2.4rem,5vw,5.7rem);line-height:.88;margin:0;letter-spacing:-.045em}
.section-no{font-family:"Posture Master";font-size:5.5rem;line-height:.65;color:var(--red)}
.lab{padding:clamp(4rem,8vw,8rem) clamp(1.3rem,5vw,5.5rem);background:var(--paper-light);border-bottom:1px solid var(--ink)}
.controls{display:grid;grid-template-columns:minmax(220px,1.5fr) minmax(190px,.7fr) auto;gap:1rem;align-items:end;padding:1rem;border:1px solid var(--ink);background:var(--paper);box-shadow:5px 5px 0 var(--ink);position:relative;z-index:2}
.control label,.control-title{display:block;font:700 .61rem Arial,sans-serif;letter-spacing:.13em;text-transform:uppercase;margin-bottom:.5rem}
.control input[type="text"]{width:100%;border:0;border-bottom:1px solid var(--ink);background:transparent;padding:.45rem .1rem;font-size:1rem;outline:none}
.control input[type="range"]{width:100%;accent-color:var(--red)}
.swatches{display:flex;gap:.45rem;padding-bottom:.2rem}.swatch{width:1.8rem;height:1.8rem;border:1px solid var(--ink);border-radius:50%;cursor:pointer;padding:0}.swatch[aria-pressed="true"]{outline:3px double var(--ink);outline-offset:2px}.swatch.navy{background:#17243a}.swatch.red{background:#de493b}.swatch.green{background:#3e673d}
.stage-wrap{padding-top:2rem}.stage{
  min-height:420px;border:1px solid var(--ink);background:#efe1c4;display:flex;align-items:center;justify-content:center;text-align:center;padding:clamp(1rem,4vw,4rem);overflow:hidden;
  background-image:linear-gradient(rgba(23,36,58,.07) 1px,transparent 1px),linear-gradient(90deg,rgba(23,36,58,.07) 1px,transparent 1px);background-size:24px 24px;
}
#stageText{font-family:"Posture Master";font-size:var(--display-size);font-weight:400;line-height:.92;letter-spacing:.015em;color:var(--ink);max-width:100%;overflow-wrap:anywhere}
.stage-note{display:flex;justify-content:space-between;gap:1rem;margin-top:.65rem;font:italic .8rem Georgia,serif;color:var(--muted)}
.roster{padding:clamp(4rem,8vw,8rem) clamp(1.3rem,5vw,5.5rem);border-bottom:1px solid var(--ink)}
.glyph-grid{display:grid;grid-template-columns:repeat(7,1fr);border-top:1px solid var(--ink);border-left:1px solid var(--ink)}
.glyph-card{min-width:0;aspect-ratio:.78;border:0;border-right:1px solid var(--ink);border-bottom:1px solid var(--ink);background:rgba(248,240,223,.45);cursor:pointer;position:relative;display:flex;align-items:center;justify-content:center;padding:.8rem;transition:.18s background,.18s color}
.glyph-card:hover,.glyph-card:focus{background:var(--red);color:#fff8e8;outline:0}
.glyph-card .char{font-family:"Posture Master";font-size:clamp(3.7rem,7vw,8rem);line-height:.8}
.glyph-card .label{position:absolute;top:.55rem;left:.65rem;font:700 .65rem Arial,sans-serif;letter-spacing:.1em}
.glyph-card .solo{position:absolute;right:.45rem;bottom:.45rem;font:italic .62rem Georgia,serif;opacity:.65}
.anatomy{display:grid;grid-template-columns:1fr 1fr;min-height:680px;border-bottom:1px solid var(--ink)}
.anatomy-art{background:var(--ink);color:var(--paper);display:flex;align-items:center;justify-content:center;padding:4rem;position:relative;overflow:hidden}
.anatomy-art .big-pose{font-family:"Posture Master";font-size:min(56vw,42rem);line-height:.6;color:var(--paper);transform:rotate(-5deg)}
.callout{position:absolute;font:700 .62rem Arial,sans-serif;letter-spacing:.12em;text-transform:uppercase;color:var(--lime);display:flex;align-items:center;gap:.5rem}.callout::after{content:"";display:block;width:5vw;border-top:1px solid currentColor}.callout.one{top:18%;left:7%}.callout.two{right:6%;top:47%;flex-direction:row-reverse}.callout.three{bottom:12%;left:12%}
.anatomy-copy{padding:clamp(3rem,7vw,8rem);display:flex;flex-direction:column;justify-content:center}
.anatomy-copy h2{font-size:clamp(2.5rem,5vw,5.6rem);font-weight:normal;line-height:.88;margin:0 0 2rem;letter-spacing:-.04em}
.facts{list-style:none;margin:0;padding:0;border-top:1px solid var(--ink)}.facts li{display:grid;grid-template-columns:2.5rem 1fr;gap:1rem;padding:1.1rem 0;border-bottom:1px solid var(--rule);line-height:1.5}.facts b{font:700 .68rem Arial,sans-serif;color:var(--red)}
.reference{display:grid;grid-template-columns:1.15fr .85fr;gap:clamp(2rem,6vw,7rem);padding:clamp(4rem,9vw,9rem) clamp(1.3rem,5vw,5.5rem);background:var(--paper-light);border-bottom:1px solid var(--ink);align-items:center}
.print-frame{background:#fff9ed;padding:clamp(.7rem,2vw,1.6rem);border:1px solid var(--ink);box-shadow:10px 10px 0 var(--red);transform:rotate(-1deg)}.print-frame img{display:block;width:100%;height:auto;filter:saturate(.8) contrast(1.04)}.print-frame figcaption{font:italic .72rem Georgia,serif;margin-top:.7rem;color:var(--muted)}
.reference-copy p{font-size:1.08rem;line-height:1.7;color:var(--muted)}.dropcap:first-letter{float:left;font-family:"Posture Master";font-size:5.7rem;line-height:.65;color:var(--red);padding:.3rem .55rem .2rem 0}
.download{padding:clamp(4rem,9vw,9rem) clamp(1.3rem,5vw,5.5rem);text-align:center;background:var(--red);color:#fff7e7;position:relative;overflow:hidden}.download::before{content:"ABCDEFGHIJKLMNOPQRSTUVWXYZ";font-family:"Posture Master";font-size:17rem;line-height:1;white-space:nowrap;position:absolute;left:-2rem;top:50%;transform:translateY(-50%);opacity:.07;pointer-events:none}.download>*{position:relative}.download h2{font-size:clamp(3rem,8vw,8rem);font-weight:normal;line-height:.85;margin:0 0 1.2rem;letter-spacing:-.05em}.download p{max-width:45rem;margin:0 auto 2rem;line-height:1.6}.download-actions{display:flex;justify-content:center;flex-wrap:wrap;gap:.8rem}.download .button{background:#fff7e7;color:var(--ink)}
footer{display:flex;justify-content:space-between;gap:1rem;padding:1.4rem clamp(1.3rem,5vw,5.5rem);background:var(--ink);color:var(--paper);font:700 .62rem Arial,sans-serif;letter-spacing:.11em;text-transform:uppercase}
@media(max-width:900px){.hero{grid-template-columns:1fr;align-items:start}.hero-copy{max-width:38rem}.controls{grid-template-columns:1fr 1fr}.controls .control:first-child{grid-column:1/-1}.glyph-grid{grid-template-columns:repeat(4,1fr)}.anatomy,.reference{grid-template-columns:1fr}.anatomy-art{min-height:520px}.reference-copy{order:-1}.nav-links{display:none}}
@media(max-width:560px){.masthead{border-width:6px}.hero{padding-top:4rem;padding-bottom:4rem}h1{font-size:20vw}.hero-copy{border-left:0;border-top:1px solid;padding:1.5rem 0 0}.hero-foot{grid-template-columns:1fr;text-align:center}.hero-foot .line{display:none}.controls{grid-template-columns:1fr}.controls .control:first-child{grid-column:auto}.glyph-grid{grid-template-columns:repeat(2,1fr)}.stage{min-height:330px}.section-head{align-items:start}.section-no{font-size:3.6rem}.anatomy-art{min-height:400px;padding:2rem}.download h2{font-size:15vw}footer{flex-direction:column;text-align:center}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}.ticker-track{animation:none}.button{transition:none}}
</style>
</head>
<body>
<a class="skip-link" href="#main">Skip to specimen</a>
<header class="masthead">
  <nav aria-label="Main navigation">
    <a class="brand" href="#"><span class="brand-mark" aria-hidden="true">P</span><span>Posture Master<br>Type Foundry*</span></a>
    <div class="nav-links"><a href="#playground">Try it</a><a href="#alphabet">Alphabet</a><a href="#source">The print</a><a href="#get">Download</a></div>
    <span>No. 26½</span>
  </nav>
  <div class="hero">
    <div>
      <p class="kicker">A contorted human alphabet</p>
      <h1 aria-label="Posture Master"><span>POSTURE</span><span>MASTER</span></h1>
    </div>
    <div class="hero-copy">
      <span class="issue">24 historical poses · 2 editorial letters</span>
      <h2>The alphabet has never looked so uncomfortable.</h2>
      <p>A funny display face reconstructing the 24 surreal body poses in an eighteenth-century posture alphabet, with clearly marked editorial J and U forms for modern A–Z coverage.</p>
      <div class="actions"><a class="button primary" href="#playground">Bend some words ↓</a><a class="button" href="posture-master.woff2" download>Get WOFF2</a></div>
    </div>
  </div>
  <div class="hero-foot"><span>Single bodies · hat-and-shoe serifs</span><span class="line"></span><span>Improbable letterforms · Absolutely no warm-up</span></div>
</header>
<div class="ticker" aria-hidden="true"><div class="ticker-track">ABCDEFGHIJKLMNOPQRSTUVWXYZ - ABCDEFGHIJKLMNOPQRSTUVWXYZ - ABCDEFGHIJKLMNOPQRSTUVWXYZ - ABCDEFGHIJKLMNOPQRSTUVWXYZ - </div></div>
<main id="main">
<section class="lab" id="playground">
  <div class="section-head"><div><p class="eyebrow">Open practice</p><h2>Make them perform.</h2></div><div class="section-no" aria-hidden="true">A</div></div>
  <div class="controls" aria-label="Type specimen controls">
    <div class="control"><label for="copyInput">Your text</label><input id="copyInput" type="text" value="BENDY TYPE!" maxlength="48" autocomplete="off"></div>
    <div class="control"><label for="sizeInput">Point size · <output id="sizeOutput">148</output></label><input id="sizeInput" type="range" min="52" max="240" value="148"></div>
    <div class="control"><span class="control-title">Ink</span><div class="swatches"><button class="swatch navy" data-color="#17243a" aria-label="Navy ink" aria-pressed="true"></button><button class="swatch red" data-color="#de493b" aria-label="Red ink" aria-pressed="false"></button><button class="swatch green" data-color="#3e673d" aria-label="Green ink" aria-pressed="false"></button></div></div>
  </div>
  <div class="stage-wrap"><div class="stage"><div id="stageText" role="status">BENDY TYPE!</div></div><div class="stage-note"><span>Uppercase or lowercase: the same acrobatic cast.</span><span>Tap a glyph below to rehearse it.</span></div></div>
</section>
<section class="roster" id="alphabet">
  <div class="section-head"><div><p class="eyebrow">The company</p><h2>Twenty-six solo acts.</h2></div><div class="section-no" aria-hidden="true">Z</div></div>
  <div class="glyph-grid" id="glyphGrid" aria-label="A to Z character set"></div>
</section>
<section class="anatomy">
  <div class="anatomy-art" aria-label="A large Posture Master ampersand substitute: letter R"><span class="big-pose" aria-hidden="true">R</span><span class="callout one">Cocked hat serif</span><span class="callout two">Torso under pressure</span><span class="callout three">Outward shoe serif</span></div>
  <div class="anatomy-copy"><p class="eyebrow">Anatomy of a stunt</p><h2>Built from heads, hands, feet & nerve.</h2><ol class="facts"><li><b>01</b><span><strong>The approved construction comes first.</strong> Every visible leg wears full short trousers ending in a below-knee cuff, then swells through a modeled stockinged calf before tapering into its source-directed shoe. A keeps its left-facing shoes; B shortens its loop arms and lower-bowl leg around a visible knee; I restores a realistic rigid-body ratio; K bends into a two-finger hand serif; M retains cuffed impossible calf pillars; N grounds head and knee while outlining its foreground arm; O inverts its face, clasps its apex hands, and marks visible side joints; P shortens both backward loop arms; Q articulates its inverted leg ring, inverts its bottom face like O, and shortens its shoulder-attached tail; R corrects its planted shoe; and W lowers the outer knees to baseline hands with distinct index fingers and thumbs.</span></li><li><b>02</b><span><strong>Costume becomes typography.</strong> Gathered knee-breeches, cuffs, calf muscles, hat brims, and source-directed shoes remain attached to the performer’s actual joints and endpoints, turning period dress into anatomical letter structure.</span></li><li><b>03</b><span><strong>Web ready.</strong> WOFF2, WOFF and TTF are included, with uppercase, lowercase aliases and essential punctuation.</span></li><li><b>04</b><span><strong>Fair warning.</strong> The poses are typographic fiction, not fitness instruction.</span></li></ol></div>
</section>
<section class="reference" id="source">
  <figure class="print-frame"><img src="data:image/png;base64,__PRINT_DATA__" alt="The supplied historical print showing figures arranged as alphabetic letters"><figcaption>The supplied visual reference: “The Comical Hotch-Potch, or the Alphabet turn’d Posture-Master.”</figcaption></figure>
  <div class="reference-copy"><p class="eyebrow">From the print room</p><h2>An old joke, freshly stretched.</h2><p class="dropcap">The source print stages a 24-letter alphabet as bodily comedy: bows, bridges, balances and impossible hinges. Each cell was isolated and enlarged so its exact surreal pose construction could guide the corresponding digital glyph.</p><p>The result preserves the historical body topology in monochrome outlines rather than tracing clothing color, paper texture, or raster shading. Anatomically placed below-knee breeches, gathered cuffs, swelling calf muscles, hat brims, and source-directed shoe silhouettes supply the period costume structure and serif treatment. I combines the source’s straight rigidity with ordinary head/trunk/leg ratios. N places its inverted head and bent knee on one ground plane and separates the foreground sleeve from the blue diagonal with a narrow outline. O turns its bottom face upside down, looks into the counter, joins smooth shoulder/elbow arcs, marks visible side knee/elbow joints, and interlocks its apex hands. P uses two compact, normally proportioned backward arm routes. Q makes its ring from cuffed bent legs with joined apex shoes, inverts its bottom face like O, shortens the shoulder-attached tail arm, and gives it a visible hand. R points its planted shoe to the source-right, while W lowers the outer knees to the baseline and shows distinct supporting index fingers and thumbs. M retains its upward face, cupping hands, paired buttocks, central cleft, cuffed calf pillars, and outward shoes without the former center appendage; K still folds three fingers while projecting thumb and index. G, O, and Q remain free of the former dangling decorative artifacts. J and U are labeled editorial interpolations because they do not appear in the 1782 print.</p></div>
</section>
<section class="download" id="get"><h2>Limber up your headlines.</h2><p>Install the desktop TTF, serve the compact WOFF2 on the web, or inspect every vector pose in the SVG glyph sheet.</p><div class="download-actions"><a class="button" href="posture-master.ttf" download>Download TTF</a><a class="button" href="posture-master.woff2" download>Download WOFF2</a><a class="button" href="posture-master.woff" download>Download WOFF</a><a class="button" href="glyph-sheet.svg" download>View SVG sheet</a></div></section>
</main>
<footer><span>Posture Master · Regular · Version 1.000</span><span>*No actual foundry. Several imaginary sprains.</span></footer>
<script>
(() => {
  const alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
  const grid = document.querySelector("#glyphGrid");
  const stage = document.querySelector("#stageText");
  const input = document.querySelector("#copyInput");
  const slider = document.querySelector("#sizeInput");
  const output = document.querySelector("#sizeOutput");

  for (const letter of alphabet) {
    const button = document.createElement("button");
    button.className = "glyph-card";
    button.type = "button";
    button.setAttribute("aria-label", `Show letter ${letter} in playground`);
    button.innerHTML = `<span class="label">${letter}</span><span class="char" aria-hidden="true">${letter}</span><span class="solo">solo</span>`;
    button.addEventListener("click", () => {
      input.value = letter;
      stage.textContent = letter;
      document.querySelector("#playground").scrollIntoView({behavior:"smooth"});
    });
    grid.appendChild(button);
  }
  input.addEventListener("input", () => { stage.textContent = input.value || " "; });
  slider.addEventListener("input", () => {
    output.value = slider.value;
    stage.style.fontSize = `${slider.value}px`;
  });
  document.querySelectorAll(".swatch").forEach((swatch) => swatch.addEventListener("click", () => {
    document.querySelectorAll(".swatch").forEach((item) => item.setAttribute("aria-pressed", "false"));
    swatch.setAttribute("aria-pressed", "true");
    stage.style.color = swatch.dataset.color;
  }));
})();
</script>
</body>
</html>
'''

html = html.replace("__FONT_DATA__", font_data).replace("__PRINT_DATA__", print_data)
(ROOT / "index.html").write_text(html, encoding="utf-8")
print(f"Built {ROOT / 'index.html'} ({len(html):,} characters)")
