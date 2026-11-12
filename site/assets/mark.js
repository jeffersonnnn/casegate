// The hero logo as a live three.js scene (docs/DESIGN.md §3-4). It lives in its own file so
// index.html stays under 250 lines. Any failure here (no network, no WebGL) leaves the
// fallback SVG in index.html, so the page still reads with JS off.
const stage = document.getElementById('stage');
const stateEl = document.getElementById('state');
const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
const C = { pass: '#3DDC84', fail: '#FF5D5D', body: '#E3ECE7' };

let THREE = null;
try { THREE = await import('https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js'); } catch (e) { THREE = null; }
const c = document.createElement('canvas');
c.setAttribute('aria-hidden', 'true');
const gl = THREE && (c.getContext('webgl2') || c.getContext('webgl'));

if (THREE && gl) {
  stage.classList.add('gl');
  stage.prepend(c);
  const r = new THREE.WebGLRenderer({ canvas: c, antialias: true, alpha: true });
  r.setPixelRatio(Math.min(devicePixelRatio, 2));
  const scene = new THREE.Scene();
  const cam = new THREE.PerspectiveCamera(30, 1, 0.1, 100);
  cam.position.set(0, 0.3, 12.5);
  scene.add(new THREE.HemisphereLight(0xffffff, 0x222222, 1.4));
  const key = new THREE.DirectionalLight(0xffffff, 2.2); key.position.set(3, 4, 6); scene.add(key);
  const rim = new THREE.DirectionalLight(0xffffff, 1.0); rim.position.set(-4, -2, -3); scene.add(rim);

  function bar(w, h) {
    const s = new THREE.Shape(); const rr = h / 2;
    s.moveTo(0, -rr); s.lineTo(w - rr, -rr); s.absarc(w - rr, 0, rr, -Math.PI / 2, Math.PI / 2, false);
    s.lineTo(0, rr); s.absarc(0, 0, rr, Math.PI / 2, Math.PI * 1.5, false);
    return new THREE.ExtrudeGeometry(s, { depth: 0.42, bevelEnabled: true, bevelThickness: 0.08, bevelSize: 0.06, bevelSegments: 6, curveSegments: 24 }).translate(0, 0, -0.21);
  }
  const matPost = new THREE.MeshStandardMaterial({ color: C.body, metalness: 0.35, roughness: 0.35 });
  const matArm = new THREE.MeshStandardMaterial({ color: C.pass, metalness: 0.25, roughness: 0.3 });
  const g = new THREE.Group(); scene.add(g);
  const leg = new THREE.Mesh(bar(1.35, 0.46), matPost); leg.rotation.z = Math.PI * 3 / 4; g.add(leg);
  const pivot = new THREE.Group(); g.add(pivot);
  pivot.add(new THREE.Mesh(bar(3.1, 0.46), matArm));
  g.add(new THREE.Mesh(new THREE.CylinderGeometry(0.34, 0.34, 0.62, 40).rotateX(Math.PI / 2), matPost));
  g.position.set(-0.7, -0.9, 0);

  const UP = Math.PI / 4.1, DOWN = -0.12, CYC = 5.2;
  const ease = t => t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
  // The logo cycle of docs/DESIGN.md §4, same as angleAt in docs/design/options/build.py.
  function angleAt(s) {
    const p = (s % CYC) / CYC;
    if (p < 0.38) return { a: UP, f: false };
    if (p < 0.44) { const k = ease((p - 0.38) / 0.06); return { a: UP + k * 0.12, f: false }; }
    if (p < 0.54) {
      const k = (p - 0.44) / 0.10; const e2 = 1 - Math.pow(1 - k, 3);
      return { a: UP + 0.12 - (UP + 0.12 - DOWN) * e2 - (k > 0.8 ? Math.sin((k - 0.8) * 15) * 0.05 : 0), f: k > 0.35 };
    }
    if (p < 0.80) return { a: DOWN, f: true };
    const k = ease((p - 0.80) / 0.20); return { a: DOWN + (UP - DOWN) * k, f: k < 0.5 };
  }

  let mx = 0, my = 0;
  if (!reduce) addEventListener('pointermove', e => { mx = e.clientX / innerWidth - 0.5; my = e.clientY / innerHeight - 0.5; });

  let lastFail = null;
  function draw(s) {
    const st = reduce ? { a: UP, f: false } : angleAt(s);
    pivot.rotation.z = st.a;
    matArm.color.set(st.f ? C.fail : C.pass);
    if (st.f !== lastFail) {
      stateEl.textContent = st.f ? '✗ blocked' : '✓ pass';
      stateEl.classList.toggle('x', st.f);
      lastFail = st.f;
    }
    g.rotation.y = -0.35 + (reduce ? 0 : mx * 0.5 + Math.sin(s * 0.6) * 0.08);
    g.rotation.x = reduce ? 0 : my * 0.25;
    r.render(scene, cam);
  }

  const t0 = performance.now();
  let visible = true, raf = 0;
  function frame(now) { raf = 0; draw((now - t0) / 1000); loop(); }
  function loop() { if (!reduce && visible && !document.hidden && !raf) raf = requestAnimationFrame(frame); }
  function stop() { if (raf) { cancelAnimationFrame(raf); raf = 0; } }

  function size() {
    const w = stage.clientWidth;
    r.setSize(w, w, false); cam.aspect = 1; cam.updateProjectionMatrix();
    draw((performance.now() - t0) / 1000);
  }
  new ResizeObserver(size).observe(stage);
  new IntersectionObserver(([en]) => { visible = en.isIntersecting; visible ? loop() : stop(); }).observe(stage);
  document.addEventListener('visibilitychange', () => { document.hidden ? stop() : loop(); });
  size();
  loop();
}
