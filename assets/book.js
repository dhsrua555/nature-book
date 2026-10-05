import { Leaf, HardLeaf, tween, ease, constrain, arcPoint } from "./curl.js";

/* ───────────────────────── 상태 ─────────────────────────
   쪽(page)은 화면 크기에 맞춰 엮는다. 종의 해설은 길이에 따라 여러 쪽으로 흘러가므로
   쪽 번호 대신 도판 번호(Pl.)로 찾아간다. 위치는 늘 쪽 key 로 기억한다. */
const S = {
  vid: "aves", book: null, nodes: new Map(), species: [],
  detail: new Map(), detailP: new Map(), flows: new Map(), dirty: false,
  pages: [], views: [], viewOf: new Map(), pageOf: new Map(),
  mode: null, W: 0, H: 0, view: 0, busy: false, pending: null,
  cap: { list: 7, index: 16 },
  reduced: matchMedia("(prefers-reduced-motion: reduce)"),
  edit: new URLSearchParams(location.search).has("edit"),
};
const $ = id => document.getElementById(id);
const bookEl = $("book"), slotL = $("slot-left"), slotR = $("slot-right");
const ESC = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ESC[c]);
const isTodo = v => v == null || v === "" || (typeof v === "string" && v.includes("TODO"));
const todo = `<span class="todo" title="출처로 확인하지 못해 비워 둔 값">조사 중</span>`;
const val = v => isTodo(v) ? todo : esc(v);
const href = key => `#/${S.vid}/${key}`;
const imgUrl = (id, kind) => `img/${S.vid}/${id}${kind === "plate" ? ".id" : ""}.webp`;
const RANK = { order: ["목", "Ordo"], family: ["과", "Familia"] };
const LABELS = { season: "관찰 시기", seen: "볼 수 있음", breed: "번식기", sexes: "암수 구별", young: "어린새", similar: "비슷한 종", points: "동정 포인트" };
const L = k => S.book?.labels?.[k] || LABELS[k];

/* ───────────────────────── 자료 ───────────────────────── */
async function getJSON(url) {
  const r = await fetch(url, { cache: "no-cache" });
  if (!r.ok) throw new Error(`${url} (${r.status})`);
  return r.json();
}

function indexBook(book) {
  S.book = book; S.nodes.clear(); S.species = [];
  for (const o of book.tree) {
    S.nodes.set(o.id, o);
    for (const f of o.children) {
      f.parent = o; S.nodes.set(f.id, f);
      for (const s of f.children) {
        s.rank = "species"; s.parent = f; s.plateNo = S.species.length + 1;
        S.nodes.set(s.id, s); S.species.push(s);
      }
    }
  }
  const range = n => {
    if (n.rank === "species") return [n.plateNo, n.plateNo];
    const r = n.children.map(range);
    return [Math.min(...r.map(x => x[0])), Math.max(...r.map(x => x[1]))];
  };
  for (const n of S.nodes.values()) n.plates = range(n);
}
const countSp = n => n.rank === "species" ? 1 : n.children.reduce((a, c) => a + countSp(c), 0);
const plateLabel = n => n?.plates ? (n.plates[0] === n.plates[1] ? `${n.plates[0]}` : `${n.plates[0]}–${n.plates[1]}`) : "";

function loadDetail(id) {
  if (!S.detailP.has(id)) {
    S.detailP.set(id, getJSON(`data/${S.vid}/species/${id}.json`).then(d => {
      S.detail.set(id, d);
      S.dirty = true;
      if (!S.busy) applyFlows();
      return d;
    }));
  }
  return S.detailP.get(id);
}
const needs = view => [...new Set((view || []).filter(p => p?.node?.rank === "species").map(p => p.node.id))];
const ready = view => needs(view).every(id => S.detail.has(id) && S.flows.has(id));
async function ensure(view) {
  await Promise.all(needs(view).map(loadDetail));
  applyFlows();
}

/* ───────────────────────── 판형 ───────────────────────── */
function measure() {
  const vw = document.documentElement.clientWidth;
  const vh = window.innerHeight;
  const barH = $("bar").offsetHeight || 56;
  const availH = Math.max(320, vh - barH - (vw < 600 ? 14 : 34));
  let mode = "spread", H = Math.min(availH, 900), W = Math.min(H * 0.7, (vw - 48) / 2);
  if (W < 330 || vw < 760) {
    mode = "single";
    H = Math.min(availH, 900);
    W = Math.min(vw - 16, H * 0.72, 600);
    if (W / H < 0.54) H = Math.round(W / 0.54);
  } else H = Math.min(H, Math.round(W / 0.68));
  return { mode, W: Math.floor(W), H: Math.floor(H) };
}

function applySize() {
  bookEl.style.setProperty("--W", `${S.W}px`);
  bookEl.style.setProperty("--H", `${S.H}px`);
  bookEl.style.setProperty("--fs", `${Math.max(14.5, Math.min(17.5, S.W / 31)).toFixed(2)}px`);
  bookEl.dataset.mode = S.mode;
  document.body.dataset.mode = S.mode;
}

/* 보이지 않는 시험 쪽: 목록 줄 수와 해설이 들어가는지를 실제로 그려 보고 잰다 */
let probe = null;
function probeSlot() {
  if (!probe) { probe = document.createElement("div"); probe.className = "slot probe"; bookEl.appendChild(probe); }
  return probe;
}
function fitsPage(p, side) {
  const pr = probeSlot();
  pr.replaceChildren(makePage(p, side));
  const inn = pr.querySelector(".pg-in");
  return inn.scrollHeight <= inn.clientHeight + 1;
}

function measureCaps() {
  const pr = probeSlot();
  const fake = { ko: "가나다라마바사아", sci: "Abcdefg hijklmn", en: "Abcdefg", rank: "species", img: {}, focus: [0.5, 0.5], children: [], plates: [1, 9] };
  const sides = S.mode === "spread" ? ["left", "right"] : ["single"];
  const cap = (kind, n) => Math.min(...sides.map(side => {
    pr.replaceChildren(makePage({ kind, key: "probe", items: Array.from({ length: n }, () => fake), part: 0, probe: true }, side));
    const list = pr.querySelector(".fill");
    const gap = parseFloat(getComputedStyle(list).rowGap) || 0;
    const h = list.firstElementChild.getBoundingClientRect().height;
    return Math.max(3, Math.floor((list.clientHeight + gap - 3) / (h + gap)));
  }));
  S.cap.list = Math.min(cap("list", 40), cap("contents", 40));
  S.cap.index = cap("index", 80);
  pr.replaceChildren();
}

