// 쪽 넘김: 한 장을 책 가운데(또는 한 쪽 화면의 왼쪽 끝)를 축으로 돌린다.
// 실제 종이처럼 휘게 하지 않고, 평평한 장이 넘어가는 모습만 보여 준다.

function div(cls, parent) {
  const d = document.createElement("div");
  d.className = cls;
  parent?.appendChild(d);
  return d;
}

/**
 * host 안 [left, left+width] 위에 놓인 한 장.
 * hinge "left": 왼쪽 끝을 축으로 왼쪽으로 넘어간다(앞으로). hinge "right": 오른쪽 끝을 축으로 오른쪽으로(뒤로).
 * sweep: t=1 일 때 돌아간 각도(펼침 180°, 한 쪽 화면 100°).
 */
export class Flip {
  constructor(host, { left, width, hinge = "left", sweep = 180, front, back }) {
    this.hinge = hinge; this.sweep = sweep;
    this.root = div(`flip hinge-${hinge}`, host);
    this.root.style.left = `${left}px`;
    this.root.style.width = `${width}px`;
    this.frontFace = div("flip-face front", this.root);
    if (front) this.frontFace.appendChild(front);
    this.backFace = div("flip-face back", this.root);
    if (back) this.backFace.appendChild(back);
    this.frontShade = div("flip-shade", this.frontFace);
    this.backShade = div("flip-shade", this.backFace);
    this.cast = div(`flip-cast hinge-${hinge}`, host);
    this.cast.style.left = `${left}px`;
    this.cast.style.width = `${width}px`;
    this.front = front; this.back = back;
  }

  /** t: 0(제자리) → 1(넘어감) */
  set(t) {
    const deg = (this.hinge === "left" ? -1 : 1) * this.sweep * t;
    this.root.style.transform = `rotateY(${deg}deg)`;
    const a = Math.abs(deg);
    // 앞면은 세워질수록 어두워지고, 뒷면은 눕혀질수록 밝아진다
    this.frontShade.style.opacity = Math.min(1, a / 90) * 0.14;
    this.backShade.style.opacity = a <= 90 ? 0.14 : ((180 - a) / 90) * 0.14;
    // 넘어가는 장이 아래 쪽에 드리우는 그늘
    this.cast.style.opacity = Math.sin(Math.min(Math.PI, (a / 180) * Math.PI)) * 0.55;
  }

  destroy() { this.root.remove(); this.cast.remove(); }
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
