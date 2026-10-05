// 책장 넘김: 접힌 선을 기준으로 앞면을 자르고, 뒷면을 그 선에 대해 뒤집어 붙인다(turn.js와 같은 방식).
// 좌표는 책등(spine) 위 끝이 원점, 오른쪽으로 쪽 너비 W, 아래로 높이 H.
// 모서리 C(오른쪽 아래 또는 위)가 P로 옮겨졌을 때, 접힌 선은 C와 P의 수직이등분선이다.

const px = v => `${v.toFixed(2)}px`;

// 사각형 [0,W]×[0,H] 중 a·x + b·y + c ≥ 0 인 부분의 꼭짓점들
function halfRect(W, H, a, b, c) {
  const pts = [[0, 0], [W, 0], [W, H], [0, H]];
  const out = [];
  for (let i = 0; i < 4; i++) {
    const p = pts[i], q = pts[(i + 1) % 4];
    const fp = a * p[0] + b * p[1] + c, fq = a * q[0] + b * q[1] + c;
    if (fp >= 0) out.push(p);
    if ((fp >= 0) !== (fq >= 0)) {
      const t = fp / (fp - fq);
      out.push([p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])]);
    }
  }
  return out;
}
const polygon = pts => pts.length >= 3 ? `polygon(${pts.map(p => `${px(p[0])} ${px(p[1])}`).join(",")})` : "polygon(0 0,0 0,0 0)";

// (ox, oy)를 지나는 선에서 (dx, dy) 방향으로 폭 w만큼 뻗는 띠. 그라디언트는 to right = (dx, dy) 방향
function placeBand(el, ox, oy, dx, dy, w, len) {
  el.style.width = px(Math.max(w, 0.01));
  el.style.height = px(len);
  el.style.transform = `translate(${px(ox)},${px(oy)}) rotate(${Math.atan2(dy, dx)}rad) translateY(${px(-len / 2)})`;
}

function div(cls, parent) {
  const d = document.createElement("div");
  d.className = cls;
  parent?.appendChild(d);
  return d;
}

/** 넘어가는 한 장. front·back은 쪽 요소(W×H). spineX는 host 안에서 책등의 x. */
export class Leaf {
  constructor(host, { W, H, spineX, front, back }) {
    this.W = W; this.H = H;
    this.root = div("leaf", host);
    this.root.style.left = px(spineX);
    this.root.style.width = px(W);
    this.root.style.height = px(H);
    // 아래 쪽에 떨어지는 그림자(오른쪽 쪽 영역 안에서만)
    this.castBox = div("leaf-cast", this.root);
    this.cast = div("band cast", this.castBox);
    this.frontWrap = div("leaf-face front", this.root);
    this.frontWrap.appendChild(front);
    this.frontShade = div("band front-shade", this.frontWrap);
    this.backWrap = div("leaf-face back", this.root);
    this.backWrap.appendChild(back);
    this.backShade = div("band back-shade", this.backWrap);
    this.front = front; this.back = back;
    this.len = 2.2 * Math.hypot(W, H);
  }

  /** 모서리 C가 P로 왔을 때의 모양 */
  set(C, P) {
    const { W, H, len } = this;
    const dx = C[0] - P[0], dy = C[1] - P[1];
    const dist = Math.hypot(dx, dy);
    if (dist < 0.5) { // 접히지 않음
      this.frontWrap.style.clipPath = "none";
      this.backWrap.style.visibility = "hidden";
      this.cast.style.opacity = 0;
      this.frontShade.style.opacity = 0;
      return;
    }
    this.backWrap.style.visibility = "visible";
    const nx = dx / dist, ny = dy / dist;        // 접힌 선의 법선(P → C)
    const mx = (C[0] + P[0]) / 2, my = (C[1] + P[1]) / 2;
    const k = mx * nx + my * ny;                 // 선: n·X = k

    // 앞면: n·X ≤ k 인 부분
    this.frontWrap.style.clipPath = polygon(halfRect(W, H, -nx, -ny, k));

    // 뒷면: 쪽 내용 좌표 c → 종이 좌표 F(c) = (W − cx, cy) → 접힌 선에 대한 반사
    const a = 2 * nx * nx - 1, b = 2 * nx * ny, c = -2 * nx * ny, d = 1 - 2 * ny * ny;
    const e = W * (1 - 2 * nx * nx) + 2 * k * nx, f = -2 * nx * ny * W + 2 * k * ny;
    this.backWrap.style.transform = `matrix(${a},${b},${c},${d},${e},${f})`;
    // 접혀 넘어간 부분(종이 좌표에서 n·X ≥ k)을 쪽 내용 좌표로: −nx·cx + ny·cy + (W·nx − k) ≥ 0
    this.backWrap.style.clipPath = polygon(halfRect(W, H, -nx, ny, W * nx - k));

    const fold = dist / 2;                       // 접힌 선에서 모서리까지
    const lift = Math.min(1, fold / (W * 0.5));  // 0(막 들림) → 1(반쯤 넘어감)
    // 뒷면 음영: 접힌 선 쪽에서 바깥으로
    placeBand(this.backShade, W - mx, my, -nx, ny, Math.min(fold * 1.1, W * 0.75), len);
    // 아래 쪽에 지는 그림자: 접힌 선에서 C 쪽으로
    placeBand(this.cast, mx, my, nx, ny, Math.min(fold * 0.55, W * 0.32) + 6, len);
    this.cast.style.opacity = Math.min(1, 0.35 + lift);
    // 앞면이 들리며 생기는 그늘: 접힌 선에서 책등 쪽으로
    placeBand(this.frontShade, mx, my, -nx, -ny, Math.min(fold * 0.35, 46) + 4, len);
    this.frontShade.style.opacity = Math.min(1, lift * 1.4);
  }