/* ───────────────────────── 종 해설 흘리기 ─────────────────────────
   도판(왼쪽) → 해설(오른쪽부터 필요한 만큼) → 동정 도해(왼쪽) → 동정 포인트(오른쪽부터).
   동정 도해와 동정 포인트가 늘 마주 보도록, 앞 해설이 왼쪽에서 끝나면 뒤쪽 글(어린새·비슷한 종)을 당겨 채운다. */
function blockList(d) {
  const A = ["facts", "season", "summary", "sexes"];
  const B = ["young", ...(d.similar || []).map((_, i) => `sim${i}`)];
  if (d.taxon_note) B.push("tnote");
  if ((d.sources || []).length) B.push("sources");
  return { A, B };
}

function flowSpecies(node) {
  const d = S.detail.get(node.id);
  const spread = S.mode === "spread";
  const { A, B } = blockList(d);
  const out = [{ kind: "plate" }];
  const sideAt = i => spread ? (i % 2 === 0 ? "left" : "right") : "single";
  const fits = pg => fitsPage({ ...pg, key: "probe", node }, sideAt(out.length));
  let page = { kind: "text", head: true, blocks: [] };
  const place = b => {
    page.blocks.push(b);
    if (fits(page)) return;
    page.blocks.pop();
    if (page.blocks.length || page.head || page.ptsHead) { out.push(page); page = { kind: "text", blocks: [b] }; }
    else page.blocks.push(b); // 한 쪽보다 큰 덩어리: 그대로 둔다(쪽 안에서 스크롤)
  };
  A.forEach(place);
  if (spread && out.length % 2 === 0) { // 해설이 왼쪽에서 끝남 → 오른쪽 한 쪽을 더 채운다
    out.push(page);
    page = { kind: "text", blocks: [] };
    while (B.length) { page.blocks.push(B[0]); if (!fits(page)) { page.blocks.pop(); break; } B.shift(); }
  }
  out.push(page);
  out.push({ kind: "idplate" });
  page = { kind: "text", blocks: [] };
  ["points", ...B].forEach(place);
  out.push(page);
  if (spread && out.length % 2 === 1) out.push({ kind: "blank", spreadOnly: true });
  let t = 0;
  return out.map(p => ({
    ...p,
    key: p.kind === "plate" ? node.id : p.kind === "idplate" ? `${node.id}/id` : p.kind === "blank" ? `${node.id}/blank` : `${node.id}/t${++t}`,
  }));
}

function defaultFlow(node) {
  return [
    { kind: "plate", key: node.id }, { kind: "text", key: `${node.id}/t1`, head: true, blocks: [] },
    { kind: "idplate", key: `${node.id}/id` }, { kind: "text", key: `${node.id}/t2`, blocks: [] },
  ];
}

/** 자료가 들어온 종의 쪽을 새로 엮고, 지금 보던 쪽을 그대로 붙든다 */
function applyFlows() {
  if (!S.mode || !S.book) return;
  let changed = false;
  for (const id of S.detail.keys()) {
    if (S.flows.has(id)) continue;
    S.flows.set(id, flowSpecies(S.nodes.get(id)));
    changed = true;
  }
  S.dirty = false;
  probe?.replaceChildren();
  if (!changed) return;
  const keep = S.views.length ? keyOfView(S.view) : null;
  paginate();
  if (keep != null) S.view = viewOfKey(keep) ?? S.view;
}

/* ───────────────────────── 책 엮기 ───────────────────────── */
const chunk = (arr, n) => { const out = []; for (let i = 0; i < arr.length; i += n) out.push(arr.slice(i, i + n)); return out.length ? out : [[]]; };

function paginate() {
  const P = [];
  const add = p => { P.push(p); return p; };
  const padToLeft = key => { if (P.length % 2 === 0) add({ kind: "blank", key: `${key}/blank`, spreadOnly: true }); };
  const lists = (kind, key, node, items) => chunk(items, S.cap.list).forEach((it, i) =>
    add({ kind, key: i ? `${key}/${i + 1}` : key, node, items: it, part: i }));

  add({ kind: "cover", key: "" });
  add({ kind: "endpaper", key: "endpaper", spreadOnly: true });
  add({ kind: "title", key: "title" });
  add({ kind: "guide", key: "guide" });
  lists("contents", "contents", null, [...S.book.tree, { plain: "찾아보기", key: "index" }, { plain: "출처와 판권", key: "colophon" }]);
  padToLeft("contents");
  for (const o of S.book.tree) {
    add({ kind: "group", key: o.id, node: o });
    lists("list", `${o.id}/list`, o, o.children);
    padToLeft(o.id);
    for (const f of o.children) {
      add({ kind: "group", key: f.id, node: f });
      lists("list", `${f.id}/list`, f, f.children);
      padToLeft(f.id);
      for (const s of f.children) for (const p of (S.flows.get(s.id) || defaultFlow(s))) add({ ...p, node: s });
    }
  }
  const sorted = [...S.species].sort((a, b) => a.ko.localeCompare(b.ko, "ko"));
  chunk(sorted, S.cap.index).forEach((it, i) => add({ kind: "index", key: i ? `index/${i + 1}` : "index", items: it, part: i }));
  if (P.length % 2 === 1) add({ kind: "blank", key: "colophon/blank", spreadOnly: true });
  add({ kind: "colophon", key: "colophon" });

  P.forEach((p, i) => { p.i = i; });
  S.pages = P;
  S.pageOf = new Map(P.map(p => [p.key, p]));
  const V = [];
  if (S.mode === "spread") {
    V.push([null, P[0]]);
    for (let i = 1; i < P.length; i += 2) V.push([P[i], P[i + 1] || null]);
  } else {
    for (const p of P) if (!p.spreadOnly) V.push([p]);
  }
  S.views = V;
  S.viewOf = new Map();
  V.forEach((v, n) => v.forEach(p => p && S.viewOf.set(p.key, n)));
}

function viewOfKey(key) {
  if (S.viewOf.has(key)) return S.viewOf.get(key);
  const p = S.pageOf.get(key);
  if (p) for (let i = p.i; i < S.pages.length; i++) if (S.viewOf.has(S.pages[i].key)) return S.viewOf.get(S.pages[i].key);
  if (key.includes("/")) return viewOfKey(key.split("/")[0]); // 다른 판형에서 엮인 쪽 → 그 종의 처음
  return null;
}
function keyOfView(n) {
  const v = S.views[n];
  if (!v) return "";
  const p = v.find(p => p && !p.spreadOnly) || v.find(Boolean);
  return p.key;
}

