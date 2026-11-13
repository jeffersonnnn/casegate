// casegate 3D mark for the launch videos. The scene is a copy of scripts/render_mark.html
// (docs/DESIGN.md §3): same geometry, materials, lights, camera and angleAt(t) (DESIGN §4).
// The videos never play the 5.2 s cycle free-running and never use the 25 fps GIF frames:
// each scene maps its own frame number to a cycle frame at 30 fps and renders that pose.
// Usage: CasegateMark.create(canvas, sizePx) -> Promise<{ render(cycleSeconds, rotY) -> { a, f } }>.
(function () {
  const UP = Math.PI / 4.1, DOWN = -0.12, CYC = 5.2;
  const ease = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
  // angleAt: verbatim from scripts/render_mark.html (the build.py function).
  function angleAt(s) {
    const p = (s % CYC) / CYC;
    if (p < 0.38) return { a: UP, f: false };
    if (p < 0.44) { const k = ease((p - 0.38) / 0.06); return { a: UP + k * 0.12, f: false }; }
    if (p < 0.54) {
      const k = (p - 0.44) / 0.1; const e2 = 1 - Math.pow(1 - k, 3);
      return { a: UP + 0.12 - (UP + 0.12 - DOWN) * e2 - (k > 0.8 ? Math.sin((k - 0.8) * 15) * 0.05 : 0), f: k > 0.35 };
    }
    if (p < 0.8) return { a: DOWN, f: true };
    const k = ease((p - 0.8) / 0.2); return { a: DOWN + (UP - DOWN) * k, f: k < 0.5 };
  }
  const PAL = { body: "#E3ECE7", pass: "#3DDC84", fail: "#FF5D5D" };
  let threeP = null;
  const loadThree = () =>
    (threeP = threeP || import("https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js"));

  async function create(canvas, size) {
    const THREE = await loadThree();
    const gl = canvas.getContext("webgl2", { alpha: true, antialias: true, preserveDrawingBuffer: true })
      || canvas.getContext("webgl", { alpha: true, antialias: true, preserveDrawingBuffer: true });
    const r = new THREE.WebGLRenderer({ canvas, context: gl, antialias: true, alpha: true, preserveDrawingBuffer: true });
    r.setPixelRatio(1); r.setClearColor(0x000000, 0); r.setSize(size, size, false);
    const scene = new THREE.Scene(), cam = new THREE.PerspectiveCamera(30, 1, 0.1, 100);
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
    const matPost = new THREE.MeshStandardMaterial({ color: PAL.body, metalness: 0.35, roughness: 0.35 });
    const matArm = new THREE.MeshStandardMaterial({ color: PAL.pass, metalness: 0.25, roughness: 0.3 });
    const g = new THREE.Group(); scene.add(g);
    const leg = new THREE.Mesh(bar(1.35, 0.46), matPost); leg.rotation.z = (Math.PI * 3) / 4; g.add(leg);
    const pivot = new THREE.Group(); g.add(pivot);
    pivot.add(new THREE.Mesh(bar(3.1, 0.46), matArm));
    g.add(new THREE.Mesh(new THREE.CylinderGeometry(0.34, 0.34, 0.62, 40).rotateX(Math.PI / 2), matPost));
    g.position.set(-0.7, -0.9, 0);
    return {
      // cycleSeconds: a whole number of 30 fps frames / 30, so every pose is a DESIGN §4 sample.
      render(cycleSeconds, rotY) {
        const st = angleAt(cycleSeconds);
        pivot.rotation.z = st.a;
        matArm.color.set(st.f ? PAL.fail : PAL.pass);
        g.rotation.y = -0.35 + (rotY || 0);
        g.rotation.x = 0;
        r.render(scene, cam);
        return st;
      },
    };
  }
  window.CasegateMark = { create, angleAt, UP, DOWN, CYC };
})();