  destroy() { this.root.remove(); }
}

/** 단단한 표지: 책등을 축으로 3D 회전 */
export class HardLeaf {
  constructor(host, { W, H, spineX, front, back }) {
    this.root = div("leaf hard", host);
    this.root.style.left = px(spineX);
    this.root.style.width = px(W);
    this.root.style.height = px(H);
    this.frontFace = div("hard-face front", this.root);
    this.frontFace.appendChild(front);
    this.backFace = div("hard-face back", this.root);
    this.backFace.appendChild(back);
    this.frontDim = div("hard-dim", this.frontFace);
    this.backDim = div("hard-dim", this.backFace);
    this.front = front; this.back = back;
  }
  /** t: 0(닫힘, 오른쪽) → 1(넘어감, 왼쪽) */
  setT(t) {
    const deg = -180 * t;
    this.root.style.transform = `rotateY(${deg}deg)`;
    this.frontDim.style.opacity = Math.min(0.55, t * 0.9);
    this.backDim.style.opacity = Math.min(0.55, (1 - t) * 0.9);
  }
  destroy() { this.root.remove(); }
}

export const ease = {
  inOut: t => t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2,
  out: t => 1 - Math.pow(1 - t, 3),
  turn: t => t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2,
};

// 다음 프레임. 탭이 가려지는 등으로 rAF가 멈춰도 타이머로 이어 간다.
function nextFrame(cb) {
  let done = false;
  const f = () => { if (!done) { done = true; cb(performance.now()); } };
  requestAnimationFrame(f);
  setTimeout(f, 40);
}

/** 트윈. step(e)는 0→1 */
export function tween(ms, easing, step) {
  return new Promise(resolve => {
    if (ms <= 0) { step(1); resolve(); return; }
    const t0 = performance.now();
    const tick = now => {
      const t = Math.min(1, (now - t0) / ms);
      step(easing(t));
      if (t < 1) nextFrame(tick); else resolve();
    };
    nextFrame(tick);
  });
}

/** 책등에 매인 종이가 늘어나지 않도록 모서리 위치를 제한한다 */
export function constrain(P, W, H, bottom) {
  const anchor = bottom ? [0, H] : [0, 0], far = bottom ? [0, 0] : [0, H];
  let [x, y] = P;
  let dx = x - anchor[0], dy = y - anchor[1], r = Math.hypot(dx, dy);
  if (r > W) { x = anchor[0] + dx * W / r; y = anchor[1] + dy * W / r; }
  const D = Math.hypot(W, H);
  dx = x - far[0]; dy = y - far[1]; r = Math.hypot(dx, dy);
  if (r > D) { x = far[0] + dx * D / r; y = far[1] + dy * D / r; }
  return [x, y];
}

/** 클릭으로 넘길 때 모서리가 지나는 길: C(t=0)에서 반대편(t=1)까지 살짝 들리며 원호로 */
export function arcPoint(t, W, H, bottom) {
  const th = Math.PI * t;
  const lift = Math.min(W * 0.12, H * 0.085) * Math.sin(th);
  const x = W * Math.cos(th);
  return [x, bottom ? H - lift : lift];
}