/* ───────────────────────── 그림 조각 ───────────────────────── */
const SKETCH = `<svg class="sketch" viewBox="0 0 120 90" aria-hidden="true" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
<path d="M99 33.5c-3-.6-5.6-1-7.4-1.4-1.5-4.6-5.4-7.6-10.4-7.6-6.6 0-10.8 4.6-14.4 9.4C61.6 41 54 46.4 42 52.4 32.6 57 21.4 61.4 9.6 66.6c9.8.4 19.8-1 28.6-3.2 6.4 3.6 14.6 4.8 22.8 3.2C75 64 85 55.4 88.6 43.6c4.2-3.2 7.6-6.6 10.4-10.1z" stroke-width="1.3"/>
<path d="M52.6 47.6c7.2 1.4 15.8.2 22.4-4.6M47 53.2c8.8 2.2 19.6 1 27.6-4.8" stroke-width=".9" opacity=".7"/>
<circle cx="84.6" cy="33" r="1.3" fill="currentColor" stroke="none"/>
<path d="M60.4 66.6l-1.6 8.6m8.4-9.4l.4 9M28 76.6c18-1.4 44-2.6 76-1.2" stroke-width="1.1"/></svg>`;

const ORN = `<svg class="orn" viewBox="0 0 120 14" aria-hidden="true"><path d="M2 7h44M74 7h44" stroke="currentColor" stroke-width=".8"/><path d="M60 1.5c3 2.6 3 8.4 0 11-3-2.6-3-8.4 0-11zM52 7c2.6-2.4 5-2.4 6.4 0-1.4 2.4-3.8 2.4-6.4 0zm16 0c-2.6-2.4-5-2.4-6.4 0 1.4 2.4 3.8 2.4 6.4 0z" fill="currentColor"/></svg>`;

function vignette(node, cls = "vig") {
  const sp = node && (node.rank === "species" ? node : S.nodes.get(node.rep));
  if (sp?.img?.scene) {
    const [fx, fy] = sp.focus || [0.5, 0.5];
    return `<span class="${cls}"><img src="${imgUrl(sp.id, "scene")}" alt="" decoding="async" style="object-position:${fx * 100}% ${fy * 100}%"></span>`;
  }
  return `<span class="${cls} ph">${SKETCH}</span>`;
}

function crumbs(node) {
  const chain = [];
  for (let n = node; n; n = n.parent) if (n.rank !== "species") chain.unshift(n);
  return [`<a href="${href("contents")}">차례</a>`, ...chain.map(n => `<a href="${href(n.id)}">${esc(n.ko)}</a>`)].join(`<span class="sep">›</span>`);
}

function runningHead(p, side) {
  const n = p.node;
  const right = n?.rank === "species" ? `${esc(n.ko)} <i>${esc(n.sci)}</i>` : n ? esc(n.ko) : side === "single" ? "" : esc(S.book.title);
  if (side === "right") return `<header class="rh"><span></span><span class="rh-r">${right}</span></header>`;
  return `<header class="rh"><span class="rh-l">${n ? crumbs(n) : esc(S.book.title)}</span><span class="rh-r">${n?.rank === "species" || side === "single" ? right : ""}</span></header>`;
}

/* 관찰 시기 달력 */
function monthRanges(ms) {
  const set = new Set(ms);
  if (set.size === 12) return "연중";
  const out = [];
  for (let m = 1; m <= 12; m++) {
    if (!set.has(m) || set.has(((m + 10) % 12) + 1)) continue;
    let e = m; while (set.has((e % 12) + 1) && ((e % 12) + 1) !== m) e = (e % 12) + 1;
    out.push(e === m ? `${m}월` : `${m}–${e}월`);
  }
  return out.join(", ");
}
function calendar(months) {
  const seen = Array.isArray(months?.seen) ? new Set(months.seen) : null;
  const breed = Array.isArray(months?.breed) ? new Set(months.breed) : null;
  if (!seen) return `<p class="cal-todo">${L("seen")} ${todo}</p>`;
  const label = `${L("seen")}: ${monthRanges([...seen])}${breed ? `, ${L("breed")}: ${monthRanges([...breed])}` : ""}`;
  const cells = Array.from({ length: 12 }, (_, i) => {
    const m = i + 1;
    return `<span class="mo${seen.has(m) ? " on" : ""}${breed?.has(m) ? " br" : ""}"><i></i><b>${m}</b></span>`;
  }).join("");
  return `<div class="cal" role="img" aria-label="${esc(label)}">${cells}</div>
    <p class="cal-key"><span class="k on"></span>${L("seen")} ${breed ? `<span class="k br"></span>${L("breed")}` : `<span class="dim">${L("breed")} ${todo}</span>`}</p>`;
}

function facts(d) {
  return S.book.fields.map(f => {
    let v = d[f.key];
    if (Array.isArray(v)) {
      if (!v.length) return "";
      v = v.map(x => `<span class="stamp">${esc(x)}</span>`).join(" ");
    } else {
      if (f.optional && isTodo(v)) return "";
      v = val(v);
    }
    return `<dt>${esc(f.label)}</dt><dd>${v}</dd>`;
  }).join("");
}

/* 동정 도해 위 번호·지시선 */
function callouts(points) {
  const placed = points.map((p, i) => ({ ...p, n: i + 1 })).filter(p => Array.isArray(p.at));
  if (!placed.length) return "";
  const withLabel = placed.filter(p => Array.isArray(p.label));
  const lines = withLabel.map(p => `<line x1="${p.at[0] * 100}" y1="${p.at[1] * 100}" x2="${p.label[0] * 100}" y2="${p.label[1] * 100}"/>`).join("");
  const labels = withLabel.map(p =>
    `<span class="co-label ${p.label[0] < p.at[0] ? "to-left" : "to-right"}" style="left:${p.label[0] * 100}%;top:${p.label[1] * 100}%">${esc(p.ko)}</span>`).join("");
  const dots = placed.map(p => `<span class="co-dot" style="left:${p.at[0] * 100}%;top:${p.at[1] * 100}%">${p.n}</span>`).join("");
  return `<svg class="co-lines" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">${lines}</svg>${labels}${dots}`;
}

const firstSentence = t => isTodo(t) ? "" : (String(t).match(/^.*?[다요]\./) || [t])[0];
function entry(n, extra = "", roomy = false) {
  let desc = "";
  if (roomy) {
    desc = n.rank === "species"
      ? [isTodo(n.en) ? "" : n.en, isTodo(n.status) ? "" : n.status, isTodo(n.length) ? "" : `몸길이 ${n.length}`].filter(Boolean).join(" · ")
      : firstSentence(n.desc);
  }
  return `<li><a class="entry${roomy ? " roomy" : ""}" href="${href(n.id)}">${vignette(n)}<span class="en-names"><span class="l1"><span class="ko">${esc(n.ko)}</span>${extra}</span><span class="sci"><i>${esc(n.sci)}</i></span>${desc ? `<span class="desc">${esc(desc)}</span>` : ""}</span><span class="lead"></span><span class="pg"><span class="pl">Pl.</span>${plateLabel(n)}</span></a></li>`;
}

/* 해설 덩어리 */
const BLOCK = {
  facts: d => `<dl class="facts">${facts(d)}</dl>`,
  season: d => `<section class="season"><h3>${L("season")}</h3>${calendar(d.months)}${d.months?.note && !isTodo(d.months.note) ? `<p class="note">${esc(d.months.note)}</p>` : ""}</section>`,
  summary: d => `<p class="summary">${val(d.summary)}</p>`,
  sexes: d => {
    const sx = d.sexes || {};
    return `<section><h3>${L("sexes")}</h3>${sx.alike ? `<p>${val(sx.text)}</p>`
      : `<dl class="sexes"><dt>수컷</dt><dd>${val(sx.male)}</dd><dt>암컷</dt><dd>${val(sx.female)}</dd></dl>`}</section>`;
  },
  points: d => `<section class="pts-sec"><h2 class="pg-title small">${L("points")}</h2><ol class="pts">${(d.points || []).map((x, i) => `<li><span class="num">${i + 1}</span>${val(x.ko)}</li>`).join("")}</ol></section>`,
  young: d => `<section><h3>${L("young")}</h3><p>${val(d.young)}</p></section>`,
  tnote: d => `<p class="tnote">${esc(d.taxon_note)}</p>`,
  sources: d => `<footer class="src"><h4>출처</h4><ol>${(d.sources || []).map(s => `<li>${s.url ? `<a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.title)}</a>` : esc(s.title)}</li>`).join("")}</ol></footer>`,
};
function block(b, d, node) {
  if (b.startsWith("sim")) {
    const i = +b.slice(3), x = d.similar[i];
    const id = S.book.similar?.[node.id]?.[i];
    const name = id ? `<a href="${href(id)}">${esc(x.ko)}</a>` : esc(x.ko);
    return `<section class="sim">${i === 0 ? `<h3>${L("similar")}</h3>` : ""}<p><b>${name}</b> ${val(x.how)}</p></section>`;
  }
  return BLOCK[b](d);
}

/* ───────────────────────── 쪽 그리기 ───────────────────────── */
const R = {
  cover() {
    const b = S.book;
    return `<div class="cover-in"><div class="cover-frame">
        <p class="cv-kicker">${esc(b.kicker)}</p>
        <h1 class="cv-title">${esc(b.title)}</h1>
        <p class="cv-en">${esc(b.en)}</p>
        <svg class="cv-bird" viewBox="0 0 120 90" aria-hidden="true">${SKETCH.replace(/^<svg[^>]*>|<\/svg>$/g, "")}</svg>
        <p class="cv-ed">${esc(b.edition)}</p>
      </div></div>`;
  },
  endpaper() {
    return `<div class="endpaper-in"><div class="bookplate"><p class="bp-ex">Ex Libris</p>${ORN}<p class="bp-line"></p><p class="bp-cap">이 책의 주인</p></div></div>`;
  },
  title() {
    const b = S.book, c = b.counts;
    return `<div class="pg-in title-page">
      <p class="tp-kicker">${esc(b.kicker)}</p>
      <h1 class="tp-title">${esc(b.title)}</h1>
      <p class="tp-en"><i>${esc(b.en)}</i></p>
      ${ORN}
      ${vignette(S.nodes.get(b.rep), "cartouche big")}
      <p class="tp-basis">${esc(b.basis.name)}(${esc(b.basis.edition)})에 따라<br>${c.orders}목 ${c.families}과 ${c.species}종을 싣다</p>
      <p class="tp-ed">${esc(b.edition)}</p>
    </div>`;
  },
  guide(p) {
    const b = S.book;
    return `<div class="pg-in guide">${runningHead(p, "left")}
      <h2 class="pg-title">일러두기</h2>
      <ol class="notes">
        <li><b>분류와 이름</b> 국명과 학명, 목·과와 그 차례는 ${esc(b.basis.name)}(${esc(b.basis.edition)})을 따랐다. 이 목록에 실린 조류는 ${b.counts.nibr}종이다.</li>
        <li><b>도판과 해설</b> 종마다 사는 곳을 배경으로 한 수채 도판과 해설을 싣고, 이어서 동정 도해와 동정 포인트를 마주 보게 놓았다. 차례와 찾아보기의 숫자는 도판 번호(Pl.)다.</li>
        <li><b>관찰 시기</b> 국내에서 볼 수 있는 달을 칠하고, 번식하는 달에 점을 찍었다.${calendar({ seen: [4, 5, 6, 7, 8, 9, 10], breed: [5, 6, 7] })}</li>
        <li><b>보호</b> 붉은 도장은 천연기념물과 멸종위기 야생생물 등급이다(국가생물종목록 표시).</li>
        <li><b>${todo}</b> 출처로 확인하지 못한 값은 지어내지 않고 비워 두었다.</li>
        <li><b>삽화</b> 생성형 이미지 모델로 그린 뒤 사람이 살펴 고른 그림이다. 깃 색과 무늬는 해설을 기준으로 삼는다.</li>
      </ol>
      <p class="howto">쪽 모서리를 끌거나 화살표 키(← →), 아래 단추로 넘긴다.</p>
    </div>`;
  },
  contents(p, side) {
    const rows = p.items.map(it => it.plain
      ? `<li><a class="entry plain" href="${href(it.key)}"><span class="vig none"></span><span class="en-names"><span class="l1"><span class="ko">${esc(it.plain)}</span></span></span><span class="lead"></span><span class="pg"></span></a></li>`
      : entry(it, `<span class="meta">${it.children.length}과 ${countSp(it)}종</span>`)).join("");
    return `<div class="pg-in list-page">${runningHead(p, side)}
      <h2 class="pg-title">차례${p.part ? `<span class="cont">이어서</span>` : ""}</h2>
      <ul class="entries fill">${rows}</ul></div>`;
  },
  group(p, side) {
    const n = p.node, [rk, la] = RANK[n.rank];
    const inBook = n.rank === "order" ? `${n.children.length}과 ${countSp(n)}종` : `${countSp(n)}종`;
    return `<div class="pg-in group-page">${runningHead(p, side)}
      <p class="rank">${rk} <span class="la">${la}</span></p>
      <h2 class="grp-ko">${esc(n.ko)}</h2>
      <p class="grp-sci"><i>${esc(n.sci)}</i></p>
      ${vignette(n, "cartouche")}
      <p class="grp-desc">${val(n.desc)}</p>
      ${ORN}
      <p class="grp-count">이 책에 ${inBook} · 국가생물종목록 ${n.nibr}종</p>
    </div>`;
  },
  list(p, side) {
    const n = p.node || { ko: "가나다라목", rank: "order" };
    const sub = n.rank === "order" ? "과" : "종";
    const roomy = !p.probe && p.items.length <= Math.floor(S.cap.list / 2);
    const rows = p.items.map(c => c.rank === "species"
      ? entry(c, roomy || isTodo(c.en) ? "" : `<span class="meta">${esc(c.en)}</span>`, roomy)
      : entry(c, `<span class="meta">${countSp(c)}종</span>`, roomy)).join("");
    return `<div class="pg-in list-page">${runningHead(p, side)}
      <h2 class="pg-title">${esc(n.ko)}의 ${sub}${p.part ? `<span class="cont">이어서</span>` : ""}</h2>
      <ul class="entries fill">${rows}</ul></div>`;
  },
  plate(p, side) {
    const n = p.node;
    const img = n.img?.scene
      ? `<img src="${imgUrl(n.id, "scene")}" alt="${esc(n.ko)}가 사는 곳을 배경으로 그린 수채 도판" decoding="async">`
      : `<div class="ph-plate">${SKETCH}<span>도판 준비 중</span></div>`;
    return `<div class="pg-in plate-page">${runningHead(p, side)}
      <figure class="plate">
        <p class="pl-no">Pl. ${n.plateNo}</p>
        <div class="pl-frame${S.edit ? " editable" : ""}" data-edit="focus" data-id="${n.id}">${img}</div>
        <figcaption>
          <span class="ko">${esc(n.ko)}</span>
          <span class="sci"><i>${esc(n.sci)}</i></span>
          <span class="en">${val(n.en)}</span>
        </figcaption>
      </figure></div>`;
  },
  text(p, side) {
    const n = p.node, d = S.detail.get(n.id);
    if (!d) return `<div class="pg-in"><p class="loading">…</p></div>`;
    const head = p.head ? `<header class="sp-head">
        <h2>${esc(d.ko)}</h2>
        <p class="sci"><i>${esc(d.sci)}</i> <span class="auth">${esc(d.author || "")}</span></p>
        <p class="en">${val(d.en)}</p>
        <p class="taxon"><a href="${href(n.parent.parent.id)}">${esc(n.parent.parent.ko)}</a> › <a href="${href(n.parent.id)}">${esc(n.parent.ko)}</a></p>
      </header>` : "";
    return `<div class="pg-in text-page">${runningHead(p, side)}${head}${(p.blocks || []).map(b => block(b, d, n)).join("")}</div>`;
  },
  idplate(p, side) {
    const n = p.node, d = S.detail.get(n.id);
    const body = n.img?.plate
      ? `<div class="idframe${S.edit ? " editable" : ""}" data-edit="points" data-id="${n.id}"><img src="${imgUrl(n.id, "plate")}" alt="${esc(n.ko)} 동정 도해" decoding="async">${callouts(d?.points || [])}</div>`
      : `<div class="ph-plate tall">${SKETCH}<span>동정 도해 준비 중</span></div>`;
    return `<div class="pg-in idplate-page">${runningHead(p, side)}
      <figure class="idfig">${body}
        <figcaption><span class="ko">${esc(n.ko)}</span> 동정 도해${d?.art?.views?.length ? ` · ${d.art.views.length}가지 모습` : ""}</figcaption>
      </figure></div>`;
  },
  index(p, side) {
    const rows = p.items.map(s => `<li><a href="${href(s.id)}"><span class="ko">${esc(s.ko)}</span><span class="lead"></span><span class="pg"><span class="pl">Pl.</span>${s.plates ? s.plates[0] : ""}</span></a></li>`).join("");
    return `<div class="pg-in index-page">${runningHead(p, side)}
      <h2 class="pg-title">찾아보기${p.part ? `<span class="cont">이어서</span>` : ""}</h2>
      <ul class="idx fill">${rows}</ul></div>`;
  },
  colophon(p, side) {
    const b = S.book;
    return `<div class="pg-in colophon">${runningHead(p, side)}
      <h2 class="pg-title">출처와 판권</h2>
      <p>분류와 국명, 학명은 <a href="${esc(b.basis.url)}" target="_blank" rel="noopener">${esc(b.basis.name)}</a>(${esc(b.basis.edition)})을 따랐다. 종마다 참고한 문헌과 누리집은 그 종의 해설 끝에 적었다.</p>
      <p>도판과 동정 도해는 생성형 이미지 모델로 그린 뒤 사람이 검수했다. 동정 도해의 글자는 그림에 넣지 않고 해설 자료에서 얹었다.</p>
      ${ORN}
      <p class="colo">${esc(b.title)} · ${esc(b.kicker)}<br>${esc(b.edition)}년 엮음 · 자료 갱신 ${esc(b.built)}</p>
    </div>`;
  },
  blank() { return `<div class="pg-in blank-page">${ORN}</div>`; },
};

function foxing(seed) {
  let s = seed % 2147483647; if (s <= 0) s += 2147483646;
  const rnd = () => (s = (s * 16807) % 2147483647) / 2147483647;
  const v = [];
  for (let i = 1; i <= 3; i++) v.push(`--f${i}x:${(8 + rnd() * 84).toFixed(1)}%;--f${i}y:${(6 + rnd() * 88).toFixed(1)}%;--f${i}s:${(0.6 + rnd() * 1.6).toFixed(2)}%`);
  return v.join(";");
}
const hashKey = k => [...String(k)].reduce((a, c) => (a * 31 + c.charCodeAt(0)) | 0, 7);

function makePage(p, side) {
  const el = document.createElement("article");
  if (p.kind === "cover") el.className = `page cover ${side}`;
  else {
    el.className = `page paper ${side} k-${p.kind}`;
    el.style.cssText = foxing(Math.abs(hashKey(p.key)) + 101);
  }
  el.dataset.key = p.key;
  const mark = p.node?.rank === "species" && p.kind !== "blank" ? `<footer class="folio">Pl. ${p.node.plateNo}</footer>` : "";
  el.innerHTML = R[p.kind](p, side) + mark;
  if (p.kind === "plate" || p.kind === "idplate") el.setAttribute("aria-label", `${p.node.ko} ${p.kind === "plate" ? "도판" : "동정 도해"}`);
  return el;
}

/** 넘어가는 종이의 뒷면(한 쪽씩 볼 때): 앞쪽 글씨가 희미하게 비친다 */
function makeVerso(front) {
  const el = document.createElement("article");
  el.className = "page paper verso";
  el.style.cssText = front?.style.cssText || "";
  if (front) {
    const ghost = front.cloneNode(true);
    ghost.className += " ghost";
    ghost.removeAttribute("style");
    ghost.setAttribute("aria-hidden", "true");
    el.appendChild(ghost);
  }
  return el;
}

/* ───────────────────────── 펼치기 ───────────────────────── */
function put(slot, el) { slot.replaceChildren(...(el ? [el] : [])); }
function take(slot) { const el = slot.firstElementChild; if (el) el.remove(); return el; }

function showView(n) {
  S.view = Math.max(0, Math.min(n, S.views.length - 1));
  const v = S.views[S.view];
  if (S.mode === "spread") {
    put(slotL, v[0] ? makePage(v[0], "left") : null);
    put(slotR, v[1] ? makePage(v[1], "right") : null);
  } else {
    put(slotL, null);
    put(slotR, makePage(v[0], "single"));
  }
  chrome();
}

function chrome() {
  const n = S.view, v = S.views[n];
  bookEl.classList.toggle("closed", S.mode === "spread" && n === 0);
  $("prev").disabled = n === 0;
  $("next").disabled = n === S.views.length - 1;
  const main = v.find(p => p?.node && p.kind !== "blank") || v.find(Boolean);
  const node = main?.node;
  const name = node ? node.ko : { contents: "차례", index: "찾아보기", guide: "일러두기", colophon: "출처와 판권", title: S.book.title }[main?.kind] || "";
  $("where").textContent = node?.rank === "species" ? `Pl. ${node.plateNo} / ${S.species.length}` : name;
  document.title = name && main?.kind !== "title" ? `${name} — ${S.book.title}` : `${S.book.title} — ${S.book.kicker}`;
  $("live").textContent = name || "표지";
  const prog = S.views.length > 1 ? n / (S.views.length - 1) : 0;
  bookEl.style.setProperty("--stackL", `${Math.round(prog * 7)}px`);
  bookEl.style.setProperty("--stackR", `${Math.round((1 - prog) * 7)}px`);
  if (S.edit) editPanel();
}

function setHash(push) {
  const url = `#/${S.vid}/${keyOfView(S.view)}`;
  if (location.hash === url) return;
  history[push ? "pushState" : "replaceState"](null, "", url);
}
function routeKey() {
  const m = location.hash.match(/^#\/?([^/]*)\/?(.*)$/);
  return m && m[1] === S.vid ? decodeURIComponent(m[2]) : "";
}

function prefetch(n) {
  for (const k of [n + 1, n - 1, n + 2, n - 2]) {
    const v = S.views[k];
    if (!v) continue;
    needs(v).forEach(id => loadDetail(id).catch(() => {}));
    for (const p of v) {
      if (p?.kind === "plate" && p.node.img?.scene) new Image().src = imgUrl(p.node.id, "scene");
      if (p?.kind === "idplate" && p.node.img?.plate) new Image().src = imgUrl(p.node.id, "plate");
    }
  }
}

function imagesReady(els, ms = 400) {
  const imgs = els.filter(Boolean).flatMap(el => [...el.querySelectorAll("img")]);
  const all = Promise.all(imgs.map(i => i.decode ? i.decode().catch(() => {}) : Promise.resolve()));
  return Promise.race([all, new Promise(r => setTimeout(r, ms))]);
}

/* ───────────────────────── 넘기기 ───────────────────────── */
const DUR = 860;

/** from → to 로 넘길 장을 준비한다(아직 움직이지 않음) */
function setupTurn(from, to, bottom = true) {
  const fwd = to > from, spread = S.mode === "spread";
  const cv = S.views[from], tv = S.views[to];
  let front, back, commit, restore;
  if (spread) {
    if (fwd) {
      front = take(slotR);
      back = tv[0] ? makePage(tv[0], "left") : makeVerso();
      put(slotR, tv[1] ? makePage(tv[1], "right") : null);
      commit = () => put(slotL, back);
      restore = () => put(slotR, front);
    } else {
      back = take(slotL);
      front = tv[1] ? makePage(tv[1], "right") : makeVerso();
      put(slotL, tv[0] ? makePage(tv[0], "left") : null);
      commit = () => put(slotR, front);
      restore = () => put(slotL, back);
    }
  } else if (fwd) {
    front = take(slotR);
    back = makeVerso(front);
    put(slotR, makePage(tv[0], "single"));
    commit = () => {};
    restore = () => put(slotR, front);
  } else {
    front = makePage(tv[0], "single");
    back = makeVerso(front);
    commit = () => put(slotR, front);
    restore = () => {};
  }
  const hard = fwd ? (spread ? from === 0 : cv[0].kind === "cover") : (spread ? to === 0 : tv[0].kind === "cover");
  if (hard && !spread) back = Object.assign(document.createElement("article"), { className: "page board" });
  const leaf = new (hard ? HardLeaf : Leaf)(bookEl, { W: S.W, H: S.H, spineX: spread ? S.W : 0, front, back });
  const C = [S.W, bottom ? S.H : 0];
  const far = [-S.W, C[1]];
  if (hard) leaf.setT(fwd ? 0 : 1); else leaf.set(C, fwd ? C : far);
  return { from, to, fwd, hard, leaf, C, far, bottom, commit, restore };
}

function finishTurn(t) {
  t.commit();
  t.leaf.destroy();
  S.view = t.to;
  chrome();
  prefetch(t.to);
  keepFocus();
}

/** 누른 링크가 쪽과 함께 사라졌으면 새 쪽으로 초점을 옮긴다 */
function keepFocus() {
  const a = document.activeElement;
  if (a && a !== document.body && document.contains(a)) return;
  const pg = (S.mode === "spread" ? slotL.querySelector(".pg-in") || slotR.querySelector(".pg-in") : slotR.querySelector(".pg-in"));
  if (pg) { pg.tabIndex = -1; pg.focus({ preventScroll: true }); }
}

/** spec: { key } 또는 { delta } — 쪽을 다시 엮어도 같은 곳을 가리키도록 위치를 key로 받는다 */
async function turnTo(spec, { push = false, fast = false } = {}) {
  if (S.busy) { S.pending = { spec, push }; return; }
  S.busy = true;
  try {
    const resolve = () => spec.key != null ? viewOfKey(spec.key) : S.view + spec.delta;
    let to = resolve();
    if (to == null || to < 0 || to >= S.views.length) return;
    await ensure(S.views[to]);
    await ensure(S.views[S.view]);
    to = resolve();
    if (to == null || to < 0 || to >= S.views.length || to === S.view) { setHash(false); return; }
    if (S.reduced.matches) {
      showView(to);
      bookEl.animate?.([{ opacity: 0.6 }, { opacity: 1 }], { duration: 160 });
      prefetch(to);
      keepFocus();
    } else {
      const t = setupTurn(S.view, to, true);
      await imagesReady([t.leaf.front, t.leaf.back, slotL, slotR]);
      if (S.mode === "spread" && (S.view === 0 || to === 0)) bookEl.classList.toggle("closed", to === 0);
      const ms = fast ? DUR * 0.6 : DUR;
      if (t.hard) await tween(ms * 1.1, ease.inOut, e => t.leaf.setT(t.fwd ? e : 1 - e));
      else await tween(ms, ease.turn, e => t.leaf.set(t.C, arcPoint(t.fwd ? e : 1 - e, S.W, S.H, true)));
      finishTurn(t);
    }
    setHash(push);
  } catch (err) {
    console.error(err);
  } finally {
    idle();
  }
}

function idle() {
  S.busy = false;
  if (S.dirty) applyFlows();
  if (S.pending) { const { spec, push } = S.pending; S.pending = null; turnTo(spec, { push, fast: true }); }
}

const go = d => turnTo({ delta: d });

/* ───────────── 손으로 끌어 넘기기 · 모서리 들추기 ───────────── */
const drag = { st: null, peek: null };
function localPoint(e) {
  const r = bookEl.getBoundingClientRect();
  return [e.clientX - r.left - (S.mode === "spread" ? S.W : 0), e.clientY - r.top];
}
function inCorner([x, y]) {
  const z = Math.min(70, S.W * 0.16);
  if (!(y > S.H - z || y < z)) return 0;
  if (x > S.W - z && x <= S.W + 4) return 1;
  if (S.mode === "spread" && x < -S.W + z && x >= -S.W - 4) return -1;
  return 0;
}

function startSession(dir, pt, grabbed) {
  const to = S.view + dir;
  if (to < 0 || to >= S.views.length || !ready(S.views[to])) return null;
  const t = setupTurn(S.view, to, pt[1] > S.H / 2);
  if (t.hard) { t.restore(); t.leaf.destroy(); return null; }
  S.busy = true;
  return { t, dir, start: dir > 0 ? t.C : t.far, grabbed };
}

function movePoint(st, P) {
  st.P = constrain(P, S.W, S.H, st.t.bottom);
  st.t.leaf.set(st.t.C, st.P);
}

async function release(st, complete) {
  const { t } = st;
  const from = st.P || st.start;
  const end = complete ? (st.dir > 0 ? t.far : t.C) : st.start;
  const dist = Math.hypot(end[0] - from[0], end[1] - from[1]);
  const ms = S.reduced.matches ? 0 : Math.max(140, Math.min(520, dist / S.W * 420));
  await tween(ms, ease.out, e => {
    t.leaf.set(t.C, constrain([from[0] + (end[0] - from[0]) * e, from[1] + (end[1] - from[1]) * e], S.W, S.H, t.bottom));
  });
  if (complete) { finishTurn(t); setHash(false); }
  else { t.restore(); t.leaf.destroy(); }
  idle();
}

function peek(dir, pt) {
  if (drag.peek || S.busy || S.reduced.matches) return;
  const s = startSession(dir, pt, true);
  if (!s) return;
  drag.peek = s;
  const from = s.start;
  const to = [from[0] - dir * S.W * 0.13, s.t.bottom ? S.H - S.W * 0.1 : S.W * 0.1];
  s.anim = tween(240, ease.out, e => !s.dead && movePoint(s, [from[0] + (to[0] - from[0]) * e, from[1] + (to[1] - from[1]) * e]));
}
async function unpeek() {
  const s = drag.peek;
  if (!s || s.dragging) return;
  drag.peek = null;
  await s.anim;
  if (s.dead) return;
  s.dead = true;
  await release(s, false);
}

function onPointerDown(e) {
  if (e.button !== 0 || (S.edit && e.target.closest(".editable"))) return;
  if (S.busy && !drag.peek) return;
  drag.st = { id: e.pointerId, x0: e.clientX, y0: e.clientY, pt: localPoint(e), moved: false, vx: 0, lastX: e.clientX, lastT: performance.now() };
}
function onPointerMove(e) {
  const d = drag.st;
  if (!d) {
    if (e.pointerType !== "mouse" || (S.busy && !drag.peek)) return;
    const pt = localPoint(e), c = inCorner(pt);
    if (c && !drag.peek) peek(c, pt);
    else if (!c && drag.peek) unpeek();
    return;
  }
  if (e.pointerId !== d.id) return;
  const dx = e.clientX - d.x0, dy = e.clientY - d.y0;
  const now = performance.now();
  d.vx = (e.clientX - d.lastX) / Math.max(1, now - d.lastT); d.lastX = e.clientX; d.lastT = now;
  if (!d.session) {
    if (Math.abs(dx) < 8 || Math.abs(dx) < Math.abs(dy) * 1.1) return;
    const dir = dx < 0 ? 1 : -1;
    if (drag.peek && drag.peek.dir === dir) { d.session = drag.peek; drag.peek = null; }
    else {
      if (drag.peek) return;
      if (S.mode === "spread" && (dir > 0 ? d.pt[0] < 0 : d.pt[0] > 0)) { drag.st = null; return; }
      const s = startSession(dir, d.pt, !!inCorner(d.pt));
      if (!s) { drag.st = null; if (S.views[S.view + dir]) go(dir); return; }
      d.session = s;
    }
    d.session.dragging = true;
    d.moved = true;
    try { bookEl.setPointerCapture(e.pointerId); } catch {}
  }
  const s = d.session;
  movePoint(s, s.grabbed ? localPoint(e) : [s.start[0] + dx, s.start[1] + dy]);
  e.preventDefault();
}
async function onPointerUp(e) {
  const d = drag.st;
  if (!d || e.pointerId !== d.id) return;
  drag.st = null;
  const s = d.session;
  if (s) {
    s.dead = true;
    const P = s.P || s.start;
    const complete = s.dir > 0 ? (P[0] < S.W * 0.3 || d.vx < -0.45) : (P[0] > -S.W * 0.3 || d.vx > 0.45);
    bookEl.dataset.dragged = "1";
    setTimeout(() => delete bookEl.dataset.dragged, 0);
    await release(s, complete);
    return;
  }
  if (drag.peek && !d.moved && inCorner(d.pt) === drag.peek.dir) { // 들춘 모서리를 누르면 넘긴다
    const p = drag.peek; drag.peek = null; p.dead = true;
    await p.anim;
    await release(p, true);
  }
}

/* ───────────────────────── 검수 모드 ─────────────────────────
   ?edit 로 열면 동정 도해를 눌러 번호 위치(at)·글자 위치(label)를, 도판을 눌러 둥근 그림의 초점(focus)을 정한다.
   tools/serve.py 로 띄웠으면 '저장'이 종 파일을 바로 고쳐 쓴다. */
const ED = { point: 0, target: "at" };
function editPanel() {
  let pn = $("edit-panel");
  if (!pn) {
    pn = document.createElement("aside");
    pn.id = "edit-panel";
    document.body.appendChild(pn);
    pn.addEventListener("click", e => {
      const b = e.target.closest("button");
      if (!b) return;
      if (b.dataset.pt) { ED.point = +b.dataset.pt; ED.target = b.dataset.t; }
      if (b.dataset.act === "save") saveEdits(b.dataset.id);
      editPanel();
    });
  }
  const sp = S.views[S.view].find(p => p?.node?.rank === "species")?.node;
  const d = sp && S.detail.get(sp.id);
  if (!d) { pn.innerHTML = `<p><b>검수 모드</b> 종 쪽으로 가면 위치를 정할 수 있다.</p>`; return; }
  const rows = (d.points || []).map((p, i) => `<li class="${ED.point === i ? "on" : ""}"><span>${i + 1}. ${esc(p.ko)}</span>
    <button data-pt="${i}" data-t="at" class="${ED.point === i && ED.target === "at" ? "sel" : ""}">번호 ${p.at ? "✓" : ""}</button>
    <button data-pt="${i}" data-t="label" class="${ED.point === i && ED.target === "label" ? "sel" : ""}">글자 ${p.label ? "✓" : ""}</button></li>`).join("");
  pn.innerHTML = `<p><b>검수 모드</b> ${esc(d.ko)}</p>
    <p class="hint">동정 도해: 항목을 고르고 그림을 누른다. 도판: 그림을 누르면 둥근 그림의 초점.</p>
    <ol>${rows}</ol>
    <p>초점 ${d.art?.focus ? d.art.focus.map(x => x.toFixed(2)).join(", ") : "가운데"}</p>
    <button data-act="save" data-id="${d.id}">저장</button> <span id="edit-msg"></span>`;
}
function onEditClick(e) {
  const fr = e.target.closest(".editable");
  if (!fr) return;
  e.preventDefault();
  const img = fr.querySelector("img");
  if (!img) return;
  const r = img.getBoundingClientRect();
  const x = +((e.clientX - r.left) / r.width).toFixed(3), y = +((e.clientY - r.top) / r.height).toFixed(3);
  const d = S.detail.get(fr.dataset.id);
  if (fr.dataset.edit === "focus") {
    d.art.focus = [x, y];
    S.nodes.get(d.id).focus = [x, y];
  } else {
    const p = d.points[ED.point];
    p[ED.target] = [x, y];
    if (ED.target === "at" && !p.label) ED.target = "label";
    else { ED.point = Math.min(d.points.length - 1, ED.point + 1); ED.target = "at"; }
  }
  showView(S.view);
}
async function saveEdits(id) {
  const d = S.detail.get(id);
  const body = JSON.stringify(d, null, 2) + "\n";
  const msg = t => { const m = $("edit-msg"); if (m) m.textContent = t; };
  try {
    const r = await fetch(`/__save/data/${S.vid}/species/${id}.json`, { method: "PUT", body, headers: { "Content-Type": "application/json" } });
    if (!r.ok) throw new Error(r.status);
    msg("저장했다. uv run tools/build.py 로 다시 엮을 것");
  } catch {
    await navigator.clipboard?.writeText(body).catch(() => {});
    msg("저장 서버가 아니어서 JSON을 클립보드에 복사했다");
  }
}

/* ───────────────────────── 시작 ───────────────────────── */
function layout() {
  const m = measure();
  if (m.mode === S.mode && m.W === S.W && m.H === S.H && S.pages.length) return false;
  const keep = S.views.length ? keyOfView(S.view) : null;
  Object.assign(S, m);
  applySize();
  measureCaps();
  S.flows.clear();
  for (const id of S.detail.keys()) S.flows.set(id, flowSpecies(S.nodes.get(id)));
  paginate();
  S.view = viewOfKey(keep ?? routeKey()) ?? 0;
  return true;
}

async function start() {
  try {
    const lib = await getJSON("data/library.json");
    const want = (location.hash.match(/^#\/?([^/]+)/) || [])[1];
    const vol = lib.volumes.find(v => v.id === want) || lib.volumes[0];
    S.vid = vol.id;
    indexBook(await getJSON(vol.book));
    $("toc").href = href("contents");
    $("idx").href = href("index");
    await Promise.race([document.fonts?.ready, new Promise(r => setTimeout(r, 2500))]);
    layout();
    await ensure(S.views[S.view]);
    S.view = viewOfKey(routeKey()) ?? S.view;
    await ensure(S.views[S.view]);
    showView(S.view);
    prefetch(S.view);
    $("boot").remove();
    document.body.classList.add("ready");
  } catch (err) {
    console.error(err);
    $("boot").innerHTML = `도감 자료를 읽지 못했습니다.<br><small>폴더에서 <code>uv run tools/serve.py</code>(또는 <code>python -m http.server</code>)를 실행한 뒤 http://localhost:8000 으로 여세요. 파일을 바로 열면 브라우저가 자료 읽기를 막습니다.</small>`;
    return;
  }

  // 확인용: ?freeze=0.4 → 다음 쪽으로 넘기는 중간 모습에서 멈춘다(음수는 뒤로)
  const fz = parseFloat(new URLSearchParams(location.search).get("freeze"));
  if (!Number.isNaN(fz)) {
    const to = S.view + (fz < 0 ? -1 : 1);
    if (S.views[to]) {
      await ensure(S.views[to]);
      const t = setupTurn(S.view, to, true);
      const e = Math.abs(fz);
      if (t.hard) t.leaf.setT(fz < 0 ? 1 - e : e);
      else t.leaf.set(t.C, arcPoint(fz < 0 ? 1 - e : e, S.W, S.H, true));
      S.busy = true;
    }
  }

  $("prev").addEventListener("click", () => go(-1));
  $("next").addEventListener("click", () => go(1));
  addEventListener("hashchange", () => turnTo({ key: routeKey() }));
  document.addEventListener("keydown", e => {
    if (e.altKey || e.ctrlKey || e.metaKey || e.target.closest("input,textarea")) return;
    if (e.key === "ArrowRight" || e.key === "PageDown") { e.preventDefault(); go(1); }
    else if (e.key === "ArrowLeft" || e.key === "PageUp") { e.preventDefault(); go(-1); }
    else if (e.key === "Home") turnTo({ key: "" });
    else if (e.key === "End") turnTo({ key: "colophon" });
  });
  bookEl.addEventListener("pointerdown", onPointerDown);
  addEventListener("pointermove", onPointerMove, { passive: false });
  addEventListener("pointerup", onPointerUp);
  addEventListener("pointercancel", onPointerUp);
  bookEl.addEventListener("pointerleave", e => { if (e.pointerType === "mouse" && !drag.st) unpeek(); });
  bookEl.addEventListener("click", e => {
    if (bookEl.dataset.dragged) { e.preventDefault(); e.stopPropagation(); return; }
    if (S.edit) onEditClick(e);
  }, true);
  let rt;
  addEventListener("resize", () => {
    clearTimeout(rt);
    rt = setTimeout(() => { if (!S.busy && S.views.length && layout()) showView(S.view); }, 160);
  });
}

if (new URLSearchParams(location.search).has("test")) window.__book = { S, showView, turnTo, ensure, layout };
start();
